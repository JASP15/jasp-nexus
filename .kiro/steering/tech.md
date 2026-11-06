# Stack técnico y compatibilidad

Dirección del 6 de noviembre de 2026 ([decisión](../../docs/decision-2026-11-06.md)); spec activa `multi-provider-orchestrator`. No agregar dependencias de ejecución ni cambiar tecnologías fuera de lo que fija la tarea activa de esa spec.

## Base Python

- Python **3.11+** (3.12 en WSL), layout `src/`, paquete `jasp-nexus`, build **setuptools**.
- CLI **argparse**, entrypoint `nexus = "jasp_nexus.cli:main"`. Los comandos nuevos se añaden con módulos de despacho propios (patrón de `local_cli.py`), sin cambiar comandos, opciones ni comportamiento existentes.
- **Librería estándar, sin dependencias de ejecución**: `sqlite3`, `subprocess`, `threading`, `http.server`, `json`, `argparse`… `pip install -e .` sigue siendo la única instalación necesaria para ejecutar Nexus.
- Datos: `.nexus/state.sqlite3` (configurable con `--db`). Las tablas nuevas son aditivas e idempotentes; se preservan `tasks`, `events`, `local_runs`, `local_run_events`, sus estados y las APIs de `TaskStore` y `RunStore`.
- Configuración: `config/agents.example.json` (JSON, librería estándar), ampliado con claves aditivas en F3/T10. `config/routing.yaml` queda obsoleto: no hay parser YAML en stdlib; sus valores se migran al JSON en T10 y el archivo se elimina en F5.
- Pruebas: **unittest** (54 casos verificados en WSL). CI Linux/macOS con Python 3.11/3.12. Las pruebas no requieren credenciales, cuota ni CLIs reales: usan una CLI falsa (`tests/fake_cli.py`, F1) y servidores efímeros en loopback.

## Adaptadores de proveedores (`subprocess`)

- Cada CLI (`claude`, `codex`, `kiro-cli`) se invoca en modo headless con `subprocess.Popen` y **lista de argumentos**, nunca `shell=True`; prompt por stdin cuando la CLI lo admite; `start_new_session=True`; plazo total con reloj monotónico y terminación del grupo de procesos propio al vencer; stdout/stderr acotados por bytes.
- Entorno del hijo: lista blanca de **nombres** de variables (p. ej. `PATH`, `HOME`, `LANG`, `TERM`, `XDG_*`, `CLAUDE_CONFIG_DIR`, `CODEX_HOME`, `KIRO_API_KEY`). Nexus nunca lee, imprime ni guarda sus valores.
- Los argv, formatos de salida, ids de sesión y permisos de cada CLI son **supuestos** hasta capturarlos en F0/T03 (`docs/providers/*.md`, fixtures depurados en `tests/fixtures/providers/`). Versiones observadas en macOS el 6 de noviembre de 2026: `claude` 2.1.303, `codex` 0.163.0; Kiro CLI pendiente de instalar en WSL.
- Cuota: no existe API de cupo restante en headless. Solo se detectan señales en la salida y se aplica enfriamiento.
- LM Studio (opcional, F5) reutiliza `local_services` y `local_http` (T02 de `local-runtime-mvp`): loopback o host WSL declarado, sin proxies ni redirecciones.

## Backend de la consola: librería estándar

- `server.py` con `http.server.ThreadingHTTPServer` ligado solo a `127.0.0.1`, enrutado propio, JSON y **SSE** (`text/event-stream`) para la salida en vivo; comprobación de `Host` y `Origin`; límite de tamaño de cuerpo; errores `{"detail": "..."}` en español. Manejadores como funciones puras en `api/handlers.py`. API documentada a mano en `docs/api.md`.
- **FastAPI queda reservado**, no planificado: solo se reconsidera, en una tarea propia revisada, si la API supera ~20 rutas o necesita WebSocket, conservando `api/handlers.py`.

## Consola web (`web/`, F4)

Nuxt 4 en modo SPA (`ssr: false`), Vue 3, TypeScript `strict` sin `any`, Tailwind CSS, TanStack Query (`@tanstack/vue-query`), Vitest y ESLint; Node LTS y npm en WSL. Textos en español. `nuxi generate` produce el build que se copia a `src/jasp_nexus/static/` (ignorado por Git, incluido como package-data) y `server.py` lo sirve. En desarrollo, `nuxi dev --host 127.0.0.1` con proxy de `/api`. Si el repo vive en `/mnt/c`, `node_modules` puede ir lento: se recomienda clonar en el sistema de archivos de WSL.

## Herramientas de desarrollo (no de ejecución)

- **uv** y **ruff** (versión fijada en el extra `dev` de `pyproject.toml`, F0/T02). Ruff aplica a código nuevo o modificado; la base foundation sigue excluida hasta F5/T21.
- Node LTS + npm solo para `web/`.

## Verificar

Base de toda tarea, desde la raíz en WSL:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m jasp_nexus.cli --help
uv run ruff check . && uv run ruff format --check .
git diff --check
```

La línea de ruff se exige desde que F0/T02 deje `uv` y ruff instalados en WSL; antes se anota como no ejecutada. Cada tarea añade sus comandos propios en `tasks.md`. Un comando que no se ejecutó, o que no puede correr en el host (p. ej. macOS con Python 3.9), se registra así; nunca se declara verde.

## Retirado

CAO (`cao-server`, `http://127.0.0.1:9889`), tmux, perfiles `profiles/nexus_*.md`, `scripts/*.sh`, `config/routing.yaml`, el stack reservado de la consola anterior (FastAPI + uvicorn, httpx, pydantic, ruamel.yaml, React + Vite) y `docs/cao/contract.md` como referencia. Los archivos que existen se conservan sin ejecutar hasta F5/T20; la comprobación de `cao-server` en `doctor` es deuda heredada que sustituye `doctor.py` (F2/T09) y se retira en F5.
