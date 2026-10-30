import sys
import asyncio
from bootstrap import build_deps
from agent import AgentRuntime,OpenAICompatibleLLMAdapter
from model.enums import DecisionTask
from model.request import DecisionRequest
from model.errors import LLMError, AgentRuntimeError
from model.models import FinalDecision,ToolCall,ToolCallDecision
from config import LLMSettings
from time import perf_counter



EXIT_OK, EXIT_WIRING, EXIT_MODEL = 0, 1, 2

def expect(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)

class RecordingLLM:
    def __init__(self, inner):
        self.inner = inner
        self.requests = []     # 每轮收到的 DecisionRequest
        self.decisions = []    # 每轮返回的决策
        self.elapsed = []      # 每轮耗时（秒）

    async def decide(self, request):
        self.requests.append(request)
        t0 = perf_counter()
        decision = await self.inner.decide(request)   # 抛异常就让它抛出去
        self.elapsed.append(perf_counter() - t0)
        self.decisions.append(decision)
        return decision


async def check_wiring(deps):
    """ A层 检查skill和tool 读取和使用是否正常 """
    # A1.断言read_skill 已注册
    tool_name = []
    for tool_spec in deps.tool_registry.list_specs():
        tool_name.append(tool_spec.name)

    expect("read_skill" in tool_name, "检查tool工具异常，未发现内置工具read_skill")

    # A2.断言skill目录合理
    skill_ids = []
    for summary in deps.skill_toolkit.catalog():
        skill_ids.append(summary.skill_id)

    bad = [i for i in skill_ids if i.startswith(("builtin/", "buildin/"))]
    expect(not bad, f"skill_id 带了不该有的前缀：{bad}")
    expect("sre/incident-triage" in skill_ids,"默认事件检查skill：incident-triage，未注册")

    # A3.能读取到存在的skill
    call = ToolCall(
        call_id="wiring-1",
        tool_name="read_skill",
        arguments={"load_ref": "skill://sre/incident-triage"}
    )
    result = await deps.tool_registry.execute(call)
    expect(result.success,"调用工具失败")
    expect(result.data.get("skill_id") == "sre/incident-triage","read_skill 返回的 skill_id 与请求不一致")

    # A4.读不存在的skill会失败而不会崩溃
    call = ToolCall(
        call_id="wiring-2",
        tool_name="read_skill",
        arguments={"load_ref": "skill://no-such/skill"}
    )
    result = await deps.tool_registry.execute(call)
    expect(result.success is False, "读取不存在的 skill 应该失败")
    expect(result.error_type is not None, "失败时 error_type 不能是 None")


def check_history(llm:RecordingLLM, events:list[tuple[str, dict]]):
    # B1.至少调用过一次模型
    expect(len(llm.requests) >= 1,"没有调用过模型")
    for n, req in enumerate(llm.requests, start=1):
        history = req.context.get("agent_history")
        expect(history is not None, f"第{n}次请求缺少 agent_history")
        expect(len(history) == 2 * (n - 1), f"第{n}次请求历史长度不对：{len(history)}")
        # B3.第 n≥2 次请求里   顺序和轮次正确，这一条能暴露"结果没带回去"的 bug
        if n >= 2:
            expect(history[-2]["kind"] == "tool_call", f"第{n}次请求：倒数第二条应是 tool_call，实际是 {history[-2]['kind']}")
            expect(history[-1]["kind"] == "tool_result", f"第{n}次请求：倒数第一条应是 tool_result，实际是 {history[-1]['kind']}")
            expect(history[-1]["round"] == n - 1, f"第{n}次请求：最后一条的 round 应为 {n-1}，实际是 {history[-1]['round']}")

    # B4._prepare_request 注入正确
    first = llm.requests[0].context
    tool_names = {t["name"] for t in first["available_tools"]}
    expect("read_skill" in tool_names, "第1次请求的 available_tools 里没有 read_skill")
    expect(len(first["available_skills"]) > 0, "第1次请求没有注入 available_skills")
    # 第1次请求的  里有read_skill，
    # B5.事件里 tool_call 数量 == tool_result 数量 == llm.decisions 里 ToolCallDecision 的数量   事件和决策一一对应
    n_call = sum(1 for t, _ in events if t == "tool_call")
    n_result = sum(1 for t, _ in events if t == "tool_result")
    n_dec = sum(1 for d in llm.decisions if isinstance(d, ToolCallDecision))
    expect(n_call == n_result == n_dec, f"事件与决策数量不一致：call={n_call} result={n_result} decision={n_dec}")


def report(llm:RecordingLLM, events:list[tuple[str, dict]],result:FinalDecision | None):
    seen_tools: list[tuple[str,str]]  = []
    for i, d in enumerate(llm.decisions,start=1):
        if isinstance(d, ToolCallDecision):
            tool_calls = d.tool_calls
            for tool_call in tool_calls:
                tool_name = tool_call.tool_name
                arguments = tool_call.arguments
                load_ref = arguments.get("load_ref")
                key = (tool_name, load_ref)
                if key in seen_tools:
                    print(f"现在是第{i}轮，工具名称{tool_name}，加载路径{load_ref}，耗时{llm.elapsed[i - 1]:.1f}s , ⚠ 重复读取")
                else:
                    seen_tools.append(key)
                    print(f"现在是第{i}轮，工具名称{tool_name}，加载路径{load_ref}，耗时{llm.elapsed[i - 1]:.1f}s")
        else:# FinalDecision
            print(f"当前是第{i}轮. 耗时{llm.elapsed[i-1]:.1f}s")

    if len(llm.requests) > len(llm.decisions):  # 录到了请求，却没有对应决策
        print(f"第 {len(llm.requests)} 轮模型调用失败...")

    if result is not None:
        print(f"{result.response.summary[:200]}")

async def main() -> int:
    offline = "--offline" in sys.argv
    deps = build_deps()

    # A 层
    try:
        await check_wiring(deps)
    except AssertionError as e:
        print(f"[FAIL][接线] {e}")
        return EXIT_WIRING
    print("[PASS][接线] 4 项检查通过")
    if offline:
        return EXIT_OK

    # B 层
    request = DecisionRequest(
        task=DecisionTask.DIAGNOSE,
        incident_id="verify-skill-001",
        goal="default 命名空间的 redis Pod 昨晚重启了两次，请选择最合适的 skill 并说明排查步骤",
        context={"environment": {"namespace": "default", "resource": "redis"}},
    )
    adapter = OpenAICompatibleLLMAdapter(LLMSettings())
    llm = RecordingLLM(adapter)
    events: list[tuple[str, dict[str, object]]] = []
    result = None
    exit_code = EXIT_OK
    try:
        runtime = AgentRuntime(llm=llm, tool_registry=deps.tool_registry,
                               skill_toolkit=deps.skill_toolkit, max_rounds=5,
                               event_sink=lambda t, d: events.append((t, d)))
        result = await runtime.run(request)
    except (LLMError, AgentRuntimeError) as e:
        print(f"[FAIL][模型侧] {type(e).__name__}: {e}")  # 退出码 2，不是接线问题
        exit_code = EXIT_MODEL
    finally:
        await adapter.aclose()

    report(llm, events, result)
    try:
        check_history(llm, events)
    except AssertionError as e:
        print(f"[FAIL][接线] {e}")
        return EXIT_WIRING  # 断言失败优先级高于模型失败
    return exit_code


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))