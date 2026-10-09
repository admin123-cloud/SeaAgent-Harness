from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from sre_agent.enums.incident_status import IncidentStatus
from sre_agent.enums.workflow_stage import WorkflowStage
from sre_agent.models.evidence import Evidence
from sre_agent.models.status_transition import StatusTransition


def utc_now() -> datetime:
    return datetime.now(UTC)

# 事件
class Incident(BaseModel):
    """Incident 根模型；仓储将其当前字段及关联记录保存到 SQLite。"""

    schema_version: str = Field(
        default="1.0",
        description="状态数据结构的版本号，用于兼容不同版本的 Schema",
    )
    incident_id: str = Field(
        description="事件唯一标识，用于关联同一次事件的诊断、执行和验证过程"
    )
    goal: str = Field(description="事件处理目标，描述本次事件最终希望达到的状态")
    environment: dict[str, str] = Field(default_factory=dict)
    status: IncidentStatus = IncidentStatus.CREATED
    stage: WorkflowStage | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    status_history: list[StatusTransition] = Field(default_factory=list)
    iteration: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("incident_id", "goal")
    @classmethod
    def strip_and_require_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("不能为空")
        return value

    @field_validator("created_at", "updated_at")
    @classmethod
    def require_aware_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("时间必须包含时区")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def status_history_matches_current_state(self) -> "Incident":
        for previous, current in zip(self.status_history, self.status_history[1:]):
            if current.from_status != previous.to_status:
                raise ValueError("status_history 中相邻状态变更不连续")
        if self.status_history and self.status_history[-1].to_status != self.status:
            raise ValueError("最后一条状态变更必须与 Incident 当前状态一致")
        return self
