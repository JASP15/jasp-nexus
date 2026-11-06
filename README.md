# JASP Nexus

Orquestador personal multi-proveedor: reparte el trabajo de un objetivo común entre Claude Code, Codex y Kiro CLI, lanzados en modo headless desde una sola herramienta, con revisión cruzada entre empresas y aprobación humana. LM Studio es opcional. Se ejecuta en local (WSL2 como host principal, macOS secundario); la consola web escucha solo en `127.0.0.1`.

**Estado actual (6 de noviembre de 2026): fase F0.** La CLI administra tareas, simula asignaciones y habla con LM Studio contra un servidor de prueba; todavía **no ejecuta agentes** ni tiene consola. Los adaptadores headless, el pipeline y la consola son trabajo planificado.

## Dirección vigente

El 6 de noviembre de 2026 el usuario aprobó convertir Nexus en orquestador multi-proveedor ([decisión y procedencia](docs/decision-2026-11-06.md)): suscripciones primero, adaptadores directos por `subprocess` sin CAO ni tmux, consola Nuxt 4 después del flujo por CLI.

- Spec activa: [multi-provider-orchestrator](.kiro/specs/multi-provider-orchestrator/tasks.md) (21 tareas en seis fases, F0–F5). Resumen en el [roadmap](docs/ROADMAP.md).
- [local-runtime-mvp](.kiro/specs/local-runtime-mvp/tasks.md): **cerrada**. T01 aprobada por Claude en ronda 2; T02 cerrada con revisión interna por excepción del usuario, sin aceptación real contra LM Studio.
- [nexus-console](.kiro/specs/nexus-console/tasks.md): **reemplazada** por la fase F4; se conserva como referencia hasta F5.

## Qué hay disponible

| Componente | Estado |
|---|---|
| CLI `doctor/create/list/show/route/history/advance` | Funciona (base foundation) |
| SQLite `.nexus/state.sqlite3`, transiciones e historial | Funciona, compatible con `--db` |
| `route` con `config/agents.example.json` | Simulado: no comprueba binario, login ni cuota |
| `providers/models/chat/runs` (LM Studio/ComfyUI) | Probado contra servidor falso; aceptación real pendiente (F5/T19, opcional) |
| Pruebas unitarias y CI Linux/macOS | 54 pruebas unittest verificadas en WSL; CI solo unittest |
| Adaptadores Claude/Codex/Kiro, `nexus run`, `doctor` real | Pendiente (F1–F2) |
| Router por etapas, pipeline, aprobación humana | Pendiente (F3) |
| Consola web Nuxt | Pendiente (F4) |
| Perfiles CAO, `scripts/*.sh`, `config/routing.yaml` | Legado no validado; no ejecutar; se retira en F5 |

`route` produce un plan lógico y no consume créditos. `advance --actor` registra un actor declarado, sin autenticarlo. `doctor` hoy solo busca binarios y consulta `cao-server`; no acredita autenticación ni cuota.

## Probar la base sin instalar proveedores

Desde la raíz del checkout en WSL, con Python 3.11+ (3.12 recomendado):

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m jasp_nexus.cli --help
```

Ensayo manual con datos descartables:

```bash
PYTHONPATH=src python3 -m jasp_nexus.cli --db .build/demo/state.sqlite3 create --title "Prueba local" --kind general
PYTHONPATH=src python3 -m jasp_nexus.cli --db .build/demo/state.sqlite3 list
# Usa el ID mostrado; route sigue siendo una simulación.
PYTHONPATH=src python3 -m jasp_nexus.cli --db .build/demo/state.sqlite3 route ID_DE_TAREA
```

La instalación editable (`pip install -e .`) es opcional y da el comando `nexus`. La guía de entorno WSL con `uv`, ruff, Node y las tres CLIs llegará con F0/T02 (`docs/setup-wsl.md`).

## Guías

- [Reglas de agentes](AGENTS.md), [steering](.kiro/steering/) y [spec activa](.kiro/specs/multi-provider-orchestrator/requirements.md).
- [Roadmap](docs/ROADMAP.md) y [decisión del 6 de noviembre](docs/decision-2026-11-06.md).
- [Dictámenes de revisión](docs/revisiones/).

### Histórico

- [Revisión local del 23 de octubre](docs/revision-local-2026-10-23.md), [conciliación](docs/conciliacion-local-2026-10-23.md) y [consolidación de Git](docs/consolidacion-git-2026-10-23.md): procedencia de la base actual. Foundation `8683b6568ff026cb957866225115743b8b01d4f8` está incorporada en `main` mediante el merge `e120277`; `main` es la única rama local de trabajo y no se publica sin petición del usuario.
- Guías heredadas de la línea CAO, sin vigencia: [Windows](docs/setup-windows.md), [arquitectura](docs/ARCHITECTURE.md), [seguridad](docs/SECURITY.md), [WSL2](docs/WINDOWS_WSL2.md), [macOS](docs/MACOS.md) y [multi-host](docs/MULTI_HOST.md). Pasan a `docs/archivo/` en F5.

Nunca ejecutar los scripts CAO heredados ni paradas globales de agentes. Cada host conserva sus datos y credenciales; Git no sincroniza sesiones ni SQLite.
