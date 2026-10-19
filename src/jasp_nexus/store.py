"""Local audited state, separate from CAO's database."""
from __future__ import annotations
from pathlib import Path
import sqlite3
from uuid import uuid4

TRANSITIONS = {
    "backlog": {"assigned", "blocked"},
    "assigned": {"running", "blocked"},
    "running": {"in_review", "blocked"},
    "in_review": {"approved", "changes_requested", "blocked"},
    "changes_requested": {"assigned", "blocked"},
    "blocked": {"assigned"},
    "approved": set(),
}


class TaskStore:
    def __init__(self, filename: str | Path):
        self.filename = Path(filename)
        self.filename.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    complexity INTEGER NOT NULL,
                    quality INTEGER NOT NULL,
                    state TEXT NOT NULL,
                    coordinator TEXT,
                    worker TEXT,
                    reviewer TEXT,
                    attempt INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL DEFAULT 3
                );
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    from_state TEXT,
                    to_state TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    note TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                );
                """
            )

    def _connect(self):
        db = sqlite3.connect(self.filename, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        return db

    def create(self, title: str, kind: str, complexity: int, quality: int) -> str:
        from .core import KINDS
        if not title.strip() or kind not in KINDS or complexity not in (1, 2, 3) or quality not in (1, 2, 3):
            raise ValueError("Invalid task attributes")
        task_id = uuid4().hex[:12]
        with self._connect() as db:
            db.execute(
                "INSERT INTO tasks (id,title,kind,complexity,quality,state) VALUES (?,?,?,?,?,?)",
                (task_id, title.strip(), kind, complexity, quality, "backlog"),
            )
            db.execute(
                "INSERT INTO events (task_id,from_state,to_state,actor,note) VALUES (?,?,?,?,?)",
                (task_id, None, "backlog", "operator", "created"),
            )
        return task_id

    def get(self, task_id: str) -> dict:
        with self._connect() as db:
            row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            raise ValueError(f"Task not found: {task_id}")
        return dict(row)

    def list(self) -> list[dict]:
        with self._connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM tasks ORDER BY rowid DESC")]

    def history(self, task_id: str) -> list[dict]:
        self.get(task_id)
        with self._connect() as db:
            return [
                dict(row) for row in db.execute(
                    "SELECT from_state,to_state,actor,note,created_at FROM events WHERE task_id = ? ORDER BY id",
                    (task_id,),
                )
            ]

    def assign(self, task_id: str, coordinator: str, worker: str, reviewer: str):
        if not coordinator or not worker or not reviewer or worker == reviewer:
            raise ValueError("A separate worker and reviewer are mandatory")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT state,attempt,max_attempts FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if row is None:
                raise ValueError("Task not found")
            if row["state"] not in {"backlog", "changes_requested", "blocked"}:
                raise ValueError("Task cannot be assigned from this state")
            if row["attempt"] >= row["max_attempts"]:
                raise ValueError("Maximum assignment attempts reached; manual reset required")
            db.execute(
                "UPDATE tasks SET coordinator=?,worker=?,reviewer=?,attempt=attempt+1,state='assigned' WHERE id=?",
                (coordinator, worker, reviewer, task_id),
            )
            db.execute(
                "INSERT INTO events (task_id,from_state,to_state,actor,note) VALUES (?,?,?,?,?)",
                (task_id, row["state"], "assigned", coordinator, f"assigned worker={worker}, reviewer={reviewer}"),
            )

    def advance(self, task_id: str, target: str, actor: str, note: str):
        if target not in TRANSITIONS:
            raise ValueError("Unknown state")
        if not actor.strip():
            raise ValueError("Actor is mandatory")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if row is None:
                raise ValueError("Task not found")
            old = row["state"]
            if target not in TRANSITIONS[old]:
                raise ValueError(f"Illegal transition: {old} -> {target}")
            if target == "assigned":
                raise ValueError("Use route to assign a worker and reviewer")
            if target in {"approved", "changes_requested"}:
                if actor != row["reviewer"] or actor == row["worker"]:
                    raise ValueError("Only the independent designated reviewer may record a review")
                if not note.strip():
                    raise ValueError("Review decisions need an evidence/reason note")
            if target == "in_review" and not note.strip():
                raise ValueError("Submitting for review needs a link or evidence note")
            db.execute("UPDATE tasks SET state = ? WHERE id = ?", (target, task_id))
            db.execute(
                "INSERT INTO events (task_id,from_state,to_state,actor,note) VALUES (?,?,?,?,?)",
                (task_id, old, target, actor, note.strip()),
            )
