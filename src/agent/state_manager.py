from datetime import UTC, datetime

from model.enums import IncidentStatus
from model.enums import WorkflowStage
from model.models.evidence import Evidence
from model.models.incident import Incident
from model.models.status_transition import StatusTransition
from database.incident_repository import DuplicateEvidenceError, IncidentRepository


_ALLOWED_TRANSITIONS: dict[IncidentStatus, set[IncidentStatus]] = {
    IncidentStatus.CREATED: {IncidentStatus.PLANNING, IncidentStatus.FAILED},
    IncidentStatus.PLANNING: {
        IncidentStatus.DIAGNOSING,
        IncidentStatus.BLOCKED,
        IncidentStatus.FAILED,
    },
    IncidentStatus.DIAGNOSING: {
        IncidentStatus.ACTING,
        IncidentStatus.BLOCKED,
        IncidentStatus.FAILED,
    },
    IncidentStatus.ACTING: {
        IncidentStatus.VERIFYING,
        IncidentStatus.BLOCKED,
        IncidentStatus.FAILED,
    },
    IncidentStatus.VERIFYING: {
        IncidentStatus.RESOLVED,
        IncidentStatus.BLOCKED,
        IncidentStatus.FAILED,
    },
    IncidentStatus.BLOCKED: {IncidentStatus.PLANNING},
    IncidentStatus.RESOLVED: set(),
    IncidentStatus.FAILED: set(),
}

_STAGE_BY_STATUS: dict[IncidentStatus, WorkflowStage] = {
    IncidentStatus.PLANNING: WorkflowStage.PLANNER,
    IncidentStatus.DIAGNOSING: WorkflowStage.DIAGNOSE,
    IncidentStatus.ACTING: WorkflowStage.ACT,
    IncidentStatus.VERIFYING: WorkflowStage.VERIFY,
}


class StateManager:
    """SRE事件状态管理器"""

    def __init__(self, state: Incident, repository: IncidentRepository):
        self.state = state
        self.repository = repository

    def transition_to(
        self,
        target: IncidentStatus,
        reason: str | None = None,
    ) -> Incident:
        """校验并持久化状态变化，提交成功后再更新内存模型。"""
        current = self.state.status
        if target in {IncidentStatus.BLOCKED ,IncidentStatus.FAILED} and (reason is None or not reason.strip()):
            raise ValueError("进入 BLOCKED 或 FAILED 时必须提供非空原因")
        if target not in _ALLOWED_TRANSITIONS[current]:
            raise ValueError(f"不允许的状态流转: {current.value} -> {target.value}")


        changed_at = datetime.now(UTC)
        transition = StatusTransition(
            from_status=current,
            to_status=target,
            reason=reason,
            changed_at=changed_at,
        )
        stage = _STAGE_BY_STATUS.get(target, self.state.stage)

        self.repository.save_transition(self.state.incident_id, transition, stage)

        self.state.status = target
        self.state.stage = stage
        self.state.updated_at = changed_at
        self.state.status_history.append(transition)
        return self.state

    def add_evidence(self, evidence: Evidence) -> Incident:
        """拒绝重复证据 ID；SQLite 提交成功后才追加到内存模型。"""
        if any(item.evidence_id == evidence.evidence_id for item in self.state.evidence):
            raise DuplicateEvidenceError(
                f"重复的 evidence_id: {evidence.evidence_id} "
                f"(incident_id={self.state.incident_id})"
            )

        stored_evidence = evidence.model_copy(deep=True)
        if stored_evidence.stage is None and self.state.stage is not None:
            stored_evidence = stored_evidence.model_copy(update={"stage": self.state.stage})

        updated_at = datetime.now(UTC)
        self.repository.add_evidence(self.state.incident_id, stored_evidence, updated_at)

        self.state.evidence.append(stored_evidence)
        self.state.updated_at = updated_at
        return self.state
