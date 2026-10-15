import asyncio

from sre_agent.agent.runtime import AgentRuntime
from sre_agent.enums.decision_task import DecisionTask
from sre_agent.models import (
    FinalDecision,
    ToolCall,
    ToolCallDecision,
)
from sre_agent.request.decision_request import DecisionRequest
from sre_agent.response.decision_response import DecisionResponse
from sre_agent.tools.default_tools import build_default_registry


class FakeLLM:
    """不访问网络，只返回预先写好的模型结果。"""

    def __init__(self):
        self.calls = 0

    async def decide(self, request: DecisionRequest):
        self.calls += 1
        print(f"FakeLLM 第 {self.calls} 次调用")

        if self.calls == 1:
            return ToolCallDecision(
                tool_calls=[
                    ToolCall(
                        call_id="call-001",
                        tool_name="demo_echo",
                        arguments={"message": "hello"},
                    )
                ]
            )

        history = request.context.get("agent_history", [])

        if len(history) != 2:
            raise AssertionError(
                f"工具调用历史数量错误：{history}"
            )

        if history[0]["kind"] != "tool_call":
            raise AssertionError("缺少 tool_call 历史")

        if history[1]["kind"] != "tool_result":
            raise AssertionError("缺少 tool_result 历史")

        tool_result = history[1]["results"][0]

        if tool_result["success"] is not True:
            raise AssertionError(
                f"工具执行失败：{tool_result}"
            )

        return FinalDecision(
            response=DecisionResponse(
                summary="Fake LLM 已收到 demo_echo 的执行结果",
                findings=[],
                evidence_ids=[],
                confidence=1.0,
                recommendations=[],
            )
        )



async def main():
    fake_llm = FakeLLM()
    registry = build_default_registry()

    events: list[tuple[str, dict[str, object]]] = []

    runtime = AgentRuntime(
        llm=fake_llm,
        registry=registry,
        max_rounds=3,
        event_sink=lambda event_type, data: events.append((event_type, data)),
    )

    request = DecisionRequest(
        task=DecisionTask.DIAGNOSE,
        incident_id="verify-001",
        goal="验证 AgentRuntime 工具调用闭环",
        context={},
    )

    result = await runtime.run(request)

    if not isinstance(result, FinalDecision):
        raise AssertionError(
            f"最终结果类型错误：{type(result).__name__}"
        )

    print("最终结论：", result.response.summary)
    print("LLM 调用次数：", fake_llm.calls)
    print("Runtime 验收通过")

    event_types = [event_type for event_type, _ in events]

    if event_types != ["tool_call", "tool_result"]:
        raise AssertionError(
            f"Runtime 事件类型错误：{event_types}"
        )
    print("Runtime 事件内容：")
    for event_type, data in events:
        print(f"- {event_type}: {data}")

    if events[0][1]["round"] != 1:
        raise AssertionError("tool_call 的 round 不正确")

    if events[1][1]["round"] != 1:
        raise AssertionError("tool_result 的 round 不正确")

    print("Runtime 事件回调验收通过")

if __name__ == "__main__":
    asyncio.run(main())