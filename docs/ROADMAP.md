# Roadmap de JASP Nexus

Dirección aprobada por el usuario el 6 de noviembre de 2026 ([decisión](decision-2026-11-06.md)): orquestador personal multi-proveedor con Claude Code, Codex y Kiro CLI lanzados en headless por `subprocess`, sin CAO ni tmux. La fuente ejecutable es [.kiro/specs/multi-provider-orchestrator/tasks.md](../.kiro/specs/multi-provider-orchestrator/tasks.md); este documento no marca tareas por sí mismo.

## Fases

| Fase | Tareas | Objetivo | Hecho cuando |
|---|---|---|---|
| **F0. Redirección y entorno WSL** | T01–T03 | Fuentes de verdad redirigidas; entorno WSL con `uv`, ruff, Node y las tres CLIs con sesión iniciada; contratos headless capturados con fixtures reales | Spec activa aprobada; `nexus doctor` ve los tres binarios; `docs/providers/*.md` con evidencia |
| **F1. Adaptador Claude** | T04–T06 | Contrato común de adaptadores, runner de procesos seguro, métricas aditivas y `nexus run --provider claude` | Aceptación real en un repo descartable: archivo creado, diff, tokens y `--resume` |
| **F2. Adaptadores Codex y Kiro** | T07–T09 | Adaptadores Codex y Kiro; `doctor` completo con estados y enfriamiento por cuota observada | Aceptación real de cada CLI; `doctor` con las tres filas reales |
| **F3. Router, pipeline y revisión cruzada** | T10–T13 | Asignación por etapa con revisor de otra empresa, pipeline spec → implement → review → aprobación humana, artefactos en `.nexus/tasks/`, protección del repo objetivo | Una tarea real aprobada de punta a punta con las tres CLI (Claude en `spec`, Kiro en `implement`, Codex en `review`), proveedores efectivos de empresas distintas en implementación y revisión, y aprobación humana registrada |
| **F4. Consola local** | T14–T18 | Backend HTTP stdlib en `127.0.0.1` con SSE; consola Nuxt 4 con panel, nueva tarea, seguimiento en vivo, historial, política y doctor | Flujo de F3 operable desde el navegador; nada escucha fuera de `127.0.0.1` |
| **F5. LM Studio opcional y limpieza** | T19–T21 | Adaptador LM Studio (incluye la aceptación real pendiente de T02 de `local-runtime-mvp`, si el servicio está disponible); retirada del legado CAO; normalización del código heredado | Sin referencias vigentes a CAO; ruff sin exclusiones; pruebas foundation intactas |

Reglas comunes: una tarea a la vez, en orden; casilla y commit solo tras dictamen APROBADO de un revisor de otra empresa que la del modelo implementador; sin push.

## Estado de partida (6 de noviembre de 2026)

`main` en `b6de266`. CLI de tareas con routing simulado, `TaskStore` en SQLite y conexión local a LM Studio/ComfyUI probada contra un servidor falso (54 pruebas unittest en WSL). No hay adaptadores headless, ejecución real de agentes, cuota observada ni consola. Detalle en [product.md](../.kiro/steering/product.md).

Se mantiene la portabilidad WSL2 (principal) y macOS (secundario). Handoff, control remoto, leasing y sincronización de SQLite entre hosts siguen fuera de alcance.

## Histórico: dirección del 23 de octubre de 2026

Autorizada mediante la [revisión local](revision-local-2026-10-23.md) («sigamos tu propuesta») y sustituida el 6 de noviembre de 2026. Su spec ejecutable fue [local-runtime-mvp](../.kiro/specs/local-runtime-mvp/tasks.md), hoy cerrada.

1. **T01 — Conciliación y compatibilidad.** Cerrada con APROBADO de Claude en ronda 2.
2. **T02 — Conexión local real.** Cerrada con revisión interna por excepción aceptada por el usuario; aceptación real contra LM Studio y ruff no superadas (la aceptación real pasa a F5/T19, opcional).
3. **H3 — Agente acotado (OpenCode + LM Studio).** Sustituido por F1–F3: los agentes son las CLIs de suscripción y la protección del repo objetivo pasa a T12.
4. **H4 — ComfyUI.** Fuera del alcance de la spec activa; no cancelado.
5. **H5 — Orquestación y consola con CAO.** Sustituido por F3–F4 sin CAO; la spec `nexus-console` queda reemplazada por F4.

Ese orden, a su vez, había sustituido el piloto CAO del roadmap foundation (`8683b65`).
