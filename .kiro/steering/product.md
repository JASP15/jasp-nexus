# Producto: JASP Nexus

JASP Nexus es el **orquestador personal multi-proveedor** del usuario: una sola herramienta que reparte el trabajo de un objetivo común entre sus suscripciones de agentes de código (Claude Code, Codex y Kiro CLI) sin saltar entre aplicaciones. Cada CLI se lanza en modo headless como proceso propio; Nexus decide quién hace cada etapa, pasa el contexto entre etapas mediante artefactos en disco y exige revisión de otra empresa antes de pedir la aprobación humana.

## Dirección vigente: 6 de noviembre de 2026

El usuario aprobó el plan del orquestador multi-proveedor el 6 de noviembre de 2026 ([decisión y procedencia](../../docs/decision-2026-11-06.md)). La spec activa es `multi-provider-orchestrator`. Cuatro decisiones la definen:

1. **Suscripciones primero.** Claude Code, Codex y Kiro CLI son trabajadores de primera clase. LM Studio es opcional (F5). ComfyUI queda fuera del alcance de esta spec.
2. **Adaptadores directos.** Cada CLI se invoca por `subprocess` con lista de argumentos, sin CAO, tmux ni perfiles intermedios.
3. **Consola web local después del flujo por CLI.** Nuxt 4 (SPA) con backend Python en `127.0.0.1`; antes se completa y acepta el flujo por terminal.
4. **WSL2 como host principal**, macOS como secundario.

Orden: **F0 redirección y entorno → F1 adaptador Claude → F2 adaptadores Codex y Kiro → F3 router, pipeline y revisión cruzada → F4 consola → F5 LM Studio opcional y retirada del legado CAO.** Detalle en [ROADMAP](../../docs/ROADMAP.md).

La dirección del 23 de octubre de 2026 (conexión local real → agente acotado → ComfyUI → orquestación y consola, con CAO como motor externo) es histórica.

## Usuario y entornos

Un desarrollador que habla español y tiene suscripciones a Claude, ChatGPT/Codex y Kiro. Entorno principal: Windows 11 con WSL2 (Ubuntu 24.04, Python 3.12) y proyectos en `C:\laragon\www` (`/mnt/c/laragon/www`) o en el sistema de archivos de WSL. macOS es secundario: sirve para editar y consultar las CLIs; su Python actual (3.9) no ejecuta la suite. Cada host mantiene sus datos, autenticación y sesiones; no hay continuidad multi-host.

## Flujo de una tarea (objetivo)

1. El usuario crea una tarea con un brief, el repositorio objetivo y las rutas permitidas.
2. El router elige, según disponibilidad observada y preferencias por etapa, quién escribe el plan (`spec`), quién implementa y quién revisa; el revisor es de otra empresa que el implementador.
3. El implementador trabaja en el repositorio objetivo (opcionalmente en un worktree); Nexus captura `diff.patch` y la lista de archivos.
4. El revisor emite dictamen APROBADO o CAMBIOS; con CAMBIOS se reintenta hasta el límite de intentos.
5. Con APROBADO, el usuario confirma o rechaza (`nexus approve` / `nexus reject`). Ningún mensaje de un modelo acredita por sí solo finalización ni aprobación.

## Estado observable

- **Real y probado** (54 pruebas unittest en WSL): CLI `doctor/create/list/show/route/history/advance`; `TaskStore` con tareas, eventos y transiciones en SQLite; conexión local `providers/models/chat/runs` con transporte sin proxies ni redirecciones y tablas aditivas `local_runs`/`local_run_events`, probada contra un servidor falso.
- **Simulado:** `route` elige agentes desde `config/agents.example.json` sin comprobar binario, login ni cuota. `doctor` solo busca binarios y consulta `cao-server`. `--actor` no autentica.
- **No validado nunca:** aceptación real contra LM Studio; ruff en WSL; perfiles CAO, scripts y `config/routing.yaml` (legado que se retira en F5).
- **Pendiente** (spec activa): adaptadores headless, `nexus run`, `doctor` real, router por etapas, pipeline con artefactos y aprobación humana, protección del repositorio objetivo, consola Nuxt y adaptador LM Studio.

## Principios y límites

- Local: todo servidor propio escucha solo en `127.0.0.1`. Sin PTY ni entrada de teclado remota hacia los agentes.
- La política determinista decide asignación, límites y revisor. La cuota solo se **observa** (señales en la salida); nunca se muestra como «restante».
- SQLite y los logs no guardan prompts ni respuestas; los artefactos de tarea en `.nexus/tasks/` son entregables del usuario y se borran con `nexus clean`.
- Español en documentación, interfaz y mensajes nuevos; identificadores de código en inglés.
- Sin multiusuario, login propio, despliegue público, aplicación Electron/Tauri ni sincronización de SQLite entre hosts.
- La aprobación humana del resultado de una tarea del producto y la revisión cruzada de las tareas de construcción de este repositorio son controles distintos; ninguno sustituye al otro.
