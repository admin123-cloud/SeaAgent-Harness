# --------------------------------------------------------------------------- #
# 异常
# --------------------------------------------------------------------------- #
class SkillError(Exception):
    """所有 skill 相关错误的基类。"""


class SkillNotFound(SkillError):
    pass


class SkillConflict(SkillError):
    """已存在 / 版本冲突。"""


class SkillReadOnly(SkillError):
    """试图修改内置 skill。"""


class SkillForbidden(SkillError):
    """操作者可见该 skill，但无权执行此操作。"""


class SkillInvalid(SkillError):
    """skill_id 非法、文件格式错误、字段不允许修改等。"""


class SkillImportError(SkillInvalid):
    """zip 导入失败。"""