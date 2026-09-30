from enum import Enum


class WorkflowStage(Enum):
    """
        工作流状态
    """
    PLANNER = 'PLANNER'
    DIAGNOSE = 'DIAGNOSE'
    ACT = 'ACT'
    VERIFY = 'VERIFY'