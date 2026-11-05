# T02: entrega para revisión (local-runtime-mvp)

**Implementador:** Claude (Anthropic), 23 de octubre de 2026, en `main` sobre `8f98514`. **Estado:** pendiente de revisión por un proveedor distinto (Codex/GPT). Sin casilla `[x]` ni commit hasta su dictamen.

## Alcance implementado

- `config/local.example.json` y `src/jasp_nexus/local_config.py`: JSON validado con claves cerradas. Límites: `timeout_seconds` de 0,1 a 300, `max_response_bytes` de 1024 a 16 MiB y `max_tokens` de 1 a 8192. Se aceptan URLs `http`/`https` hacia loopback (`127.0.0.0/8`, `::1`, `localhost`) o hacia una IP privada numérica declarada en `allowed_private_hosts`. Se rechazan credenciales, query, fragmento, hosts por nombre y puertos inválidos.
- `src/jasp_nexus/local_http.py`: `urllib` con `ProxyHandler({})`, que ignora proxies del entorno o del registro, y con redirecciones convertidas en error. La lectura está limitada por bytes, tanto por `Content-Length` como por flujo. El plazo total se comprueba entre bloques, por lo que el peor caso es el plazo más un timeout de socket. Los errores se clasifican en categorías estables y nunca se copia el cuerpo remoto.
- `src/jasp_nexus/local_services.py`:
  - LM Studio: `GET /v1/models` (`data[].id`) y `POST /v1/chat/completions` con `stream=false` y `max_tokens`, sin `tools`.
  - ComfyUI: `GET /system_stats`, cuyo objeto debe incluir `system` y `devices`. Una raíz que responde 200 no basta.
- `src/jasp_nexus/local_runs.py`: tablas nuevas `local_runs` y `local_run_events`, creadas de forma idempotente. No tienen columnas de prompt, respuesta, cuerpo, cabeceras ni URL. Una ejecución que quede en `running` se presenta como `no_confirmado`. El `task_id` es opcional, se valida y no altera `tasks/events`.
- `src/jasp_nexus/local_cli.py` y un enganche de 5 líneas en `cli.py`: opción global `--local-config` y comandos `providers`, `models`, `chat --model --prompt [--max-tokens] [--task-id]` y `runs [--limit]`. Códigos de salida: 0 éxito, 2 entrada o configuración inválida (incluido un modelo no anunciado, sin enviar la petición) y 3 servicio o transporte.
- `pyproject.toml`: configuración de ruff. Se excluyen los archivos heredados, incluido `cli.py`, cuya única modificación es el enganche.

## Decisiones para el revisor

1. **`runs`** no figura en R2.1. Se añadió porque el diseño exige mostrar como no confirmado lo que quedó en `running`, y para comprobar metadatos sin herramientas externas.
2. **`cli.py` queda fuera de ruff.** Normalizarlo supondría tocar código heredado (tipado, imports, formato), y AGENTS exige para eso alcance y revisión propios. Las líneas nuevas son las del diff.
3. **`chat`** registra primero una ejecución `models` para el descubrimiento y después la ejecución `chat`. Si el modelo no está anunciado, la ejecución `chat` queda `failed/model_not_announced` con `model_id` nulo.
4. **Pista para WSL:** ante un fallo de red hacia loopback en WSL, el error sugiere activar el modo de red mirrored o declarar la IP del host. No se ejecutan comandos para descubrirla.

## Verificación ejecutada

- WSL Ubuntu 24.04, Python 3.12.3: `PYTHONPATH=src python3 -m unittest discover -s tests -v` da 51 pruebas OK (15 foundation y 36 nuevas). `python3 -m jasp_nexus.cli --help` y `git diff --check` también pasan.
- ruff 0.14.0, instalado en un venv temporal fuera del repositorio: `ruff check .` y `ruff format --check .` pasan sobre los archivos no excluidos.
- Windows nativo, Python 3.13: las 36 pruebas nuevas pasan. Las 5 de `test_store.py` (foundation) fallan al borrar el directorio temporal porque `TaskStore` no cierra sus conexiones SQLite (WinError 32). Es deuda heredada, fuera de la matriz CI Linux/macOS, y no se corrige aquí.

## Aceptación real: no superada

El 23/24 de octubre de 2026 (UTC 03:54) se ejecutó `providers` y `models` con base temporal y `config/local.example.json`. LM Studio y ComfyUI respondieron `connection_refused` en `127.0.0.1:1234` y `127.0.0.1:8188`. Los metadatos `failed/connection_refused` quedaron registrados. No se inició ningún proveedor. Queda pendiente repetir providers → models → chat con LM Studio en marcha y un modelo anunciado.
