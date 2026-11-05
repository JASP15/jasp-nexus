import json
import tempfile
import unittest
from pathlib import Path

from jasp_nexus.local_config import (
    DEFAULT_COMFYUI_URL,
    DEFAULT_LM_STUDIO_URL,
    ConfigError,
    load_local_config,
    validate_config,
    validate_service_url,
)


class LocalConfigTests(unittest.TestCase):
    def test_defaults(self) -> None:
        config = load_local_config(None)
        self.assertEqual(config.lm_studio_url, DEFAULT_LM_STUDIO_URL)
        self.assertEqual(config.comfyui_url, DEFAULT_COMFYUI_URL)
        self.assertEqual(config.max_tokens, 512)

    def test_example_file_is_valid(self) -> None:
        root = Path(__file__).resolve().parents[1]
        config = load_local_config(root / "config" / "local.example.json")
        self.assertEqual(config.timeout_seconds, 30.0)

    def test_invalid_json_and_missing_file(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
            path = Path(d) / "local.json"
            path.write_text("{no json", encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "JSON inválido"):
                load_local_config(path)
            with self.assertRaisesRegex(ConfigError, "No existe"):
                load_local_config(Path(d) / "missing.json")
            path.write_text(json.dumps([1]), encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "objeto"):
                load_local_config(path)

    def test_limits_must_be_finite_and_bounded(self) -> None:
        for data in (
            {"timeout_seconds": 0},
            {"timeout_seconds": float("inf")},
            {"timeout_seconds": float("nan")},
            {"timeout_seconds": 301},
            {"timeout_seconds": True},
            {"max_response_bytes": 10},
            {"max_response_bytes": 1.5},
            {"max_tokens": 0},
            {"max_tokens": 100000},
            {"unknown_key": 1},
        ):
            with self.subTest(data=data), self.assertRaises(ConfigError):
                validate_config(data)

    def test_rejected_urls(self) -> None:
        for url in (
            "ftp://127.0.0.1:1234",
            "http://user:pass@127.0.0.1:1234/v1",
            "http://127.0.0.1:1234/v1?x=1",
            "http://127.0.0.1:1234/v1#frag",
            "http://example.com/v1",
            "http://8.8.8.8/v1",
            "http://192.168.1.10:1234/v1",
            "http://127.0.0.1:99999/v1",
            "http:///v1",
        ):
            with self.subTest(url=url), self.assertRaises(ConfigError):
                validate_service_url(url, frozenset())

    def test_loopback_and_declared_private_host_accepted(self) -> None:
        validate_service_url("http://127.0.0.1:1234/v1", frozenset())
        validate_service_url("http://[::1]:1234/v1", frozenset())
        validate_service_url("http://localhost:8188", frozenset())
        config = validate_config(
            {
                "lm_studio_url": "http://172.20.0.1:1234/v1/",
                "allowed_private_hosts": ["172.20.0.1"],
            }
        )
        self.assertEqual(config.lm_studio_url, "http://172.20.0.1:1234/v1")

    def test_allowed_private_hosts_must_be_private_numeric(self) -> None:
        for hosts in (["8.8.8.8"], ["host.local"], ["127.0.0.1"], "172.20.0.1", [1]):
            with self.subTest(hosts=hosts), self.assertRaises(ConfigError):
                validate_config({"allowed_private_hosts": hosts})


if __name__ == "__main__":
    unittest.main()
