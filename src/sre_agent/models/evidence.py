import json
from pydantic import BaseModel, field_validator
from datetime import datetime, UTC
from sre_agent.enums.workflow_stage import WorkflowStage


def utc_now() -> datetime:
    return datetime.now(UTC)

class Evidence(BaseModel):
    """
        证据模型
        SRE Agent 在故障诊断过程中收集到的证据信息。
    """
    evidence_id: str
    source: str
    kind: str
    summary: str
    data: dict[str, object]
    stage : WorkflowStage | None = None
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def require_aware_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("时间必须包含时区")
        return value.astimezone(UTC)

    @field_validator("evidence_id")
    @classmethod
    def require_non_empty_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("evidence_id 不能为空")
        return value

    @field_validator("data")
    @classmethod
    def require_json_data(cls, value: dict[str, object]) -> dict[str, object]:
        try:
            json.dumps(value, ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise ValueError("Evidence.data 必须只包含可 JSON 序列化的数据") from exc
        return value
