import asyncio
from pathlib import Path

from agent import AgentRuntime,OpenAICompatibleLLMAdapter
from model.models import (
    FinalDecision,
    ToolCall,
    ToolCallDecision,
)
from model.enums import DecisionTask
from model.request import DecisionRequest
from model.response.decision_response import DecisionResponse
from skills import SkillRegistry, FileSkillStore, SkillToolkit
from tools import build_default_registry
from config import LLMSettings

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
    #  1. 构造 Skill 三件套
    # ① 先定义收集器（必须在构造 AgentRuntime 之前）
    events: list[tuple[str, dict[str, object]]] = []
    #  src目录和root目录 找到skill
    src_dir = Path(__file__).resolve().parents[1]
    # 内置skill和上传的skill
    skill_registry = SkillRegistry(
        builtin=FileSkillStore(src_dir / "skills", source="builtin", read_only=True),
        team=FileSkillStore(src_dir.parent / ".sre-agent-data" / "skills"),
    )
    toolkit = SkillToolkit(skill_registry)

    tool_registry = build_default_registry(toolkit)
    # 2. AgentRuntime 补 skill_toolkit 参数
    settings = LLMSettings()
    adapter = OpenAICompatibleLLMAdapter(settings)
    try:
        runtime = AgentRuntime(
            llm=adapter,
            registry= tool_registry,
            skill_toolkit = toolkit,
            max_rounds=5,
            event_sink=lambda t, d: events.append((t, d)),
        )

        request = DecisionRequest(
            task=DecisionTask.DIAGNOSE,
            incident_id="verify-skill-001",
            goal="验证 SkillToolkit 接入后的 AgentRuntime 工具调用闭环",
            context={},
        )
        result = await runtime.run(request)
    except AssertionError as e:
        raise e


if __name__ == "__main__":
     asyncio.run(main())