from .store import FileSkillStore
from .models import SkillDetail,SkillSummary
import json
import threading
import hashlib
from datetime import datetime, timezone
from model.errors import SkillNotFound,SkillReadOnly


LOAD_REF_PREFIX = "skill://"

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _bump(version: str) -> str:
    return str(int(version) + 1) if version.isdigit() else "1"

# 要做一次前置判断  只有vaild和enable才能给模型使用
def summary_of(detail: SkillDetail) -> SkillSummary:
    """第一层目录条目。load_ref 是逻辑引用，不暴露真实文件路径。"""
    # load_ref = load reference,模型只拿它说"我要读这本手册"，Toolkit 负责换算成 skill_id → 查索引 → 返回内容。
    return SkillSummary(
        skill_id=detail.skill_id,
        name=detail.name,
        description=detail.description,
        load_ref=f"{LOAD_REF_PREFIX}{detail.skill_id}",
    )

def content_hash_of(detail: SkillDetail) -> str:
    """模型可见内容的指纹，用于会话内的版本固定（注意：只含资源文件名，不含资源内容）。"""
    payload = json.dumps([detail.name, detail.description, detail.instructions, list(detail.resources)],
                         ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


"""内存索引：内置库（只读）+ 团队库（可写）。所有读写都过这一层。"""
class SkillRegistry:
    def __init__(self,builtin:FileSkillStore,team:FileSkillStore) -> None:
        self._builtin = builtin
        self._team = team
        self._skills : dict[str, SkillDetail] = {}
        self.load_errors : dict[str,str] = {}
        # 管理 API 的"读-改-写"需要在同一把锁下完成
        self.lock = threading.Lock()
        self.reload()

    def reload(self) -> None:
        skills: dict[str, SkillDetail] = {}
        errors: dict[str,str] = {}
        # 内置的skill 不修改
        for is_builtin, store in ((True, self._builtin), (False, self._team)):
            found, errs = store.load_all()
            errors.update(errs)
            for s in found:
                if not is_builtin and s.skill_id in skills:  # 内置库已占用的 id
                    errors[s.skill_id] = "与内置 skill 冲突"
                    continue
                skills[s.skill_id] = s
        with self.lock:
            self._skills, self.load_errors = skills, errors

    # 获取skill列表
    def summaries(self) -> list[SkillSummary]:
        with self.lock:
            # 1. 创建一个空列表，用于保存结果
            result = []
            # 2. 从内存索引中获取所有 Skill
            skills = list(self._skills.values())
            # 3. 按照 skill_id 进行排序
            skills.sort(key=lambda skill: skill.skill_id)

            # 4. 遍历排序后的 Skill
            for skill in skills:
                # 5. 判断 Skill 是否启用
                if not skill.enabled:
                    continue
                if skill.validation_status != "valid":
                    continue
                summary = summary_of(skill)
                result.append(summary)
            return result

    # 未访问其他方法直接修改内存里的_skills  此处加锁
    def get(self,skill_id:str) -> SkillDetail:
        with self.lock:
            skills = self._skills
            if skill_id not in skills:
                raise SkillNotFound(skill_id)
            return skills[skill_id]

    # 检查skill是否支持修改
    """假定已持锁：返回详情；不存在抛 SkillNotFound，内置抛 SkillReadOnly。"""
    def _writable_locked(self,skill_id:str) -> SkillDetail:
        # 直接从内存读取 防止死锁
        current = self._skills.get(skill_id)
        if current is None:
            raise SkillNotFound(f"skill 不存在: {skill_id}")
        if current.source == "builtin":
            raise SkillReadOnly(skill_id)
        return current

    # 场景：全量写入，导入/编辑后调用
    # 过程：校验内置 id → team.save() 落盘 → 更新内存索引
    def upsert(self,detail:SkillDetail) -> None:
        with self.lock:
            # 同样要挡内置 id：防止有人拿着 source="created" 但 id 是内置路径的对象写入团队库
            existing = self._skills.get(detail.skill_id)
            if existing is not None and existing.source == "builtin":
                raise SkillReadOnly(detail.skill_id)
            self._team.save(detail)
            self._skills[detail.skill_id] = detail

    # 过程：读-改-写，注意全程持锁 + model_copy 跳过校验只改标量安全
    # 场景：get → 修改 → upsert 的组合便捷方法
    def set_enabled(self,skill_id:str, enabled:bool) -> SkillDetail:
        with self.lock:
            current = self._writable_locked(skill_id)
            updated = current.model_copy(update={
                "enabled":enabled,
                "version":_bump(current.version),
                "updated_at":_now(),
            })
            self._team.save(updated)
            self._skills[skill_id] = updated
            return updated

    def remove(self,skill_id:str) -> None:
        with self.lock:
            self._writable_locked(skill_id)
            self._team.delete(skill_id)
            self._skills.pop(skill_id)