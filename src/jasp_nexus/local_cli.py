"""CLI commands for local services: providers, models, chat and runs."""

from __future__ import annotations

import argparse
import ipaddress
import json
import sys
from collections.abc import Callable
from urllib.parse import urlsplit

from .local_config import ConfigError, LocalConfig, load_local_config
from .local_http import (
    CONNECTION_ERROR,
    CONNECTION_REFUSED,
    TIMEOUT,
    TransportError,
    request_json,
)
from .local_runs import RunOutcome, RunStore
from .local_services import (
    LM_STUDIO,
    PROBES,
    ModelNotAnnouncedError,
    Requester,
    Usage,
    chat,
    list_models,
    models_url,
    probe_url,
    require_announced,
    run_probe,
)
from .platform_support import current_host
from .store import TaskStore

EXIT_OK = 0
EXIT_INVALID = 2
EXIT_SERVICE = 3

LOCAL_COMMANDS = frozenset({"providers", "models", "chat", "runs"})
NETWORK_FAILURES = frozenset({CONNECTION_REFUSED, CONNECTION_ERROR, TIMEOUT})
MODEL_NOT_ANNOUNCED = "model_not_announced"


def add_local_commands(commands: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    commands.add_parser("providers", help="Comprueba LM Studio y ComfyUI (solo lectura)")
    commands.add_parser("models", help="Lista los IDs de modelos que anuncia LM Studio")
    chat_parser = commands.add_parser("chat", help="Una petición de chat no streaming")
    chat_parser.add_argument("--model", required=True, help="ID exacto de `nexus models`")
    chat_parser.add_argument("--prompt", required=True)
    chat_parser.add_argument("--max-tokens", type=int, default=None)
    chat_parser.add_argument("--task-id", default=None, help="Vincula a una tarea existente")
    runs_parser = commands.add_parser("runs", help="Metadatos de ejecuciones locales")
    runs_parser.add_argument("--limit", type=int, default=20)


def run_local_command(args: argparse.Namespace, requester: Requester = request_json) -> int:
    try:
        config = load_local_config(args.local_config)
        TaskStore(args.db)
        runs = RunStore(args.db)
        handler = _HANDLERS[args.command]
        return handler(args, config, runs, requester)
    except (ConfigError, ModelNotAnnouncedError, ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_INVALID


def _providers(
    args: argparse.Namespace, config: LocalConfig, runs: RunStore, requester: Requester
) -> int:
    failed = False
    for probe in PROBES:
        url = probe_url(probe, config)
        handle = runs.start(probe.service, "probe")
        try:
            status = run_probe(probe, config, requester)
        except TransportError as exc:
            failed = True
            ms = runs.finish(handle, _failure(exc))
            print(f"{probe.service:10} {probe.check:18} FALLO {exc.category} ({ms} ms) {url}")
            print(f"{'':10} {exc}{_hint(exc, url)}")
            continue
        ms = runs.finish(handle, RunOutcome("succeeded", http_status=status))
        print(f"{probe.service:10} {probe.check:18} OK HTTP {status} ({ms} ms) {url}")
    print("Una respuesta correcta no demuestra modelos cargados, autenticación, cuota ni calidad.")
    return EXIT_SERVICE if failed else EXIT_OK


def _models(
    args: argparse.Namespace, config: LocalConfig, runs: RunStore, requester: Requester
) -> int:
    announced = _discover(config, runs, requester, None)
    if announced is None:
        return EXIT_SERVICE
    if not announced:
        print("LM Studio respondió con una lista vacía: no anuncia ningún modelo.")
        return EXIT_OK
    for model_id in announced:
        print(model_id)
    print(
        "Aparecer en la lista no demuestra que el modelo esté cargado (puede cargarse bajo "
        "demanda).",
        file=sys.stderr,
    )
    return EXIT_OK


def _chat(
    args: argparse.Namespace, config: LocalConfig, runs: RunStore, requester: Requester
) -> int:
    max_tokens = _chat_max_tokens(args.max_tokens, config)
    if not args.prompt.strip():
        raise ValueError("La petición (--prompt) no puede estar vacía.")
    announced = _discover(config, runs, requester, args.task_id)
    if announced is None:
        return EXIT_SERVICE
    try:
        require_announced(args.model, announced)
    except ModelNotAnnouncedError:
        handle = runs.start(LM_STUDIO, "chat", task_id=args.task_id)
        runs.finish(handle, RunOutcome("failed", MODEL_NOT_ANNOUNCED))
        raise
    handle = runs.start(LM_STUDIO, "chat", model_id=args.model, task_id=args.task_id)
    try:
        reply = chat(config, args.model, args.prompt, max_tokens, requester)
    except TransportError as exc:
        ms = runs.finish(handle, _failure(exc))
        print(f"error: chat fallido: {exc.category} ({ms} ms). {exc}", file=sys.stderr)
        return EXIT_SERVICE
    outcome = RunOutcome("succeeded", http_status=reply.http_status, usage=reply.usage)
    ms = runs.finish(handle, outcome)
    print(reply.text)
    print(f"ejecución {handle.run_id}: {ms} ms; {_usage_text(reply.usage)}", file=sys.stderr)
    return EXIT_OK


def _runs(
    args: argparse.Namespace, config: LocalConfig, runs: RunStore, requester: Requester
) -> int:
    if not 1 <= args.limit <= 1000:
        raise ValueError("--limit debe estar entre 1 y 1000.")
    print(json.dumps(runs.list(args.limit), indent=2, ensure_ascii=False))
    return EXIT_OK


def _discover(
    config: LocalConfig, runs: RunStore, requester: Requester, task_id: str | None
) -> list[str] | None:
    """Record a 'models' run; return the IDs, or None after reporting a failure."""
    handle = runs.start(LM_STUDIO, "models", task_id=task_id)
    try:
        announced, status = list_models(config, requester)
    except TransportError as exc:
        ms = runs.finish(handle, _failure(exc))
        url = models_url(config)
        print(f"error: LM Studio {exc.category} ({ms} ms) en {url}. {exc}", file=sys.stderr)
        hint = _hint(exc, url)
        if hint:
            print(hint.strip(), file=sys.stderr)
        return None
    runs.finish(handle, RunOutcome("succeeded", http_status=status))
    return announced


def _chat_max_tokens(requested: int | None, config: LocalConfig) -> int:
    if requested is None:
        return config.max_tokens
    if not 1 <= requested <= config.max_tokens:
        raise ValueError(f"--max-tokens debe estar entre 1 y {config.max_tokens}.")
    return requested


def _failure(exc: TransportError) -> RunOutcome:
    return RunOutcome("failed", exc.category, exc.http_status)


def _usage_text(usage: Usage) -> str:
    if usage.total_tokens is None and usage.completion_tokens is None:
        return "consumo de tokens: desconocido"
    return (
        f"tokens: entrada={_unknown(usage.prompt_tokens)}, "
        f"salida={_unknown(usage.completion_tokens)}, total={_unknown(usage.total_tokens)}"
    )


def _unknown(value: int | None) -> str:
    return "desconocido" if value is None else str(value)


def _hint(exc: TransportError, url: str) -> str:
    if exc.category not in NETWORK_FAILURES or not _is_loopback(url):
        return ""
    if not current_host()[0].startswith("Windows + WSL"):
        return f" Compruebe que el servicio está iniciado y escucha en {url}."
    return (
        " Desde WSL, 127.0.0.1 puede no alcanzar servicios de Windows: active el modo de red "
        "mirrored o declare la IP privada del host en allowed_private_hosts y en la URL."
    )


def _is_loopback(url: str) -> bool:
    host = urlsplit(url).hostname or ""
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


_Handler = Callable[[argparse.Namespace, LocalConfig, RunStore, Requester], int]
_HANDLERS: dict[str, _Handler] = {
    "providers": _providers,
    "models": _models,
    "chat": _chat,
    "runs": _runs,
}
