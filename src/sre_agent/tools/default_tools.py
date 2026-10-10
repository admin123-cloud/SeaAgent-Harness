from sre_agent.agent.tool_registry import ToolRegistry, ToolSpec
from sre_agent.tools.demo_echo import DemoEchoInput, run_demo_echo

""" 注册所有工具Registry，并注册内置工具 """
def build_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            name="demo_echo",
            description="原样返回输入消息，用于验证 Tool Calling 链路",
            input_model= DemoEchoInput,
            handler=run_demo_echo,
            readonly = True,
            risk_level = "low",
            timeout_seconds = 5
        )
    )
    return registry