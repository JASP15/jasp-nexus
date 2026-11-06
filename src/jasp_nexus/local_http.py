"""Bounded JSON-over-HTTP transport: one total deadline, no proxies, no redirects."""

from __future__ import annotations

import io
import json
import socket
import ssl
import time
from contextlib import closing, suppress
from dataclasses import dataclass
from functools import partial
from http.client import HTTPConnection, HTTPException, HTTPResponse
from urllib.parse import SplitResult, urlsplit

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


def request_json(
    url: str,
    *,
    timeout: float,
    max_bytes: int,
    payload: dict[str, object] | None = None,
) -> JsonResponse:
    """Send one GET (or POST when payload is given) and parse a bounded JSON body.

    ``timeout`` bounds the whole exchange (connection, TLS, request, headers and body):
    every blocking socket operation only gets the time left before one shared deadline.
    """
    parts = urlsplit(url)
    deadline = _Deadline(timeout)
    try:
        with closing(_BoundedConnection(parts, deadline)) as connection:
            connection.request(*_request_args(parts, payload))
            with connection.getresponse() as response:
                body = _read_body(response, max_bytes)
                status = response.status
    except TransportError:
        raise
    except TimeoutError:
        raise TransportError(TIMEOUT, f"Plazo total de {timeout:g} s agotado.") from None
    except ConnectionRefusedError:
        raise TransportError(CONNECTION_REFUSED, "Conexión rechazada.") from None
    except (HTTPException, OSError) as exc:
        raise TransportError(
            CONNECTION_ERROR, f"Error de conexión ({type(exc).__name__})."
        ) from None
    return JsonResponse(status=status, data=_parse_json(body))


class _Deadline:
    """End time of one exchange, measured with the monotonic clock."""

    def __init__(self, seconds: float) -> None:
        self._end = time.monotonic() + seconds

    def remaining(self) -> float:
        """Time the next blocking socket operation may wait; TimeoutError when none is left."""
        left = self._end - time.monotonic()
        if left <= 0:
            raise TimeoutError("plazo total agotado")
        return left


class _DeadlineReader(io.RawIOBase):
    """Raw socket reader for http.client: each recv waits at most until the deadline."""

    def __init__(self, sock: socket.socket, deadline: _Deadline) -> None:
        super().__init__()
        self._sock = sock
        self._deadline = deadline
        # makefile() keeps http.client's reference counting: the socket stays open
        # while the response is read, even after the connection object is closed.
        self._raw = sock.makefile("rb", buffering=0)

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: bytearray | memoryview) -> int | None:
        self._sock.settimeout(self._deadline.remaining())
        return self._raw.readinto(buffer)

    def close(self) -> None:
        self._raw.close()
        super().close()


class _BoundedResponse(HTTPResponse):
    """HTTPResponse whose status line, headers and body are read under the deadline."""

    def __init__(
        self,
        sock: socket.socket,
        debuglevel: int = 0,
        method: str | None = None,
        url: str | None = None,
        *,
        deadline: _Deadline,
    ) -> None:
        super().__init__(sock, debuglevel, method, url)
        self.fp.close()  # replace the unbounded reader before anything is read
        self.fp = io.BufferedReader(_DeadlineReader(sock, deadline))


class _BoundedConnection(HTTPConnection):
    """One-shot HTTP(S) connection whose connect, TLS, send and recv share the deadline.

    http.client, unlike urllib, never reads proxy settings and never follows redirects.
    """

    def __init__(self, parts: SplitResult, deadline: _Deadline) -> None:
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            raise ValueError(f"URL no admitida por el transporte local: {parts.geturl()!r}")
        secure = parts.scheme == "https"
        super().__init__(parts.hostname, parts.port or (443 if secure else 80))
        self._deadline = deadline
        self._tls = ssl.create_default_context() if secure else None
        self.response_class = partial(_BoundedResponse, deadline=deadline)

    def connect(self) -> None:
        sock: socket.socket = _open_socket(self.host, self.port, self._deadline)
        try:
            with suppress(OSError):  # as in http.client: Nagle only affects latency
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            if self._tls is not None:
                sock.settimeout(self._deadline.remaining())
                sock = self._tls.wrap_socket(sock, server_hostname=self.host)
        except BaseException:
            sock.close()
            raise
        self.sock = sock

    def send(self, data: bytes) -> None:
        if self.sock is None:
            self.connect()
        self.sock.settimeout(self._deadline.remaining())
        super().send(data)


def _open_socket(host: str, port: int, deadline: _Deadline) -> socket.socket:
    """Like socket.create_connection, but each address tried only gets the time left."""
    error = OSError(f"Sin direcciones para {host}.")
    for family, kind, proto, _, address in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM):
        sock = socket.socket(family, kind, proto)
        try:
            sock.settimeout(deadline.remaining())
            sock.connect(address)
        except OSError as exc:
            sock.close()
            error = exc
            continue
        return sock
    raise error


def _request_args(
    parts: SplitResult, payload: dict[str, object] | None
) -> tuple[str, str, bytes | None, dict[str, str]]:
    target = parts.path or "/"
    if parts.query:
        target = f"{target}?{parts.query}"
    headers = {"Accept": "application/json", "Connection": "close"}
    if payload is None:
        return "GET", target, None, headers
    headers["Content-Type"] = "application/json"
    return "POST", target, json.dumps(payload, ensure_ascii=False).encode("utf-8"), headers


def _read_body(response: HTTPResponse, max_bytes: int) -> bytes:
    """Reject non-2xx without reading the body; otherwise read at most max_bytes.

    A body shorter than its Content-Length is a failure, never a partial success.
    """
    if not 200 <= response.status < 300:
        raise _http_error(response.status)
    declared = response.headers.get("Content-Length")
    expected = int(declared) if declared and declared.isdigit() else None
    if expected is not None and expected > max_bytes:
        raise TransportError(RESPONSE_TOO_LARGE, f"Respuesta mayor que {max_bytes} bytes.")
    chunks: list[bytes] = []
    total = 0
    while chunk := response.read(min(READ_CHUNK_BYTES, max_bytes + 1 - total)):
        total += len(chunk)
        if total > max_bytes:
            raise TransportError(RESPONSE_TOO_LARGE, f"Respuesta mayor que {max_bytes} bytes.")
        chunks.append(chunk)
    if expected is not None and total < expected:
        raise TransportError(
            CONNECTION_ERROR, f"Respuesta incompleta: {total} de {expected} bytes declarados."
        )
    return b"".join(chunks)


def _parse_json(body: bytes) -> object:
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise TransportError(INVALID_JSON, "La respuesta no es JSON válido.") from None


def _http_error(code: int) -> TransportError:
    if 300 <= code < 400:
        return TransportError(REDIRECT, f"Redirección HTTP {code} rechazada.", code)
    return TransportError(HTTP_ERROR, f"El servicio respondió HTTP {code}.", code)
