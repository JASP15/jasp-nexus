import io
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing, redirect_stderr, redirect_stdout
from pathlib import Path

from local_fakes import CHAT, MODELS, SYSTEM_STATS, FakeServer, Route, closed_port_url, json_route

from jasp_nexus.cli import main

PROMPT = "PROMPT-PRIVADO-123"
REPLY = "Hola desde el modelo"


class LocalCliTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(temp.cleanup)
        self.dir = Path(temp.name)
        self.db = self.dir / "state.sqlite3"
        self.fake = FakeServer().__enter__()
        self.addCleanup(self.fake.__exit__)
        self.fake.routes[("GET", "/v1/models")] = json_route(MODELS)
        self.fake.routes[("GET", "/system_stats")] = json_route(SYSTEM_STATS)
        self.fake.routes[("POST", "/v1/chat/completions")] = json_route(CHAT)
        self.write_config()

    def write_config(self, **overrides: object) -> None:
        config: dict[str, object] = {
            "lm_studio_url": f"{self.fake.base}/v1",
            "comfyui_url": self.fake.base,
            "timeout_seconds": 2,
            "max_response_bytes": 65536,
            "max_tokens": 64,
        }
        config.update(overrides)
        self.config = self.dir / "local.json"
        self.config.write_text(json.dumps(config), encoding="utf-8")

    def run_cli(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        argv = ["--db", str(self.db), "--local-config", str(self.config), *args]
        with redirect_stdout(out), redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def runs(self) -> list[dict[str, object]]:
        code, out, _ = self.run_cli("runs")
        self.assertEqual(code, 0)
        return json.loads(out)

    def test_providers_all_ok(self) -> None:
        code, out, _ = self.run_cli("providers")
        self.assertEqual(code, 0)
        self.assertIn("lm_studio", out)
        self.assertIn("comfyui", out)
        self.assertEqual(out.count("OK HTTP 200"), 2)
        self.assertEqual({r["status"] for r in self.runs()}, {"succeeded"})

    def test_providers_reports_both_when_one_fails(self) -> None:
        self.write_config(comfyui_url=closed_port_url(), timeout_seconds=5)
        code, out, _ = self.run_cli("providers")
        self.assertEqual(code, 3)
        self.assertIn("OK HTTP 200", out)
        self.assertIn("FALLO connection_refused", out)
        statuses = {r["service"]: r["status"] for r in self.runs()}
        self.assertEqual(statuses, {"lm_studio": "succeeded", "comfyui": "failed"})

    def test_comfyui_root_200_without_schema_is_not_healthy(self) -> None:
        self.fake.routes[("GET", "/system_stats")] = json_route({"hello": "world"})
        code, out, _ = self.run_cli("providers")
        self.assertEqual(code, 3)
        self.assertIn("unexpected_response", out)

    def test_models_lists_exact_ids(self) -> None:
        code, out, err = self.run_cli("models")
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "qwen/qwen3-4b")
        self.assertIn("cargado", err)

    def test_models_empty_list_is_valid(self) -> None:
        self.fake.routes[("GET", "/v1/models")] = json_route({"object": "list", "data": []})
        code, out, _ = self.run_cli("models")
        self.assertEqual(code, 0)
        self.assertIn("lista vacía", out)

    def test_models_bad_schema_and_service_down(self) -> None:
        self.fake.routes[("GET", "/v1/models")] = json_route({"models": ["x"]})
        code, _, err = self.run_cli("models")
        self.assertEqual(code, 3)
        self.assertIn("unexpected_response", err)
        self.write_config(lm_studio_url=closed_port_url() + "/v1", timeout_seconds=5)
        code, _, err = self.run_cli("models")
        self.assertEqual(code, 3)
        self.assertIn("connection_refused", err)

    def test_chat_success_prints_text_and_stores_no_payload(self) -> None:
        code, out, err = self.run_cli("chat", "--model", "qwen/qwen3-4b", "--prompt", PROMPT)
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), REPLY)
        self.assertIn("total=11", err)
        method, path, body = self.fake.requests[-1]
        self.assertEqual((method, path), ("POST", "/v1/chat/completions"))
        sent = json.loads(body)
        self.assertEqual(sent["stream"], False)
        self.assertEqual(sent["max_tokens"], 64)
        self.assertNotIn("tools", sent)
        chat_run = next(r for r in self.runs() if r["operation"] == "chat")
        self.assertEqual(chat_run["status"], "succeeded")
        self.assertEqual(chat_run["model_id"], "qwen/qwen3-4b")
        self.assertEqual(chat_run["total_tokens"], 11)
        self.assert_db_free_of(PROMPT, REPLY)

    def test_chat_without_usage_records_unknown(self) -> None:
        reply = {"choices": [{"message": {"role": "assistant", "content": "ok"}}]}
        self.fake.routes[("POST", "/v1/chat/completions")] = json_route(reply)
        code, _, err = self.run_cli("chat", "--model", "qwen/qwen3-4b", "--prompt", "hola")
        self.assertEqual(code, 0)
        self.assertIn("desconocido", err)
        chat_run = next(r for r in self.runs() if r["operation"] == "chat")
        self.assertIsNone(chat_run["total_tokens"])

    def test_chat_unannounced_model_fails_before_sending(self) -> None:
        code, _, err = self.run_cli("chat", "--model", "otro/modelo", "--prompt", PROMPT)
        self.assertEqual(code, 2)
        self.assertIn("no está anunciado", err)
        self.assertNotIn("POST", [method for method, _, _ in self.fake.requests])
        chat_run = next(r for r in self.runs() if r["operation"] == "chat")
        self.assertEqual(chat_run["error_category"], "model_not_announced")
        self.assertIsNone(chat_run["model_id"])

    def test_chat_with_empty_model_list(self) -> None:
        self.fake.routes[("GET", "/v1/models")] = json_route({"data": []})
        code, _, _ = self.run_cli("chat", "--model", "qwen/qwen3-4b", "--prompt", "hola")
        self.assertEqual(code, 2)

    def test_chat_http_error_body_not_persisted(self) -> None:
        self.fake.routes[("POST", "/v1/chat/completions")] = Route(
            status=500, body=b"REMOTE-ERROR-DETAIL"
        )
        code, out, err = self.run_cli("chat", "--model", "qwen/qwen3-4b", "--prompt", PROMPT)
        self.assertEqual(code, 3)
        self.assertNotIn("REMOTE-ERROR-DETAIL", out + err)
        chat_run = next(r for r in self.runs() if r["operation"] == "chat")
        self.assertEqual((chat_run["status"], chat_run["http_status"]), ("failed", 500))
        self.assert_db_free_of(PROMPT, "REMOTE-ERROR-DETAIL")

    def test_chat_timeout_and_bad_reply_schema(self) -> None:
        self.fake.routes[("POST", "/v1/chat/completions")] = json_route({"choices": []})
        code, _, err = self.run_cli("chat", "--model", "qwen/qwen3-4b", "--prompt", "hola")
        self.assertEqual(code, 3)
        self.assertIn("unexpected_response", err)
        self.fake.routes[("POST", "/v1/chat/completions")] = Route(delay=1.5, body=b"{}")
        self.write_config(timeout_seconds=0.5)
        code, _, err = self.run_cli("chat", "--model", "qwen/qwen3-4b", "--prompt", "hola")
        self.assertEqual(code, 3)
        self.assertIn("timeout", err)

    def test_chat_input_validation(self) -> None:
        cases = (
            ("--prompt", "   "),
            ("--prompt", "hola", "--max-tokens", "0"),
            ("--prompt", "hola", "--max-tokens", "65"),
            ("--prompt", "hola", "--task-id", "inexistente"),
        )
        for extra in cases:
            with self.subTest(extra=extra):
                code, _, _ = self.run_cli("chat", "--model", "qwen/qwen3-4b", *extra)
                self.assertEqual(code, 2)
        self.assertNotIn("POST", [method for method, _, _ in self.fake.requests])

    def test_chat_links_existing_task_without_changing_it(self) -> None:
        code, task_id, _ = self.run_cli("create", "--title", "Probar chat")
        task_id = task_id.strip()
        code, _, _ = self.run_cli(
            "chat", "--model", "qwen/qwen3-4b", "--prompt", "hola", "--task-id", task_id
        )
        self.assertEqual(code, 0)
        _, shown, _ = self.run_cli("show", task_id)
        self.assertEqual(json.loads(shown)["state"], "backlog")
        _, history, _ = self.run_cli("history", task_id)
        self.assertEqual(len(json.loads(history)), 1)

    def test_invalid_config_and_url(self) -> None:
        self.write_config(lm_studio_url="http://example.com/v1")
        code, _, err = self.run_cli("models")
        self.assertEqual(code, 2)
        self.assertIn("Host no permitido", err)
        self.assertEqual(self.fake.requests, [])

    def test_legacy_commands_still_work(self) -> None:
        code, task_id, _ = self.run_cli("create", "--title", "Legacy", "--kind", "backend")
        self.assertEqual(code, 0)
        task_id = task_id.strip()
        code, out, _ = self.run_cli("route", task_id)
        self.assertEqual(code, 0)
        self.assertIn("SIMULATION ONLY", out)
        code, out, _ = self.run_cli("list")
        self.assertEqual(json.loads(out)[0]["id"], task_id)
        code, _, err = self.run_cli("show", "missing")
        self.assertEqual(code, 2)
        self.assertIn("Task not found", err)

    def assert_db_free_of(self, *needles: str) -> None:
        raw = self.db.read_bytes()
        for needle in needles:
            self.assertNotIn(needle.encode("utf-8"), raw)
        with closing(sqlite3.connect(self.db)) as db:
            dumped = "\n".join(db.iterdump())
        for needle in needles:
            self.assertNotIn(needle, dumped)


if __name__ == "__main__":
    unittest.main()
