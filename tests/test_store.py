import tempfile
import unittest
from pathlib import Path
from jasp_nexus.store import TaskStore


class TaskStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "nexus.sqlite3"
        self.store = TaskStore(self.path)
        self.id = self.store.create("Build RSVP", "visual", 1, 3)

    def test_persists_and_audits(self):
        self.store.assign(self.id, "claude", "commandcode", "codex")
        self.store.advance(self.id, "running", "commandcode", "started")
        self.store.advance(self.id, "in_review", "commandcode", "diff abc123; tests passed")
        self.store.advance(self.id, "approved", "codex", "reviewed diff and test logs")
        self.assertEqual(TaskStore(self.path).get(self.id)["state"], "approved")
        self.assertEqual(len(self.store.history(self.id)), 5)

    def test_executor_cannot_approve(self):
        self.store.assign(self.id, "claude", "commandcode", "codex")
        self.store.advance(self.id, "running", "commandcode", "")
        self.store.advance(self.id, "in_review", "commandcode", "diff")
        with self.assertRaisesRegex(ValueError, "independent"):
            self.store.advance(self.id, "approved", "commandcode", "looks good")

    def test_review_needs_evidence(self):
        self.store.assign(self.id, "claude", "commandcode", "codex")
        self.store.advance(self.id, "running", "commandcode", "")
        self.store.advance(self.id, "in_review", "commandcode", "diff")
        with self.assertRaisesRegex(ValueError, "evidence"):
            self.store.advance(self.id, "approved", "codex", " ")

    def test_invalid_transition(self):
        with self.assertRaisesRegex(ValueError, "Illegal"):
            self.store.advance(self.id, "approved", "codex", "no")

    def test_retry_limit(self):
        for _ in range(3):
            self.store.assign(self.id, "claude", "commandcode", "codex")
            self.store.advance(self.id, "running", "commandcode", "")
            self.store.advance(self.id, "in_review", "commandcode", "diff")
            self.store.advance(self.id, "changes_requested", "codex", "fix")
        with self.assertRaisesRegex(ValueError, "Maximum"):
            self.store.assign(self.id, "claude", "commandcode", "codex")


if __name__ == "__main__":
    unittest.main()
