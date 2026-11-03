from dataclasses import dataclass
from pathlib import Path
from skills import FileSkillStore,SkillRegistry
from tools import ToolRegistry
from skills.read_skill import build_read_skill_spec


@dataclass(frozen=True)
class AgentDeps:
    """ Agent 运行时需要的依赖打包 """
    tool_registry: ToolRegistry
    skill_registry: SkillRegistry

def build_deps() -> AgentDeps:
    # 1.找到根路径
    src_dir = Path(__file__).resolve().parent

    # 2.构建SkillRegistry skill注册器
    skill_registry = SkillRegistry(
        builtin=FileSkillStore(src_dir / "skills" / "builtin", source="builtin", read_only=True),
        team=FileSkillStore(src_dir.parent / ".sre-agent-data" / "skills"),
    )
    tool_registry = ToolRegistry()
    tool_registry.register(build_read_skill_spec(skill_registry))

    return AgentDeps(tool_registry, skill_registry)
