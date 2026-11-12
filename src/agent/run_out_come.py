import sys
from bootstrap import AgentDeps
from dataclasses import dataclass
from time import perf_counter
from config import LLMSettings
from model.request import DecisionRequest
from model.models import FinalDecision,ToolCall
from agent import AgentRuntime,OpenAICompatibleLLMAdapter
from model.errors import LLMError, AgentRuntimeError,LLMOutputError


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
    for summary in deps.skill_registry.summaries():
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

@dataclass
class RunOutcome:
    llm: RecordingLLM | None
    events: list[tuple[str, dict[str, object]]]
    result: FinalDecision | None
    exit_code: int

async def run_once(deps:AgentDeps, request: DecisionRequest) -> RunOutcome:
    offline = "--offline" in sys.argv

    # A 层
    try:
        await check_wiring(deps)
    except AssertionError as e:
        print(f"[FAIL][接线] {e}")
        return RunOutcome(llm=None, events=[], result=None, exit_code=EXIT_WIRING)

    print("[PASS][接线] 4 项检查通过")
    if offline:
        return RunOutcome(llm=None, events=[], result=None, exit_code=EXIT_OK)

    # B 层
    adapter = OpenAICompatibleLLMAdapter(LLMSettings())
    llm = RecordingLLM(adapter)
    events: list[tuple[str, dict[str, object]]] = []
    result = None
    exit_code = EXIT_OK
    try:
        runtime = AgentRuntime(llm=llm, tool_registry=deps.tool_registry,
                               skill_registry=deps.skill_registry, max_rounds=5,
                               event_sink=lambda t, d: events.append((t, d)))
        result = await runtime.run(request)
        return RunOutcome(llm, events, result,exit_code)
    except (LLMError, AgentRuntimeError) as e:
        print(f"[FAIL][模型侧] {type(e).__name__}: {e}")  # 退出码 2，不是接线问题
        if isinstance(e, LLMOutputError):
            print(f"  错误摘要：{e.error_summary}")
            print(f"  原始输出前300字：{e.raw_preview!r}")
            print(f"  finish_reason：{e.finish_reason}，总长度：{e.raw_length}")
            print(f"  原始输出末尾200字：{e.raw_tail!r}")
        exit_code = EXIT_MODEL
        return RunOutcome(llm, events, result, exit_code)
    finally:
        await adapter.aclose()