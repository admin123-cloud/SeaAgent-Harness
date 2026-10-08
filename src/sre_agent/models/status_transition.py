from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from sre_agent.enums.incident_status import IncidentStatus


def utc_now() -> datetime:
    return datetime.now(UTC)


class StatusTransition(BaseModel):
    """一次 Incident 状态变更记录。"""

    from_status: IncidentStatus
    to_status: IncidentStatus
    reason: str | None = None
    changed_at: datetime = Field(default_factory=utc_now)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("changed_at")
    @classmethod
    def require_aware_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("时间必须包含时区")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def require_reason_for_blocked_or_failed(self) -> "StatusTransition":
        if self.to_status in {IncidentStatus.BLOCKED, IncidentStatus.FAILED} and not self.reason:
            raise ValueError("进入 BLOCKED 或 FAILED 状态时必须提供原因")
        return self
