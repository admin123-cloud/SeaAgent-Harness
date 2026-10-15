import json
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(UTC)

# 会话实体模型
class ConversationEntry(BaseModel):
    """一条对话消息或可审计的 Agent 处理过程记录。"""

    entry_id: str = Field(default_factory=lambda: str(uuid4()))
    role: Literal["user", "assistant", "agent"]
    kind: Literal["message", "process", "llm_request", "llm_response", "error"]
    content: str = Field(min_length=1)
    data: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("content")
    @classmethod
    def require_non_blank_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("content 不能为空")
        return value

    @field_validator("created_at")
    @classmethod
    def require_aware_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("时间必须包含时区")
        return value.astimezone(UTC)

    @field_validator("data")
    @classmethod
    def require_json_data(cls, value: dict[str, object]) -> dict[str, object]:
        try:
            json.dumps(value, ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise ValueError("data 必须只包含可 JSON 序列化的数据") from exc
        return value
