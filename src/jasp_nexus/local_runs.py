"""Additive SQLite metadata for local service runs. Never stores prompts or bodies."""

from __future__ import annotations

import sqlite3
import time
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .local_services import Usage

SERVICES = ("lm_studio", "comfyui")
OPERATIONS = ("probe", "models", "chat")
UNCONFIRMED = "no_confirmado"

SCHEMA = """
CREATE TABLE IF NOT EXISTS local_runs (
    id TEXT PRIMARY KEY,
    service TEXT NOT NULL CHECK (service IN ('lm_studio', 'comfyui')),
    operation TEXT NOT NULL CHECK (operation IN ('probe', 'models', 'chat')),
    model_id TEXT,
    task_id TEXT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    duration_ms INTEGER,
    status TEXT NOT NULL CHECK (status IN ('running', 'succeeded', 'failed')),
    error_category TEXT,
    http_status INTEGER,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER
);
CREATE TABLE IF NOT EXISTS local_run_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES local_runs(id),
    event TEXT NOT NULL CHECK (event IN ('started', 'finished')),
    status TEXT NOT NULL CHECK (status IN ('running', 'succeeded', 'failed')),
    error_category TEXT,
    created_at TEXT NOT NULL
);
"""


@dataclass
class RunHandle:
    run_id: str
    started: float


@dataclass(frozen=True)
class RunOutcome:
    status: str
    error_category: str | None = None
    http_status: int | None = None
    usage: Usage = Usage()


class RunStore:
    """Lives next to TaskStore in the same file; does not touch tasks/events."""

    def __init__(self, filename: str | Path) -> None:
        self.filename = Path(filename)
        self.filename.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as db, db:
            db.executescript(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.filename, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        return db

    def start(
        self,
        service: str,
        operation: str,
        model_id: str | None = None,
        task_id: str | None = None,
    ) -> RunHandle:
        if service not in SERVICES or operation not in OPERATIONS:
            raise ValueError("Servicio u operación desconocidos.")
        run_id = uuid4().hex[:12]
        now = _utc_now()
        with closing(self._connect()) as db, db:
            if task_id is not None:
                self._require_task(db, task_id)
            db.execute(
                "INSERT INTO local_runs (id,service,operation,model_id,task_id,started_at,status) "
                "VALUES (?,?,?,?,?,?,'running')",
                (run_id, service, operation, model_id, task_id, now),
            )
            db.execute(
                "INSERT INTO local_run_events (run_id,event,status,created_at) "
                "VALUES (?,'started','running',?)",
                (run_id, now),
            )
        return RunHandle(run_id=run_id, started=time.monotonic())

    def finish(self, handle: RunHandle, outcome: RunOutcome) -> int:
        """Record the result; returns the measured duration in milliseconds."""
        if outcome.status not in {"succeeded", "failed"}:
            raise ValueError("Estado final inválido.")
        duration_ms = round((time.monotonic() - handle.started) * 1000)
        now = _utc_now()
        usage = outcome.usage
        with closing(self._connect()) as db, db:
            db.execute(
                "UPDATE local_runs SET finished_at=?,duration_ms=?,status=?,error_category=?,"
                "http_status=?,prompt_tokens=?,completion_tokens=?,total_tokens=? "
                "WHERE id=? AND status='running'",
                (
                    now,
                    duration_ms,
                    outcome.status,
                    outcome.error_category,
                    outcome.http_status,
                    usage.prompt_tokens,
                    usage.completion_tokens,
                    usage.total_tokens,
                    handle.run_id,
                ),
            )
            db.execute(
                "INSERT INTO local_run_events (run_id,event,status,error_category,created_at) "
                "VALUES (?,'finished',?,?,?)",
                (handle.run_id, outcome.status, outcome.error_category, now),
            )
        return duration_ms

    def list(self, limit: int = 20) -> list[dict[str, object]]:
        """Recent runs; an unfinished 'running' row is shown as unconfirmed, never success."""
        with closing(self._connect()) as db, db:
            rows = db.execute(
                "SELECT * FROM local_runs ORDER BY started_at DESC, rowid DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [_present(dict(row)) for row in rows]

    def events(self, run_id: str) -> list[dict[str, object]]:
        with closing(self._connect()) as db, db:
            rows = db.execute(
                "SELECT event,status,error_category,created_at FROM local_run_events "
                "WHERE run_id = ? ORDER BY id",
                (run_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _require_task(db: sqlite3.Connection, task_id: str) -> None:
        exists = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='tasks'"
        ).fetchone()
        if (
            exists is None
            or db.execute("SELECT 1 FROM tasks WHERE id = ?", (task_id,)).fetchone() is None
        ):
            raise ValueError(f"Tarea no encontrada: {task_id}")


def _present(row: dict[str, object]) -> dict[str, object]:
    if row["status"] == "running":
        row["status"] = UNCONFIRMED
    return row


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")
