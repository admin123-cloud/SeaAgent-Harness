from pydantic import BaseModel
from datetime import datetime


class Evidence(BaseModel):
    """
        SRE Agent 在故障诊断过程中收集到的证据信息。
    """
    evidence_id: str
    source: str
    kind: str
    summary: str
    data: dict[str, object]
    created_at: datetime
