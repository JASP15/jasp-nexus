# Estructura del repositorio

Spec activa: `multi-provider-orchestrator` (dirección del 6 de noviembre de 2026).

## Existente

```text
AGENTS.md                          Reglas para agentes y spec activa
.kiro/steering/                    Producto, stack y estructura vigentes
.kiro/specs/multi-provider-orchestrator/  Spec activa
.kiro/specs/local-runtime-mvp/     Spec CERRADA el 6 de noviembre de 2026
.kiro/specs/nexus-console/         Spec REEMPLAZADA por F4; se archiva en F5
pyproject.toml                     Setuptools; entrypoint jasp_nexus.cli:main; ruff con exclusiones foundation
src/jasp_nexus/
  __init__.py                      Versión 0.1.0
  cli.py                           argparse: doctor/create/list/show/route/history/advance + despacho a local_cli
  core.py                          Catálogo JSON (load_agents) y routing simulado (route)
  platform_support.py              Detección de host
  store.py                         TaskStore: tablas tasks/events y transiciones
  local_config.py                  LocalConfig y validación de URLs locales
  local_http.py                    Transporte HTTP con plazo total, sin proxies ni redirecciones
  local_services.py                list_models, chat, run_probe, Usage (LM Studio/ComfyUI)
  local_runs.py                    RunStore: tablas aditivas local_runs/local_run_events
  local_cli.py                     Comandos providers/models/chat/runs
tests/                             54 pruebas unittest; local_fakes.py (servidor HTTP falso)
.github/workflows/ci.yml           CI Linux/macOS, Python 3.11/3.12, solo unittest
config/agents.example.json         Catálogo de agentes del router (se amplía en F3/T10)
config/local.example.json          Configuración de LM Studio/ComfyUI sin secretos
docs/                              Decisiones, roadmap, revisiones y guías
docs/revisiones/                   Dictámenes de revisión cruzada por tarea
```

### Legado CAO conservado sin ejecutar (se retira en F5/T20)

```text
config/routing.yaml                Política de perfiles CAO; se migra a agents.example.json en T10 y se elimina
profiles/nexus_*.md                Ocho perfiles CAO
scripts/{start,stop,install-profiles,setup-wsl}.sh   Scripts CAO no validados; stop.sh hace una parada global prohibida
docs/{ARCHITECTURE,SECURITY,MULTI_HOST,MACOS,WINDOWS_WSL2,setup-windows}.md   Guías históricas; pasan a docs/archivo/
```

## Previsto por la spec activa

Rutas planificadas, no archivos existentes:

```text
src/jasp_nexus/
  providers/__init__.py            Registro de adaptadores
  providers/base.py                RunRequest, RunResult, ProviderStatus, Command, Adapter (F1/T04)
  providers/process.py             Runner de procesos: Popen con lista de args, plazo, env por lista blanca (F1/T04)
  providers/claude.py              Adaptador Claude Code (F1/T05)
  providers/codex.py               Adaptador Codex (F2/T07)
  providers/kiro.py                Adaptador Kiro CLI (F2/T08)
  providers/lm_studio.py           Adaptador LM Studio opcional (F5/T19)
  provider_runs.py                 Tablas aditivas provider_runs/provider_run_events/provider_state (F1/T04)
  run_cli.py                       Comando nexus run (F1/T06)
  doctor.py                        doctor real por proveedor (F2/T09)
  router.py                        Asignación por etapa con revisor de otra empresa (F3/T10)
  pipeline.py                      Etapas spec → implement → review → aprobación (F3/T11)
  artifacts.py                     .nexus/tasks/<id>/ (F3/T11)
  prompts.py                       Plantillas de etapa en español (F3/T11)
  workspace.py                     Árbol limpio, worktrees, diff y política de rutas (F3/T12)
  server.py                        Backend HTTP stdlib en 127.0.0.1 (F4/T14)
  api/handlers.py, api/sse.py      Manejadores puros y SSE (F4/T14)
  static/                          Build de web/ (ignorado por Git)
tests/fake_cli.py                  CLI falsa para pruebas de adaptadores y pipeline
tests/fixtures/providers/          Salidas reales depuradas de cada CLI (F0/T03)
docs/providers/                    Contrato headless observado por CLI (F0/T03)
docs/api.md, docs/console.md       API y pantallas de la consola (F4)
docs/setup-wsl.md                  Entorno de desarrollo WSL (F0/T02)
docs/archivo/                      Documentos y specs retirados con nota de procedencia (F5/T20)
web/                               Consola Nuxt 4 SPA (F4/T15)
scripts/build-web.sh               Único script nuevo: build de web/ hacia static/ (F4/T15)
```

## Datos

- `.nexus/state.sqlite3` relativo al directorio de ejecución, salvo `--db`. Tablas existentes: `tasks`, `events`, `local_runs`, `local_run_events`. Tablas previstas, aditivas y sin columnas de contenido: `provider_runs`, `provider_run_events`, `provider_state`, `task_steps`, `approvals`.
- `.nexus/tasks/<id>/`: artefactos de cada tarea (`brief.md`, `plan.md`, `summary.md`, `diff.patch`, `files.txt`, `review.md`; `raw/<run_id>.jsonl` solo con `--keep-raw`). Son entregables del usuario; `.nexus/` está ignorado por Git y `nexus clean <id>` los borra.
- `~/.jasp-nexus/` no se usa; no hay segunda base canónica.

## Convenciones

- Un módulo pequeño por responsabilidad; la CLI y los manejadores HTTP solo parsean, delegan y presentan.
- Adaptadores: un archivo por proveedor que implementa `Adapter` (`probe`, `build_command`, `parse`); sin lógica de proceso propia, que vive en `providers/process.py`.
- Consola: componentes Vue funcionales en PascalCase, un componente por archivo, cliente `api/` tipado con los tipos de `docs/api.md`, textos en español.
