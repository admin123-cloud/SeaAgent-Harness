from datetime import UTC, datetime
from pydantic import field_validator


def utc_now() -> datetime:
    return datetime.now(UTC)

# k8s 观测数据
class KubernetesObservation:
    namespace: str
    pod: str
    # Pod 当前阶段
    pod_phase: str
    # Kubernetes 事件
    events: list[str]
    # 容器状态
    container_statuses: list[str]
    collected_at: datetime

    @field_validator("namespace", "pod")
    @classmethod
    def strip_and_require_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("不能为空")
        return value