import json
import sqlite3
from datetime import datetime

from sre_agent.enums.incident_status import IncidentStatus
from sre_agent.enums.workflow_stage import WorkflowStage
from sre_agent.models.conversation_entry import ConversationEntry
from sre_agent.models.evidence import Evidence
from sre_agent.models.incident import Incident
from sre_agent.models.status_transition import StatusTransition
from sre_agent.storage.sqlite_database import SQLiteDatabase


class IncidentAlreadyExistsError(ValueError):
    """数据库中已存在相同 incident_id。"""


class IncidentNotFoundError(LookupError):
    """数据库中不存在指定 Incident。"""


class IncidentStatusConflictError(RuntimeError):
    """数据库中的当前状态与调用方持有的状态不一致。"""


class DuplicateEvidenceError(ValueError):
    """同一个 Incident 中已经存在相同 evidence_id。"""


class IncidentRepository:
    """Incident、Evidence 和状态变更的 SQLite 持久化入口。"""

    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def initialize(self) -> None:
        self.database.initialize()

    def create_incident(self, state: Incident) -> None:
        with self.database.transaction(immediate=True) as connection:
            try:
                connection.execute(
                    """
                    INSERT INTO incidents (
                        incident_id, schema_version, goal, environment_json,
                        status, stage, iteration, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        state.incident_id,
                        state.schema_version,
                        state.goal,
                        self._json_dumps(state.environment),
                        state.status.value,
                        state.stage.value if state.stage else None,
                        state.iteration,
                        state.created_at.isoformat(),
                        state.updated_at.isoformat(),
                    ),
                )
            except sqlite3.IntegrityError as exc:
                if connection.execute(
                    "SELECT 1 FROM incidents WHERE incident_id = ?", (state.incident_id,)
                ).fetchone():
                    raise IncidentAlreadyExistsError(
                        f"Incident 已存在: {state.incident_id}"
                    ) from exc
                raise

            for evidence in state.evidence:
                self._insert_evidence(connection, state.incident_id, evidence)
            for transition in state.status_history:
                self._insert_transition(connection, state.incident_id, transition)

    def get_incident(self, incident_id: str) -> Incident | None:
        with self.database.transaction() as connection:
            incident_row = connection.execute(
                "SELECT * FROM incidents WHERE incident_id = ?", (incident_id,)
            ).fetchone()
            if incident_row is None:
                return None

            evidence_rows = connection.execute(
                "SELECT * FROM evidence WHERE incident_id = ? ORDER BY rowid",
                (incident_id,),
            ).fetchall()
            transition_rows = connection.execute(
                "SELECT * FROM status_transitions WHERE incident_id = ? ORDER BY transition_id",
                (incident_id,),
            ).fetchall()

        evidence = [self._evidence_from_row(row) for row in evidence_rows]
        status_history = [self._transition_from_row(row) for row in transition_rows]
        return Incident(
            schema_version=incident_row["schema_version"],
            incident_id=incident_row["incident_id"],
            goal=incident_row["goal"],
            environment=json.loads(incident_row["environment_json"]),
            status=incident_row["status"],
            stage=incident_row["stage"],
            evidence=evidence,
            status_history=status_history,
            iteration=incident_row["iteration"],
            created_at=incident_row["created_at"],
            updated_at=incident_row["updated_at"],
        )

    def list_incidents(self) -> list[Incident]:
        with self.database.transaction() as connection:
            rows = connection.execute(
                "SELECT * FROM incidents ORDER BY updated_at DESC, created_at DESC"
            ).fetchall()
        return [
            Incident(
                schema_version=row["schema_version"],
                incident_id=row["incident_id"],
                goal=row["goal"],
                environment=json.loads(row["environment_json"]),
                status=row["status"],
                stage=row["stage"],
                iteration=row["iteration"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def delete_incident(self, incident_id: str) -> bool:
        with self.database.transaction(immediate=True) as connection:
            cursor = connection.execute(
                "DELETE FROM incidents WHERE incident_id = ?", (incident_id,)
            )
            return cursor.rowcount == 1

    def add_conversation_entry(self, incident_id: str, entry: ConversationEntry) -> None:
        with self.database.transaction(immediate=True) as connection:
            cursor = connection.execute(
                "UPDATE incidents SET updated_at = ? WHERE incident_id = ?",
                (entry.created_at.isoformat(), incident_id),
            )
            if cursor.rowcount != 1:
                raise IncidentNotFoundError(f"Incident 不存在: {incident_id}")
            connection.execute(
                """
                INSERT INTO conversation_entries (
                    entry_id, incident_id, role, kind, content, data_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.entry_id,
                    incident_id,
                    entry.role,
                    entry.kind,
                    entry.content,
                    self._json_dumps(entry.data),
                    entry.created_at.isoformat(),
                ),
            )

    def get_conversation_entries(self, incident_id: str) -> list[ConversationEntry]:
        with self.database.transaction() as connection:
            rows = connection.execute(
                "SELECT * FROM conversation_entries WHERE incident_id = ? ORDER BY rowid",
                (incident_id,),
            ).fetchall()
        return [
            ConversationEntry(
                entry_id=row["entry_id"],
                role=row["role"],
                kind=row["kind"],
                content=row["content"],
                data=json.loads(row["data_json"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def save_transition(
        self,
        incident_id: str,
        transition: StatusTransition,
        stage: WorkflowStage | None,
    ) -> None:
        with self.database.transaction(immediate=True) as connection:
            cursor = connection.execute(
                """
                UPDATE incidents
                SET status = ?, stage = ?, updated_at = ?
                WHERE incident_id = ? AND status = ?
                """,
                (
                    transition.to_status.value,
                    stage.value if stage else None,
                    transition.changed_at.isoformat(),
                    incident_id,
                    transition.from_status.value,
                ),
            )
            if cursor.rowcount != 1:
                current_row = connection.execute(
                    "SELECT status FROM incidents WHERE incident_id = ?", (incident_id,)
                ).fetchone()
                if current_row is None:
                    raise IncidentNotFoundError(f"Incident 不存在: {incident_id}")
                raise IncidentStatusConflictError(
                    f"Incident 状态已变化: expected={transition.from_status.value}, "
                    f"actual={current_row['status']} (incident_id={incident_id})"
                )
            self._insert_transition(connection, incident_id, transition)

    def add_evidence(
        self,
        incident_id: str,
        evidence: Evidence,
        updated_at: datetime,
    ) -> None:
        with self.database.transaction(immediate=True) as connection:
            cursor = connection.execute(
                "UPDATE incidents SET updated_at = ? WHERE incident_id = ?",
                (updated_at.isoformat(), incident_id),
            )
            if cursor.rowcount != 1:
                raise IncidentNotFoundError(f"Incident 不存在: {incident_id}")
            self._insert_evidence(connection, incident_id, evidence)

    @staticmethod
    def _insert_evidence(
        connection: sqlite3.Connection,
        incident_id: str,
        evidence: Evidence,
    ) -> None:
        try:
            connection.execute(
                """
                INSERT INTO evidence (
                    incident_id, evidence_id, source, kind, summary,
                    data_json, created_at, stage
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident_id,
                    evidence.evidence_id,
                    evidence.source,
                    evidence.kind,
                    evidence.summary,
                    IncidentRepository._json_dumps(evidence.data),
                    evidence.created_at.isoformat(),
                    evidence.stage.value if evidence.stage else None,
                ),
            )
        except sqlite3.IntegrityError as exc:
            if connection.execute(
                """
                SELECT 1 FROM evidence
                WHERE incident_id = ? AND evidence_id = ?
                """,
                (incident_id, evidence.evidence_id),
            ).fetchone():
                raise DuplicateEvidenceError(
                    f"重复的 evidence_id: {evidence.evidence_id} (incident_id={incident_id})"
                ) from exc
            raise

    @staticmethod
    def _insert_transition(
        connection: sqlite3.Connection,
        incident_id: str,
        transition: StatusTransition,
    ) -> None:
        connection.execute(
            """
            INSERT INTO status_transitions (
                incident_id, from_status, to_status, reason, changed_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                incident_id,
                transition.from_status.value,
                transition.to_status.value,
                transition.reason,
                transition.changed_at.isoformat(),
            ),
        )

    @staticmethod
    def _evidence_from_row(row: sqlite3.Row) -> Evidence:
        return Evidence(
            evidence_id=row["evidence_id"],
            source=row["source"],
            kind=row["kind"],
            summary=row["summary"],
            data=json.loads(row["data_json"]),
            created_at=row["created_at"],
            stage=row["stage"],
        )

    @staticmethod
    def _transition_from_row(row: sqlite3.Row) -> StatusTransition:
        return StatusTransition(
            from_status=IncidentStatus(row["from_status"]),
            to_status=IncidentStatus(row["to_status"]),
            reason=row["reason"],
            changed_at=row["changed_at"],
        )

    @staticmethod
    def _json_dumps(value: object) -> str:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
