"""Read-only checks and a single non-streaming chat against local services."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .local_config import LocalConfig
from .local_http import UNEXPECTED_RESPONSE, JsonResponse, TransportError, request_json

LM_STUDIO = "lm_studio"
COMFYUI = "comfyui"

Requester = Callable[..., JsonResponse]


class ModelNotAnnouncedError(ValueError):
    """The requested model ID is not in LM Studio's list (exit code 2, nothing sent)."""


@dataclass(frozen=True)
class Usage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True)
class ChatReply:
    text: str
    usage: Usage
    http_status: int


@dataclass(frozen=True)
class Probe:
    service: str
    check: str


PROBES = (
    Probe(LM_STUDIO, "GET /v1/models"),
    Probe(COMFYUI, "GET /system_stats"),
)


def models_url(config: LocalConfig) -> str:
    return f"{config.lm_studio_url}/models"


def chat_url(config: LocalConfig) -> str:
    return f"{config.lm_studio_url}/chat/completions"


def system_stats_url(config: LocalConfig) -> str:
    return f"{config.comfyui_url}/system_stats"


def probe_url(probe: Probe, config: LocalConfig) -> str:
    return models_url(config) if probe.service == LM_STUDIO else system_stats_url(config)


def run_probe(probe: Probe, config: LocalConfig, requester: Requester = request_json) -> int:
    """Return the HTTP status after validating the documented response shape."""
    response = _get(probe_url(probe, config), config, requester)
    if probe.service == LM_STUDIO:
        parse_model_ids(response.data)
    else:
        _validate_system_stats(response.data)
    return response.status


def list_models(config: LocalConfig, requester: Requester = request_json) -> tuple[list[str], int]:
    """Return the announced IDs and the observed HTTP status."""
    response = _get(models_url(config), config, requester)
    return parse_model_ids(response.data), response.status


def parse_model_ids(data: object) -> list[str]:
    """OpenAI-compatible list: {"data": [{"id": "..."}]}; IDs kept exactly as published."""
    items = data.get("data") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise _unexpected("La lista de modelos no tiene el formato esperado.")
    ids: list[str] = []
    for item in items:
        model_id = item.get("id") if isinstance(item, dict) else None
        if not isinstance(model_id, str) or not model_id:
            raise _unexpected("Un modelo de la lista no tiene ID válido.")
        ids.append(model_id)
    return ids


def require_announced(model_id: str, announced: list[str]) -> None:
    if model_id not in announced:
        raise ModelNotAnnouncedError(
            f"El modelo {model_id!r} no está anunciado por LM Studio. Use `nexus models`."
        )


def chat(
    config: LocalConfig,
    model_id: str,
    prompt: str,
    max_tokens: int,
    requester: Requester = request_json,
) -> ChatReply:
    payload: dict[str, object] = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "max_tokens": max_tokens,
    }
    response = requester(
        chat_url(config),
        timeout=config.timeout_seconds,
        max_bytes=config.max_response_bytes,
        payload=payload,
    )
    return ChatReply(
        text=_reply_text(response.data),
        usage=parse_usage(response.data),
        http_status=response.status,
    )


def parse_usage(data: object) -> Usage:
    """Optional token usage; anything missing or invalid stays unknown (None)."""
    usage = data.get("usage") if isinstance(data, dict) else None
    if not isinstance(usage, dict):
        return Usage()
    return Usage(
        prompt_tokens=_count(usage.get("prompt_tokens")),
        completion_tokens=_count(usage.get("completion_tokens")),
        total_tokens=_count(usage.get("total_tokens")),
    )


def _get(url: str, config: LocalConfig, requester: Requester) -> JsonResponse:
    return requester(url, timeout=config.timeout_seconds, max_bytes=config.max_response_bytes)


def _reply_text(data: object) -> str:
    choices = data.get("choices") if isinstance(data, dict) else None
    first = choices[0] if isinstance(choices, list) and choices else None
    message = first.get("message") if isinstance(first, dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str):
        raise _unexpected("La respuesta de chat no contiene choices[0].message.content.")
    return content


def _validate_system_stats(data: object) -> None:
    if not isinstance(data, dict):
        raise _unexpected("system_stats no devolvió un objeto.")
    if not isinstance(data.get("system"), dict) or not isinstance(data.get("devices"), list):
        raise _unexpected("system_stats no contiene 'system' y 'devices'.")


def _count(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _unexpected(message: str) -> TransportError:
    return TransportError(UNEXPECTED_RESPONSE, message)
