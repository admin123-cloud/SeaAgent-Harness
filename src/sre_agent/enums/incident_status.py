from enum import Enum


class IncidentStatus(Enum):
    """
    SRE 故障事件状态枚举。

    用于描述一个 Incident 在 SRE Agent 生命周期中的当前处理阶段。

    状态流转示例：
        CREATED
            -> PLANNING
            -> DIAGNOSING
            -> ACTING
            -> VERIFYING
            -> RESOLVED

    特殊状态：
        BLOCKED: 当前事件无法继续执行，需要人工介入或等待外部条件。
        FAILED: 事件处理失败。
    """
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    DIAGNOSING = "DIAGNOSING"
    ACTING = "ACTING"
    VERIFYING = "VERIFYING"
    RESOLVED = "RESOLVED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"