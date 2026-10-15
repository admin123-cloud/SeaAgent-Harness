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
    # 已创建 故障事件已创建，等待 Agent 开始处理
    CREATED = "CREATED"
    # 规划中	Agent 正在分析任务目标，制定故障处理计划
    PLANNING = "PLANNING"
    # 诊断中	正在收集日志、指标、事件等证据，定位故障原因
    DIAGNOSING = "DIAGNOSING"
    # 执行中	根据诊断结果执行修复操作
    ACTING = "ACTING"
    # 验证中	检查修复结果，确认故障是否消除
    VERIFYING = "VERIFYING"
    # 已解决	故障已修复并通过验证，事件处理完成
    RESOLVED = "RESOLVED"
    # 已阻塞	因权限不足、缺少信息、等待人工审批等原因，暂时无法继续
    BLOCKED = "BLOCKED"
    # 处理失败	故障处理流程失败，无法在当前约束下完成
    FAILED = "FAILED"