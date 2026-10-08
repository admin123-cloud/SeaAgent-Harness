import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


SCHEMA_VERSION = 1

_SCHEMA_V1 = (
    """
    CREATE TABLE IF NOT EXISTS incidents (
        incident_id TEXT PRIMARY KEY,
        schema_version TEXT NOT NULL,
        goal TEXT NOT NULL,
        environment_json TEXT NOT NULL,
        status TEXT NOT NULL,
        stage TEXT,
        iteration INTEGER NOT NULL CHECK (iteration >= 0),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS evidence (
        incident_id TEXT NOT NULL,
        evidence_id TEXT NOT NULL,
        source TEXT NOT NULL,
        kind TEXT NOT NULL,
        summary TEXT NOT NULL,
        data_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        stage TEXT,
        PRIMARY KEY (incident_id, evidence_id),
        FOREIGN KEY (incident_id)
            REFERENCES incidents (incident_id)
            ON DELETE CASCADE
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_evidence_incident_created ON evidence (incident_id, created_at)",
    """
    CREATE TABLE IF NOT EXISTS status_transitions (
        transition_id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_id TEXT NOT NULL,
        from_status TEXT NOT NULL,
        to_status TEXT NOT NULL,
        reason TEXT,
        changed_at TEXT NOT NULL,
        FOREIGN KEY (incident_id)
            REFERENCES incidents (incident_id)
            ON DELETE CASCADE
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_status_transitions_incident ON status_transitions (incident_id, transition_id)",
)


class SQLiteDatabase:
    """SQLite 连接和 schema 生命周期。每个操作独立开关连接并启用外键。"""

    def __init__(self, db_path: str | Path | None = None) -> None:
        configured_path = db_path or os.getenv("SRE_AGENT_DB_PATH")
        if configured_path is None:
            configured_path = (
                Path(__file__).resolve().parents[3]
                / ".sre-agent-data"
                / "sre-agent.sqlite3"
            )
        self.db_path = Path(configured_path).expanduser()

    @contextmanager
    def transaction(self, *, immediate: bool = False) -> Iterator[sqlite3.Connection]:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path, timeout=10.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            connection.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        """创建初始 schema；后续结构变化通过递增 user_version 增加迁移。"""
        with self.transaction(immediate=True) as connection:
            current_version = connection.execute("PRAGMA user_version").fetchone()[0]
            if current_version > SCHEMA_VERSION:
                raise RuntimeError(
                    f"数据库 schema 版本 {current_version} 高于当前程序支持版本 {SCHEMA_VERSION}"
                )

            if current_version == 0:
                for statement in _SCHEMA_V1:
                    connection.execute(statement)
                connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
