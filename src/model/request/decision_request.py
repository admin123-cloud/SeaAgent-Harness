from pydantic import BaseModel

from model.enums.decision_task import DecisionTask

""" 决策契约请求体 """


class DecisionRequest(BaseModel):
    # 决策类型 枚举
    task: DecisionTask
    # 事件id
    incident_id: str
    # 事件目标
    goal: str
    # 上下文 由调用方提前脱敏
    context: dict[str, object]