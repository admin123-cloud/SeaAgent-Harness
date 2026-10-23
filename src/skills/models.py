from datetime import datetime
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field

class SkillSummary(BaseModel):
    """ 常驻模型上下文的skill摘要总结"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    skill_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    # 逻辑入口，例如 skill://sre/incident-triage；不要暴露实际文件路径。
    load_ref: str = Field(min_length=1)

class SkillDetail(BaseModel):
    """Harness 按需加载和维护的完整 Skill。"""
    model_config = ConfigDict(extra="forbid")

    skill_id: str
    name: str
    description: str
    instructions: str = Field(min_length=1)
    # Skill 包内的相对路径，由 read_skill_resource 按需读取。
    resources: tuple[str, ...] = ()

    # ---- Harness 管理字段（不进入模型上下文）----
    version: str
    updated_at: datetime
    # 管理员授予的工具（目前只校验，尚未在执行层强制）。
    allowed_tools: frozenset[str] = Field(default_factory=frozenset)
    # 启用、禁用
    enabled: bool
    # 有效可用
    validation_status: Literal["pending", "valid", "invalid"]
    source: Literal["builtin", "imported", "created"]

    # ---- v2 新增 ----
    # 外部包在 allowed-tools 里"请求"的工具，仅记录，绝不自动授予。
    requested_tools: frozenset[str] = Field(default_factory=frozenset)
    # 外部包的其他 frontmatter 信息（license / compatibility / metadata.*），仅保存，不进模型上下文。
    package_meta: dict[str, str] = Field(default_factory=dict)

    def to_model_context(self) -> dict[str, object]:
        """只把正文和资源引用交给模型，管理字段留在 Harness。"""
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "instructions": self.instructions,
            "resources": list(self.resources),
        }