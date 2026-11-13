from bootstrap import AgentDeps
from dataclasses import dataclass
from config import LLMSettings
from model.request import DecisionRequest
from model.models import FinalDecision
from agent import AgentRuntime,OpenAICompatibleLLMAdapter
from model.errors import LLMError, AgentRuntimeError,LLMOutputError
from time import perf_counter


EXIT_OK, EXIT_WIRING, EXIT_MODEL = 0, 1, 2


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


@dataclass
class RunOutcome:
    llm: RecordingLLM
    events: list[tuple[str, dict[str, object]]]
    result: FinalDecision | None
    exit_code: int

async def run_once(deps:AgentDeps, request: DecisionRequest) -> RunOutcome:
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