import tempfile
from pathlib import Path
import unittest
from jasp_nexus.core import Agent, load_agents, route


def sample_agents():
    return [
        Agent("claude", "claude_code", frozenset({"coordinator", "reviewer", "worker"}), frozenset({"visual", "general"}), 3, 3, 4, True),
        Agent("codex", "codex", frozenset({"coordinator", "reviewer", "worker"}), frozenset({"integration", "backend", "general"}), 3, 3, 3, True),
        Agent("commandcode", "commandcode", frozenset({"worker"}), frozenset({"visual", "general"}), 1, 1, 1, True),
    ]


class RoutingTests(unittest.TestCase):
    def test_simple_visual_uses_economic_worker_and_independent_reviewer(self):
        p = route("visual", 1, 3, sample_agents())
        self.assertEqual(p.coordinator, "claude")
        self.assertEqual(p.worker, "commandcode")
        self.assertEqual(p.reviewer, "claude")

    def test_integration_prefers_codex(self):
        p = route("integration", 3, 3, sample_agents())
        self.assertEqual(p.coordinator, "codex")
        self.assertNotEqual(p.worker, p.reviewer)

    def test_no_independent_reviewer_fails_closed(self):
        only = [Agent("claude", "claude_code", frozenset({"coordinator", "worker", "reviewer"}), frozenset({"general"}), 3, 3, 1, True)]
        with self.assertRaisesRegex(ValueError, "independent reviewer"):
            route("general", 3, 3, only)

    def test_invalid_task_rejected(self):
        with self.assertRaises(ValueError):
            route("visual", 4, 2, sample_agents())

    def test_duplicate_id_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "a.json"
            path.write_text('{"agents":[{"id":"x","provider":"a","roles":[],"specialties":[],"max_complexity":1,"review_quality":1,"cost_rank":1,"enabled":true},{"id":"x"}]}')
            with self.assertRaisesRegex(ValueError, "unique"):
                load_agents(path)


if __name__ == "__main__":
    unittest.main()
