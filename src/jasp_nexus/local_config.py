"""Validated configuration for local services (LM Studio, ComfyUI). No secrets."""

from __future__ import annotations

import ipaddress
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

DEFAULT_LM_STUDIO_URL = "http://127.0.0.1:1234/v1"
DEFAULT_COMFYUI_URL = "http://127.0.0.1:8188"

TIMEOUT_RANGE = (0.1, 300.0)
RESPONSE_BYTES_RANGE = (1024, 16 * 1024 * 1024)
MAX_TOKENS_RANGE = (1, 8192)

ALLOWED_KEYS = frozenset(
    {
        "lm_studio_url",
        "comfyui_url",
        "timeout_seconds",
        "max_response_bytes",
        "max_tokens",
        "allowed_private_hosts",
    }
)


class ConfigError(ValueError):
    """Invalid local configuration or URL (exit code 2)."""


@dataclass(frozen=True)
class LocalConfig:
    lm_studio_url: str = DEFAULT_LM_STUDIO_URL
    comfyui_url: str = DEFAULT_COMFYUI_URL
    timeout_seconds: float = 30.0
    max_response_bytes: int = 1024 * 1024
    max_tokens: int = 512
    allowed_private_hosts: frozenset[str] = field(default_factory=frozenset)


def load_local_config(path: str | Path | None) -> LocalConfig:
    """Load and validate the JSON file; without a path, use validated defaults."""
    if path is None:
        return validate_config({})
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"No existe el archivo de configuración local: {path}") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ConfigError(f"Configuración local ilegible o JSON inválido: {path}") from exc
    if not isinstance(data, dict):
        raise ConfigError("La configuración local debe ser un objeto JSON.")
    return validate_config(data)


def validate_config(data: dict[str, object]) -> LocalConfig:
    unknown = sorted(set(data) - ALLOWED_KEYS)
    if unknown:
        raise ConfigError(f"Claves de configuración desconocidas: {', '.join(unknown)}")
    defaults = LocalConfig()
    allowed = _private_hosts(data.get("allowed_private_hosts", []))
    config = LocalConfig(
        lm_studio_url=_text(data, "lm_studio_url", defaults.lm_studio_url),
        comfyui_url=_text(data, "comfyui_url", defaults.comfyui_url),
        timeout_seconds=_number(data, "timeout_seconds", defaults.timeout_seconds, TIMEOUT_RANGE),
        max_response_bytes=_integer(
            data, "max_response_bytes", defaults.max_response_bytes, RESPONSE_BYTES_RANGE
        ),
        max_tokens=_integer(data, "max_tokens", defaults.max_tokens, MAX_TOKENS_RANGE),
        allowed_private_hosts=allowed,
    )
    validate_service_url(config.lm_studio_url, allowed)
    validate_service_url(config.comfyui_url, allowed)
    return config


def validate_service_url(url: str, allowed_private_hosts: frozenset[str]) -> None:
    """Accept http(s) to loopback or an explicitly declared private numeric host."""
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError as exc:
        raise ConfigError(f"URL inválida: {url!r}") from exc
    if parts.scheme not in {"http", "https"}:
        raise ConfigError(f"La URL debe usar http o https: {url!r}")
    if parts.username is not None or parts.password is not None:
        raise ConfigError("La URL no puede contener credenciales.")
    if parts.query or parts.fragment or "?" in url or "#" in url:
        raise ConfigError("La URL no puede contener query ni fragmento.")
    if not parts.hostname:
        raise ConfigError(f"La URL no indica host: {url!r}")
    if port == 0:
        raise ConfigError(f"Puerto inválido en la URL: {url!r}")
    if not _host_allowed(parts.hostname, allowed_private_hosts):
        raise ConfigError(
            f"Host no permitido: {parts.hostname}. Use loopback o declare la IP privada "
            "del host WSL en allowed_private_hosts."
        )


def _host_allowed(host: str, allowed_private_hosts: frozenset[str]) -> bool:
    if host == "localhost":
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    if address.is_loopback:
        return True
    return address.is_private and str(address) in allowed_private_hosts


def _private_hosts(value: object) -> frozenset[str]:
    if not isinstance(value, list):
        raise ConfigError("allowed_private_hosts debe ser una lista de IP privadas numéricas.")
    hosts: set[str] = set()
    for item in value:
        try:
            address = ipaddress.ip_address(item) if isinstance(item, str) else None
        except ValueError:
            address = None
        if address is None or not address.is_private or address.is_loopback:
            raise ConfigError(f"Dirección privada numérica inválida: {item!r}")
        if address.is_unspecified or address.is_link_local or address.is_multicast:
            raise ConfigError(f"Dirección privada numérica inválida: {item!r}")
        hosts.add(str(address))
    return frozenset(hosts)


def _text(data: dict[str, object], key: str, default: str) -> str:
    value = data.get(key, default)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{key} debe ser un texto no vacío.")
    return value.strip().rstrip("/")


def _number(
    data: dict[str, object], key: str, default: float, bounds: tuple[float, float]
) -> float:
    value = data.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ConfigError(f"{key} debe ser numérico.")
    number = float(value)
    if not math.isfinite(number) or not bounds[0] <= number <= bounds[1]:
        raise ConfigError(f"{key} debe estar entre {bounds[0]} y {bounds[1]}.")
    return number


def _integer(data: dict[str, object], key: str, default: int, bounds: tuple[int, int]) -> int:
    value = data.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{key} debe ser un entero.")
    if not bounds[0] <= value <= bounds[1]:
        raise ConfigError(f"{key} debe estar entre {bounds[0]} y {bounds[1]}.")
    return value
