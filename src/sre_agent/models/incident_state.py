from datetime import datetime, UTC

from pydantic import BaseModel,Field
from sre_agent.enums.incident_status import IncidentStatus
from sre_agent.enums.workflow_stage import WorkflowStage
from sre_agent.models.evidence import Evidence


def utc_now() -> datetime:
    return datetime.now(UTC)

class IncidentState(BaseModel):
    """
        事件状态
    """
    schema_version: str = Field(description="状态数据结构的版本号，用于兼容不同版本的 Schema")
    incident_id: str = Field(description="事件唯一标识，用于关联同一次事件的诊断、执行和验证过程")
    goal: str = Field(description="事件处理目标，描述本次事件最终希望达到的状态")
    environment: dict[str,str] = Field(description="字典:key->value,类似于java的Map")
    status: IncidentStatus
    stage: WorkflowStage | None
    evidence: list[Evidence]
    iteration: int
    created_at: datetime = Field(description="当前 UTC 时间")
    updated_at: datetime = Field(description="当前 UTC 时间")