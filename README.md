# JASP Nexus

Herramienta personal y modular para coordinar desarrollo y generación visual con servicios locales y agentes. El primer objetivo es un flujo local que no dependa de Claude ni de CAO.

**Estado actual: foundation y trabajo local consolidados en `main`, base `e120277`; T01 aprobada por Claude en ronda 2.** La CLI administra tareas y simula asignaciones; todavía no ejecuta agentes, chat local ni workflows ComfyUI. La consola web está pospuesta.

## Dirección acordada

El 23 de octubre de 2026 se aprobó seguir la [propuesta de revisión local](docs/revision-local-2026-10-23.md): **conexión local real → agente acotado → ComfyUI → orquestación y consola**.

La spec activa es [local-runtime-mvp](.kiro/specs/local-runtime-mvp/tasks.md). Se trabaja una tarea a la vez; T01 concilió las fuentes de verdad y recuperó el código existente, ya consolidado. Su cierre cuenta con [revisión de Claude](docs/revisiones/local-runtime-mvp-t01.md), proveedor distinto del implementador Codex. T02 permanece pendiente.

## Qué hay disponible

| Componente | Estado |
|---|---|
| CLI `doctor/create/list/show/route/history/advance` | Recuperada de foundation |
| SQLite `.nexus/state.sqlite3`, transiciones e historial | Recuperada, compatible con `--db` |
| Catálogo `config/agents.example.json` | Routing simulado; no comprueba login, cuota o salud |
| Pruebas unitarias y CI Linux/macOS | 15 tests de foundation; CI recuperado, sin nueva ejecución remota |
| Perfiles CAO, scripts y `config/routing.yaml` | Trabajo local conservado; integración pendiente |
| Conexión LM Studio y modelos/chat reales | T02 pendiente |
| Agente local acotado y ComfyUI | Hitos posteriores |
| Contrato CAO y consola | Pendientes y pospuestos |

`route` produce un plan lógico y no consume créditos. `advance --actor` registra un actor declarado, sin autenticarlo. No confundir ese registro con revisión de seguridad.

## Probar la base sin instalar proveedores

Desde la raíz del checkout en WSL/POSIX, con Python 3.11+:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m jasp_nexus.cli --help
```

Para un ensayo manual con datos descartables:

```bash
PYTHONPATH=src python3 -m jasp_nexus.cli --db .build/demo/state.sqlite3 create --title "Prueba local" --kind general
PYTHONPATH=src python3 -m jasp_nexus.cli --db .build/demo/state.sqlite3 list
# Usa el ID mostrado; route sigue siendo una simulación.
PYTHONPATH=src python3 -m jasp_nexus.cli --db .build/demo/state.sqlite3 route ID_DE_TAREA
```

La instalación editable del paquete es opcional para disponer del comando `nexus`; no se realizó como parte de la conciliación. `doctor` solo comprueba binarios y salud de CAO; no acredita autenticación ni cuota.

## Procedencia y archivos locales

La base procede de `8683b6568ff026cb957866225115743b8b01d4f8`, rama `feat/foundation-cao-mvp`. Primero se recuperaron sus archivos y después, por petición expresa del usuario, se fusionaron sus 13 commits con el trabajo local en `e120277e7930b77766f81201fa08cac6b79be1fd`. **La única rama local de trabajo es `main`**. El commit de cierre de T01 registra las correcciones documentales revisadas y el APROBADO externo de ronda 2; los commits de conservación y fusión no equivalen a esa aprobación. Los cambios siguen locales, sin publicar en GitHub.

Consulta [procedencia, compatibilidad y verificación](docs/conciliacion-local-2026-10-23.md). Los originales seguros y manifiesto están en `.build/reconcile-2026-10-23/`, ignorado por Git.

La [consolidación de ramas](docs/consolidacion-git-2026-10-23.md) explica el respaldo y la diferencia entre ramas locales y referencias remotas. Continuar en `main`; no cambiar a foundation para recuperar archivos, porque ya está incorporada.

## Guías

- [Reglas de agentes](AGENTS.md), [steering](.kiro/steering/) y [plan activo](.kiro/specs/local-runtime-mvp/tasks.md).
- [Roadmap vigente](docs/ROADMAP.md).
- [Diseño de consola pospuesto](.kiro/specs/nexus-console/design.md).
- [Guía local de Windows y estado de scripts CAO](docs/setup-windows.md).
- Documentación heredada: [arquitectura](docs/ARCHITECTURE.md), [seguridad](docs/SECURITY.md), [WSL2](docs/WINDOWS_WSL2.md), [macOS](docs/MACOS.md) y [multi-host](docs/MULTI_HOST.md). Se conserva como referencia; no activa esas instalaciones ni sustituye la spec vigente.

Nexus mantiene CAO como software externo, sin fork. Nunca exponer sus terminales a la red ni ejecutar paradas globales. Cada host conserva sus datos y credenciales; Git no sincroniza sesiones ni SQLite.
