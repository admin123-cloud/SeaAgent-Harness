import asyncio
from bootstrap import build_deps
from agent import AgentRuntime,OpenAICompatibleLLMAdapter
from model.enums import DecisionTask
from model.request import DecisionRequest
from config import LLMSettings

async def main():
    #  先定义收集器（必须在构造 AgentRuntime 之前）
    events: list[tuple[str, dict[str, object]]] = []
    #  定义注册器
    deps = build_deps()

    settings = LLMSettings()
    adapter = OpenAICompatibleLLMAdapter(settings)
    try:
        runtime = AgentRuntime(
            llm=adapter,
            tool_registry= deps.tool_registry,
            skill_toolkit = deps.skill_toolkit,
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
        print(result.response.summary)
        print([t for t, _ in events])
    except AssertionError as e:
        raise e


if __name__ == "__main__":
     asyncio.run(main())