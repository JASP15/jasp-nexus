import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from jasp_nexus.local_runs import UNCONFIRMED, RunOutcome, RunStore
from jasp_nexus.local_services import Usage
from jasp_nexus.store import TaskStore

FOUNDATION_SCHEMA = """
CREATE TABLE tasks (
    id TEXT PRIMARY KEY, title TEXT NOT NULL, kind TEXT NOT NULL,
    complexity INTEGER NOT NULL, quality INTEGER NOT NULL, state TEXT NOT NULL,
    coordinator TEXT, worker TEXT, reviewer TEXT,
    attempt INTEGER NOT NULL DEFAULT 0, max_attempts INTEGER NOT NULL DEFAULT 3
);
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL, from_state TEXT,
    to_state TEXT NOT NULL, actor TEXT NOT NULL, note TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
INSERT INTO tasks VALUES ('legacy000001','Old task','general',2,2,'running',
    'claude','kiro','codex',1,3);
INSERT INTO events (task_id,from_state,to_state,actor,note,created_at) VALUES
    ('legacy000001',NULL,'backlog','operator','created','2026-01-01 00:00:00'),
    ('legacy000001','backlog','assigned','claude','assigned','2026-01-01 00:01:00'),
    ('legacy000001','assigned','running','kiro','started','2026-01-01 00:02:00');
"""


def dump(path: Path, table: str) -> list[tuple[object, ...]]:
    with closing(sqlite3.connect(path)) as db:
        return db.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()


class RunStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "state.sqlite3"

    def test_populated_foundation_db_is_preserved_and_idempotent(self) -> None:
        with closing(sqlite3.connect(self.path)) as db:
            db.executescript(FOUNDATION_SCHEMA)
        tasks_before = dump(self.path, "tasks")
        events_before = dump(self.path, "events")
        for _ in range(3):
            TaskStore(self.path)
            RunStore(self.path)
        self.assertEqual(dump(self.path, "tasks"), tasks_before)
        self.assertEqual(dump(self.path, "events"), events_before)
        self.assertEqual(len(TaskStore(self.path).history("legacy000001")), 3)
        runs = RunStore(self.path)
        handle = runs.start("lm_studio", "chat", "qwen/qwen3-4b", task_id="legacy000001")
        runs.finish(handle, RunOutcome("succeeded", http_status=200))
        self.assertEqual(dump(self.path, "events"), events_before)
        self.assertEqual(TaskStore(self.path).get("legacy000001")["state"], "running")

    def test_success_failure_and_events(self) -> None:
        runs = RunStore(self.path)
        ok = runs.start("lm_studio", "chat", "m1")
        usage = Usage(prompt_tokens=3, completion_tokens=2, total_tokens=5)
        duration = runs.finish(ok, RunOutcome("succeeded", http_status=200, usage=usage))
        bad = runs.start("comfyui", "probe")
        runs.finish(bad, RunOutcome("failed", "timeout"))
        rows = {row["id"]: row for row in runs.list()}
        self.assertEqual(rows[ok.run_id]["status"], "succeeded")
        self.assertEqual(rows[ok.run_id]["total_tokens"], 5)
        self.assertEqual(rows[ok.run_id]["duration_ms"], duration)
        self.assertEqual(rows[bad.run_id]["status"], "failed")
        self.assertEqual(rows[bad.run_id]["error_category"], "timeout")
        self.assertIsNone(rows[bad.run_id]["prompt_tokens"])
        self.assertEqual([e["event"] for e in runs.events(bad.run_id)], ["started", "finished"])

    def test_unfinished_run_is_never_presented_as_success(self) -> None:
        runs = RunStore(self.path)
        handle = runs.start("lm_studio", "models")
        row = runs.list()[0]
        self.assertEqual(row["id"], handle.run_id)
        self.assertEqual(row["status"], UNCONFIRMED)
        self.assertIsNone(row["finished_at"])

    def test_unknown_task_and_enums_rejected(self) -> None:
        TaskStore(self.path)
        runs = RunStore(self.path)
        with self.assertRaisesRegex(ValueError, "Tarea no encontrada"):
            runs.start("lm_studio", "chat", task_id="nope")
        with self.assertRaises(ValueError):
            runs.start("ollama", "chat")
        self.assertEqual(runs.list(), [])

    def test_schema_has_no_payload_columns(self) -> None:
        RunStore(self.path)
        with closing(sqlite3.connect(self.path)) as db:
            columns = {
                row[1]
                for table in ("local_runs", "local_run_events")
                for row in db.execute(f"PRAGMA table_info({table})")
            }
        for forbidden in ("prompt", "response", "body", "content", "headers", "message", "url"):
            self.assertNotIn(forbidden, columns)


if __name__ == "__main__":
    unittest.main()
