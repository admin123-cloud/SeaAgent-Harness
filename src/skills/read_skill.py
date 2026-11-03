from pydantic import BaseModel, Field
from .registry import SkillRegistry
from tools import ToolSpec

""" 注册所有工具Registry，并注册内置工具 """
class ReadSkillInput(BaseModel):
    load_ref:str = Field(description="skill://<skill_id>，来自 available_skills 目录")

# 适配层：只做接线 ← ToolSpec 注册写这里
def build_read_skill_spec(registry: SkillRegistry) -> ToolSpec:

    async def run_read_skill(arguments: ReadSkillInput) -> dict[str, object]:
        return registry.read_for_model(arguments.load_ref)  # 闭包捕获 toolkit

    return ToolSpec(
        name="read_skill",
        description="加载一个 Skill 的完整指引。先从 available_skills 目录选择匹配的 skill，再用它的 load_ref 调用本工具。",
        input_model=ReadSkillInput,
        handler=run_read_skill,
        required_permissions=frozenset(),
        risk_level="low",
        timeout_seconds=2.0,
    )
