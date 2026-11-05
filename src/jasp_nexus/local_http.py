"""Bounded JSON-over-HTTP transport: no implicit proxies, no redirects."""

from __future__ import annotations

import json
import socket
import time
from dataclasses import dataclass
from http.client import HTTPException, HTTPResponse
from urllib.error import HTTPError, URLError
from urllib.request import (
    HTTPRedirectHandler,
    OpenerDirector,
    ProxyHandler,
    Request,
    build_opener,
)

READ_CHUNK_BYTES = 64 * 1024

# Stable error categories; persisted as-is, never with remote bodies.
CONNECTION_REFUSED = "connection_refused"
CONNECTION_ERROR = "connection_error"
TIMEOUT = "timeout"
HTTP_ERROR = "http_error"
REDIRECT = "redirect"
INVALID_JSON = "invalid_json"
UNEXPECTED_RESPONSE = "unexpected_response"
RESPONSE_TOO_LARGE = "response_too_large"


class TransportError(Exception):
    """Service/transport failure (exit code 3). The message never echoes remote bodies."""

    def __init__(self, category: str, message: str, http_status: int | None = None) -> None:
        super().__init__(message)
        self.category = category
        self.http_status = http_status


@dataclass(frozen=True)
class JsonResponse:
    status: int
    data: object


class _RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, *args: object, **kwargs: object) -> None:
        return None


def build_local_opener() -> OpenerDirector:
    """Empty ProxyHandler disables environment/registry proxies; redirects become errors."""
    return build_opener(ProxyHandler({}), _RejectRedirects())


def request_json(
    url: str,
    *,
    timeout: float,
    max_bytes: int,
    payload: dict[str, object] | None = None,
    opener: OpenerDirector | None = None,
) -> JsonResponse:
    """Send one GET (or POST when payload is given) and parse a bounded JSON body."""
    deadline = time.monotonic() + timeout
    request = _build_request(url, payload)
    try:
        with (opener or build_local_opener()).open(request, timeout=timeout) as response:
            body = _read_bounded(response, max_bytes, deadline)
            status = response.status
    except HTTPError as exc:
        exc.close()
        raise _http_error(exc.code) from None
    except TransportError:
        raise
    except TimeoutError:
        raise TransportError(TIMEOUT, "Tiempo de espera agotado.") from None
    except URLError as exc:
        raise _url_error(exc.reason) from None
    except ConnectionRefusedError:
        raise TransportError(CONNECTION_REFUSED, "Conexión rechazada.") from None
    except (HTTPException, OSError) as exc:
        raise TransportError(
            CONNECTION_ERROR, f"Error de conexión ({type(exc).__name__})."
        ) from None
    return JsonResponse(status=status, data=_parse_json(body))


def _build_request(url: str, payload: dict[str, object] | None) -> Request:
    headers = {"Accept": "application/json"}
    if payload is None:
        return Request(url, headers=headers, method="GET")
    headers["Content-Type"] = "application/json"
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return Request(url, data=body, headers=headers, method="POST")


def _read_bounded(response: HTTPResponse, max_bytes: int, deadline: float) -> bytes:
    declared = response.headers.get("Content-Length")
    if declared and declared.isdigit() and int(declared) > max_bytes:
        raise TransportError(RESPONSE_TOO_LARGE, f"Respuesta mayor que {max_bytes} bytes.")
    chunks: list[bytes] = []
    total = 0
    while True:
        if time.monotonic() > deadline:
            raise TransportError(TIMEOUT, "Plazo total agotado durante la lectura.")
        chunk = response.read(min(READ_CHUNK_BYTES, max_bytes + 1 - total))
        if not chunk:
            return b"".join(chunks)
        total += len(chunk)
        if total > max_bytes:
            raise TransportError(RESPONSE_TOO_LARGE, f"Respuesta mayor que {max_bytes} bytes.")
        chunks.append(chunk)


def _parse_json(body: bytes) -> object:
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise TransportError(INVALID_JSON, "La respuesta no es JSON válido.") from None


def _http_error(code: int) -> TransportError:
    if 300 <= code < 400:
        return TransportError(REDIRECT, f"Redirección HTTP {code} rechazada.", code)
    return TransportError(HTTP_ERROR, f"El servicio respondió HTTP {code}.", code)


def _url_error(reason: object) -> TransportError:
    if isinstance(reason, ConnectionRefusedError):
        return TransportError(CONNECTION_REFUSED, "Conexión rechazada.")
    if isinstance(reason, TimeoutError | socket.timeout):
        return TransportError(TIMEOUT, "Tiempo de espera agotado.")
    return TransportError(CONNECTION_ERROR, f"Error de conexión ({type(reason).__name__}).")
