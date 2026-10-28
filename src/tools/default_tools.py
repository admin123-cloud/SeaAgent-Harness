from tools.registry import ToolRegistry, ToolSpec
from tools.demo_echo import DemoEchoInput, run_demo_echo
from pydantic import BaseModel, Field
from skills import SkillToolkit

""" 注册所有工具Registry，并注册内置工具 """
class ReadSkillInput(BaseModel):
    load_ref:str = Field(description="skill://<skill_id>，来自 available_skills 目录")

# 适配层：只做接线 ← ToolSpec 注册写这里
def build_default_registry(toolkit:SkillToolkit) -> ToolRegistry:
    registry = ToolRegistry()
    async def run_read_skill(arguments: ReadSkillInput) -> dict[str, object]:
        return toolkit.read_skill(arguments.load_ref) # 闭包捕获 toolkit

    registry.register(ToolSpec(
        name="read_skill",
        description="加载一个 Skill 的完整指引。先从 available_skills 目录选择匹配的 skill，再用它的 load_ref 调用本工具。",
        input_model=ReadSkillInput,
        handler=run_read_skill,
        required_permissions=frozenset(),
        risk_level="low",
        timeout_seconds=2.0,
    ))
    registry.register(
        ToolSpec(
            name="demo_echo",
            description="原样返回输入消息，用于验证 Tool Calling 链路",
            input_model= DemoEchoInput,
            handler=run_demo_echo,
            required_permissions=frozenset(),
            risk_level = "low",
            timeout_seconds = 5
        )
    )
    return registry