"""兼容入口：开发调试请使用本地事件工作台。"""
import asyncio

from sre_agent.models import ToolCall
from sre_agent.tools.default_tools import build_default_registry


async def demo_tool() -> None:
    registry = build_default_registry()

    result = await registry.execute(
        ToolCall(
            call_id="call-001",
            tool_name="demo_echo",
            arguments={"message": "hello"},
        )
    )

    print(result.model_dump_json(indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(demo_tool())
