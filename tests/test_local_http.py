import os
import unittest
from unittest import mock

from local_fakes import FakeServer, Route, closed_port_url, json_route

from jasp_nexus import local_http
from jasp_nexus.local_http import TransportError, request_json


class LocalHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake = FakeServer().__enter__()
        self.addCleanup(self.fake.__exit__)

    def fetch(self, path: str, **kwargs: object) -> object:
        options: dict[str, object] = {"timeout": 2.0, "max_bytes": 4096}
        options.update(kwargs)
        return request_json(self.fake.base + path, **options)  # type: ignore[arg-type]

    def assert_category(self, category: str, path: str, **kwargs: object) -> TransportError:
        with self.assertRaises(TransportError) as ctx:
            self.fetch(path, **kwargs)
        self.assertEqual(ctx.exception.category, category)
        return ctx.exception

    def test_get_and_post_json(self) -> None:
        self.fake.routes[("GET", "/a")] = json_route({"ok": True})
        self.fake.routes[("POST", "/b")] = json_route({"posted": True})
        self.assertEqual(self.fetch("/a").data, {"ok": True})  # type: ignore[attr-defined]
        response = self.fetch("/b", payload={"x": 1})
        self.assertEqual(response.data, {"posted": True})  # type: ignore[attr-defined]
        self.assertEqual(self.fake.requests[-1][2], b'{"x": 1}')

    def test_http_error_does_not_echo_remote_body(self) -> None:
        self.fake.routes[("GET", "/e")] = Route(status=500, body=b"SECRET-REMOTE-BODY")
        error = self.assert_category(local_http.HTTP_ERROR, "/e")
        self.assertEqual(error.http_status, 500)
        self.assertNotIn("SECRET", str(error))

    def test_redirect_is_rejected_and_not_followed(self) -> None:
        self.fake.routes[("GET", "/r")] = Route(status=302, headers={"Location": "/target"})
        self.fake.routes[("GET", "/target")] = json_route({"followed": True})
        self.assert_category(local_http.REDIRECT, "/r")
        self.assertEqual([path for _, path, _ in self.fake.requests], ["/r"])

    def test_environment_proxy_is_ignored(self) -> None:
        self.fake.routes[("GET", "/p")] = json_route({"direct": True})
        proxy = closed_port_url()
        env = {"HTTP_PROXY": proxy, "http_proxy": proxy, "NO_PROXY": "", "no_proxy": ""}
        with mock.patch.dict(os.environ, env):
            self.assertEqual(self.fetch("/p").data, {"direct": True})  # type: ignore[attr-defined]

    def test_invalid_json(self) -> None:
        self.fake.routes[("GET", "/j")] = Route(body=b"<html>no</html>")
        self.assert_category(local_http.INVALID_JSON, "/j")

    def test_response_too_large_declared_and_streamed(self) -> None:
        self.fake.routes[("GET", "/big")] = Route(body=b"[" + b"1," * 5000 + b"1]")
        self.assert_category(local_http.RESPONSE_TOO_LARGE, "/big")
        self.fake.routes[("GET", "/stream")] = Route(
            body=b"[" + b"1," * 5000 + b"1]", omit_length=True
        )
        self.assert_category(local_http.RESPONSE_TOO_LARGE, "/stream")

    def test_timeout(self) -> None:
        self.fake.routes[("GET", "/slow")] = Route(delay=1.5)
        self.assert_category(local_http.TIMEOUT, "/slow", timeout=0.3)

    def test_connection_refused(self) -> None:
        with self.assertRaises(TransportError) as ctx:
            request_json(closed_port_url() + "/v1/models", timeout=5.0, max_bytes=4096)
        self.assertEqual(ctx.exception.category, local_http.CONNECTION_REFUSED)


if __name__ == "__main__":
    unittest.main()
