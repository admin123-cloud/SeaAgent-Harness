from skills.registry import LOAD_REF_PREFIX, SkillRegistry
from skills.store import check_skill_id
from .models import SkillSummary, SkillDetail
from model.errors import SkillInvalid, SkillNotFound

# BaseModel 是给数据类用的  特征是"字段 + 校验 + 序列化"
# Toolkit 是服务（有行为、无数据 schema）  最终喂给大模型的可用工具类

class SkillToolkit:
    def __init__(self, registry:SkillRegistry) -> None:
        self._registry = registry

    def _parse_load_ref(self,load_ref:str) -> str:
        """校验并剥离 skill:// 前缀，返回 skill_id。"""
        if not load_ref.startswith(LOAD_REF_PREFIX):
            raise SkillInvalid(f"load_ref 必须以 {LOAD_REF_PREFIX} 开头: {load_ref!r}")
        skill_id = load_ref[len(LOAD_REF_PREFIX):].strip()
        return check_skill_id(skill_id)  # 校验并返回，一步完成

    def _load_visible(self,skill_id:str) -> SkillDetail:
        """模型视角的可见性过滤：禁用/未校验按'不存在'口径处理。"""
        detail = self._registry.get(skill_id)
        if not (detail.enabled and detail.validation_status == "valid"):
            raise SkillNotFound(f"skill 不存在：{skill_id}")
        return detail


    # 给模型看的"目录页"
    def catalog(self) -> list[SkillSummary]:
        """进模型上下文的目录，直接委托 Registry.summaries()。"""
        return self._registry.summaries()

    def read_skill(self,load_ref:str) -> dict[str, object]:
        skill_id = self._parse_load_ref(load_ref)
        detail = self._load_visible(skill_id)
        return detail.to_model_context()

