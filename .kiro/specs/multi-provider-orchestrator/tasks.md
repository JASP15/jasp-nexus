# Tareas: JASP Nexus Multi-Provider Orchestrator

**Plan activo desde el 6 de noviembre de 2026** ([decisión](../../../docs/decision-2026-11-06.md)). Requisitos en [requirements.md](requirements.md); diseño en [design.md](design.md). Los números `T<nn>` de este documento pertenecen solo a esta spec; los dictámenes se guardan como `docs/revisiones/mpo-t<nn>-*.md`.

## Reglas

- Una tarea a la vez, **en orden**. Una tarea empieza cuando la anterior está marcada `[x]`.
- La casilla `[x]` y el commit `T<nn>: <título>` (cuerpo `spec: multi-provider-orchestrator`) se hacen solo tras dictamen **APROBADO** de un revisor cuyo proveedor efectivo sea de otra empresa que el del modelo implementador (R9.4). El dictamen registra ambos proveedores efectivos. Sin push; sin crear ramas.
- «Implementa / Revisa» es la asignación prevista. Si el implementador cambia (por cuota u otra causa), el revisor se vuelve a elegir según el proveedor efectivo real; si no hay revisor de otra empresa, la tarea queda pendiente.
- Código nuevo: tipado completo, ruff limpio, mensajes en español, `subprocess` con lista de argumentos (R9.3, R1.2).
- Si una tarea es imposible tal como está escrita, no se improvisa: se reporta el bloqueo con una propuesta.

**Verificación base** de toda tarea, desde la raíz en WSL:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m jasp_nexus.cli --help
uv run ruff check . && uv run ruff format --check .
git diff --check
```

La línea de ruff se exige desde que T02 deje `uv` y ruff instalados en WSL. Un comando no ejecutado se anota como tal; nunca se declara verde.

---

## F0. Redirección documental y entorno WSL

- [x] **T01. Redirección documental** (R9.4, R9.6, R3.2) — implementa: Claude (Anthropic); revisa: Codex (OpenAI)
  - Archivos: `AGENTS.md`, `.kiro/steering/{product,tech,structure}.md`, `docs/ROADMAP.md`, `README.md`, `docs/decision-2026-11-06.md`; cabeceras de `.kiro/specs/local-runtime-mvp/*.md` («CERRADA») y `.kiro/specs/nexus-console/*.md` («REEMPLAZADA»); cabeceras de las guías heredadas (`docs/{ARCHITECTURE,SECURITY,WINDOWS_WSL2,MACOS,MULTI_HOST,setup-windows}.md`); esta spec (`requirements.md`, `design.md`, `tasks.md`); dictámenes `docs/revisiones/mpo-t01-codex-ronda-<n>.md`.
  - Solo documentación: sin cambios de código, pruebas ni configuración.
  - Verificar: `git diff --check`; comprobación de enlaces relativos rotos en los `.md` tocados (script de un uso en `.build/`); `git status` muestra solo archivos `.md`. La suite unittest no aplica a un cambio solo documental y no corre en macOS con Python 3.9: se anota.
  - Aceptación: ningún documento vigente afirma que CAO, `routing.yaml` o la consola FastAPI son el plan; esta spec es la activa; la contradicción con la dirección del 23 de octubre y su procedencia están registradas; dictamen APROBADO de Codex en `docs/revisiones/mpo-t01-codex-ronda-<n>.md`.

- [ ] **T02. Entorno de desarrollo WSL** (R9.2, R9.3) — Claude escribe la guía y los cambios de `pyproject.toml`/CI; el usuario ejecuta instalaciones y logins en WSL; revisa: Codex
  - `docs/setup-wsl.md` (sustituye a `docs/setup-windows.md` y `docs/WINDOWS_WSL2.md`): Python 3.12, `uv`, `uv tool install ruff`, Node LTS, `claude` (`claude auth login`), `codex login`, Kiro CLI y su login (navegador o `KIRO_API_KEY`), con los comandos de instalación oficiales de cada herramienta. Recomendar clonar en el sistema de archivos de WSL (S12).
  - `pyproject.toml`: `[project.optional-dependencies] dev = ["ruff==<versión fijada>"]`. `.github/workflows/ci.yml`: job `lint` con ruff sobre los archivos no excluidos, sin tocar el job existente.
  - Ajustes derivados (precisión de T02): `[tool.ruff.format] exclude = ["*.md"]`, porque ruff 0.17 también formatea bloques de código en Markdown y los de la documentación son ilustrativos; `uv.lock` en `.gitignore`, porque `uv run` lo genera y Nexus no tiene dependencias de ejecución.
  - Ningún agente instala ni inicia sesión por su cuenta: el usuario ejecuta los pasos y comparte la salida que decida.
  - Verificar: `nexus doctor` muestra los tres binarios; `claude auth status`, `codex login status` y el equivalente de Kiro reportan sesión iniciada; verificación base completa, incluida ruff.
  - Aceptación: `docs/entorno-2026-11.md` registra las versiones reales observadas, sin tokens ni rutas de credenciales.

- [ ] **T03. Captura de contratos headless** (R1.3, R1.7, R1.8, R1.9, R9.5) — implementa: Claude con el usuario; revisa: Codex
  - En un directorio descartable de WSL, una ejecución mínima por CLI («crea `hola.txt` con la palabra hola»), capturando stdout, stderr y código de salida con `--output-format json` y `stream-json` (Claude), `--json -o` (Codex) y texto (Kiro).
  - Fixtures **depurados** (sin ids de cuenta ni rutas de usuario) en `tests/fixtures/providers/{claude,codex,kiro}/*.json|txt`. Documentar en `docs/providers/{claude,codex,kiro}.md`: argv exacto, campos de salida, obtención y reanudación de sesión, permisos denegados, salida ante timeout y ante falta de login, y modelo anunciado por Kiro (S4).
  - Verificar: `python3 -m json.tool` sobre cada fixture JSON; revisión manual de que no contienen secretos.
  - Aceptación: los supuestos S1–S4 de `design.md` (equivalentes a los riesgos R1–R4 del plan) quedan confirmados o anotados como «no soportado» con evidencia; consumo de cuota registrado. Lo observado sobre S5–S7 y S9 se anota como evidencia para T04–T09, sin condicionar el cierre.

## F1. Adaptador Claude headless

- [ ] **T04. Contrato de adaptadores y runner de procesos** (R1.1–R1.6, R2.2–R2.4, R3.1, R3.4, R9.1) — implementa: Kiro; revisa: Codex
  - Archivos: `src/jasp_nexus/providers/__init__.py`, `providers/base.py`, `providers/process.py`, `src/jasp_nexus/provider_runs.py`; `tests/fake_cli.py` (script invocado como `sys.executable tests/fake_cli.py --behave <caso>`: éxito, salida lenta, timeout, código ≠ 0, JSON inválido, señal de cuota) y un `Launcher` inyectable.
  - Pruebas: argv siempre lista; el prompt por stdin no aparece en argv; el entorno del hijo solo contiene nombres de la lista blanca; terminación del grupo al vencer el plazo; stdout/stderr acotados; tablas aditivas sobre una base de `local-runtime-mvp` poblada sin perder filas; `provider_runs` sin columnas de contenido.
  - Verificar: verificación base.
  - Aceptación: contrato de `design.md` §1 implementado y probado sin procesos reales de proveedores.

- [ ] **T05. Adaptador Claude** (R1.1, R1.6–R1.9) — implementa: Kiro; revisa: Codex
  - `providers/claude.py`: `build_command` según `docs/providers/claude.md`; `parse` para `json` y `stream-json` con los fixtures de T03; categorías `auth`, `quota`, `timeout`, `invalid_output`, `permission_denied`, `nonzero_exit`; `session_id`; `structured_output` con `--json-schema`; `probe()` con `claude --version` y `claude auth status`.
  - Pruebas por fixture: éxito, error, sin login, señal de cuota en stderr, `stream-json` sin evento `result` → `invalid_output` (nunca éxito).
  - Verificar: verificación base.
  - Aceptación: todos los fixtures de Claude clasificados según R1.6.

- [ ] **T06. `nexus run --provider claude` y `doctor` para Claude** (R2.1–R2.4, R4.1) — implementa: Kiro; revisa: Codex
  - `cli.py` (solo enganche de despacho, como en T02 de `local-runtime-mvp`) y `run_cli.py`: `nexus run --provider claude --workdir DIR (--brief FILE | --prompt TEXTO) [--role implement|spec|review|creative] [--allow PATH …] [--timeout S] [--resume ID] [--json]`; imprime estado, duración, tokens, id de sesión y ruta de `summary.md`; códigos de salida 0/2/3. `doctor` muestra la fila real de Claude.
  - Pruebas de extremo a extremo con la CLI falsa (incluye `nexus runs --provider` o `runs` ampliado).
  - Verificar: verificación base.
  - Aceptación real, registrada en `docs/revisiones/mpo-t06-aceptacion.md`: en WSL, sobre un repo descartable, `nexus run --provider claude` crea el archivo pedido, `diff.patch` lo muestra, la fila de `provider_runs` tiene tokens y `session_id`, y `--resume` continúa la sesión.

## F2. Adaptadores Codex y Kiro

- [ ] **T07. Adaptador Codex** (R1.1, R1.6–R1.9) — implementa: Kiro; revisa: Codex (la regla es «empresa distinta de la del modelo implementador»; que el adaptador sea de la propia CLI del revisor no la altera)
  - `providers/codex.py`: `exec - --json -C --sandbox -o --output-schema`; parser JSONL (`thread.started`, `item.completed`, `turn.completed.usage`, `error`); `thread_id` y `exec resume`; rol `review` con `codex exec review` o con prompt sobre `diff.patch`, según lo que T03 confirme en headless; mapeo de `allowed_paths` a `--sandbox read-only|workspace-write` + `--add-dir`; `probe()` con `codex --version` y `codex login status`.
  - Pruebas por fixture.
  - Verificar: verificación base.
  - Aceptación real como T06, en `docs/revisiones/mpo-t07-aceptacion.md`.

- [ ] **T08. Adaptador Kiro** (R1.1, R1.3, R1.4, R1.6–R1.9) — implementa: Codex; revisa: Claude
  - `providers/kiro.py`: `chat --no-interactive --trust-tools=…`; prompt por stdin si T03 lo confirmó (si no, por argumento, documentando la exposición en `ps`); extracción y validación del bloque JSON final; `--resume` si existe; `probe()` con versión y estado de login; `KIRO_API_KEY` solo por nombre en la lista blanca.
  - Pruebas por fixture.
  - Verificar: verificación base.
  - Aceptación real como T06, en `docs/revisiones/mpo-t08-aceptacion.md`.

- [ ] **T09. `doctor` completo y estados de proveedor** (R4.1–R4.5) — implementa: Kiro; revisa: Codex
  - `src/jasp_nexus/doctor.py` (el `doctor` heredado de `cli.py` queda como alias hasta F5): tabla por proveedor con binario, versión, login, headless (`--probe` opcional), `provider_state` y acumulados de `provider_runs`; `--json`. Detección de `quota_signals` sin distinguir mayúsculas sobre stderr y mensaje final → `provider_state=enfriamiento` hasta `now + cooldown_minutes`; `nexus providers reset <provider>`.
  - Pruebas: reloj inyectable, señal solo en la salida nueva de esa ejecución, vencimiento, restablecimiento manual, persistencia entre reinicios.
  - Verificar: verificación base.
  - Aceptación: `doctor` con las tres filas reales en WSL; nunca muestra «cuota restante».

## F3. Router, pipeline y revisión cruzada

- [ ] **T10. Router y política aditiva** (R5.1–R5.4) — implementa: Kiro; revisa: Codex
  - `src/jasp_nexus/router.py` (`design.md` §2); `config/agents.example.json` ampliado con `stage_preferences`, `review.effective_provider`, `cooldown_minutes` y `quota_signals` migrados desde `routing.yaml`. `core.load_agents` sigue leyendo `agents` sin cambios.
  - Pruebas: preferencia por etapa; exclusión por enfriamiento, no instalado o sin login; revisor de otra empresa obligatorio; `blocked` si no hay; compatibilidad con `core.route` y con el JSON actual sin claves nuevas; rechazo de política con proveedor inexistente.
  - Verificar: verificación base.
  - Aceptación: las pruebas de `core.route` existentes pasan sin modificar sus aserciones.

- [ ] **T11. Pipeline, artefactos y aprobación humana** (R3.2, R3.3, R6.1–R6.6) — implementa: Kiro; revisa: Codex
  - `src/jasp_nexus/pipeline.py`, `artifacts.py`, `prompts.py` (plantillas en español); tablas `task_steps` y `approvals`; `nexus run --task ID [--workdir DIR] [--brief FILE] [--worktree] [--allow …]`, `nexus approve ID`, `nexus reject ID --note`, `nexus status ID`, `nexus clean ID`.
  - Pruebas con la CLI falsa: ciclo completo spec → implement → review → approve; CAMBIOS → reintento hasta `max_attempts`; revisor no disponible → `blocked`; proceso muerto a mitad → paso no confirmado, nunca éxito; artefactos esperados presentes; `events` de `TaskStore` coherentes con `TRANSITIONS`; cadena centinela del brief ausente de todas las tablas.
  - Verificar: verificación base.
  - Aceptación: `store.py` sin cambios; flujo de `design.md` §3 cubierto por pruebas.

- [ ] **T12. Protección del repositorio objetivo** (R7.1–R7.4) — implementa: Kiro; revisa: Codex
  - `src/jasp_nexus/workspace.py`: comprobación de árbol limpio; `git worktree add/remove` por tarea; captura de `diff.patch`/`files.txt` con `git` por lista de argumentos; política de `allowed_paths` y `protected_paths`; rechazo automático con nota de política; aviso de instrucciones para agentes en el repo objetivo.
  - El rechazo automático usa las dos transiciones válidas de R7.3 (`running → in_review → changes_requested`, la segunda en nombre del revisor designado), sin invocar la CLI del revisor ni modificar `store.py`.
  - Pruebas con repositorios Git temporales, incluida la secuencia de `events` del rechazo automático.
  - Verificar: verificación base.
  - Aceptación: un cambio fuera de rutas permitidas o en una prueba protegida nunca llega al revisor.

- [ ] **T13. Aceptación de extremo a extremo con CLIs reales** (R5.2, R6.*, R3.2) — ejecuta: Claude con el usuario; revisa el informe: Codex
  - Repo descartable en WSL y tarea real pequeña (p. ej. «añade `slugify` con pruebas»); `nexus run --task` con Claude (spec) → Kiro (implement) → Codex (review) → `nexus approve`.
  - Informe `docs/revisiones/mpo-t13-e2e.md` con estados, artefactos, métricas y cuota consumida; sin prompts ni respuestas en SQLite (comprobado con `sqlite3 .schema` y `SELECT`).
  - Verificar: verificación base; `tests/e2e/test_real_providers.py` con `NEXUS_E2E=1`.
  - Aceptación: una tarea aprobada de punta a punta con las tres CLI previstas (Claude en `spec`, Kiro en `implement`, Codex en `review`), proveedores efectivos de empresas distintas en implementación y revisión, y aprobación humana registrada.

## F4. Backend HTTP local y consola Nuxt

- [ ] **T14. Servidor HTTP local y SSE** (R8.1–R8.4, R8.6) — implementa: Kiro; revisa: Codex
  - `src/jasp_nexus/server.py`, `api/handlers.py`, `api/sse.py`; `nexus serve [--port] [--open] [--no-browser]`; cola de trabajos en hilo (un pipeline a la vez por proveedor); `Host`/`Origin` → 403; bind solo `127.0.0.1`; límite de cuerpo; errores `{"detail": "..."}` en español; `docs/api.md`.
  - Pruebas con `http.client` en puerto efímero: health, `Host` inválido, `Origin` ajeno, crear tarea, stream SSE recibe `line`/`done` desde la CLI falsa, `stop` mata solo el proceso propio.
  - Verificar: verificación base.
  - Aceptación: ningún endpoint acepta entrada de teclado hacia un agente.

- [ ] **T15. Esqueleto `web/` Nuxt 4** (R8.5, R8.7) — implementa: Kiro; revisa: Codex
  - `web/` (Nuxt 4 SPA, TS strict, Tailwind, `@tanstack/vue-query`, Vitest, ESLint); layout con barra lateral (Panel · Nueva tarea · Tareas · Política · Doctor), píldora de estado del backend, modo claro/oscuro, cliente `api/` tipado con los tipos de `docs/api.md`, proxy de desarrollo, `npm run generate` → `src/jasp_nexus/static/`; `pyproject.toml` incluye `static/**`; `scripts/build-web.sh` (único script nuevo, sin CAO).
  - Verificar: verificación base; `cd web && npm ci && npm run lint && npm run test -- --run && npm run generate`; `nexus serve` sirve `index.html`.
  - Aceptación: build servido por `nexus serve` sin dependencias Python nuevas.

- [ ] **T16. Panel y Nueva tarea** (R8.5, R8.7, R4.1, R4.5) — implementa: Kiro; revisa: Codex (que además aporta copy y UX como rol creativo)
  - Panel: tarjeta por proveedor (instalado, login, estado, enfriamiento hasta HH:MM, tokens 5 h/24 h, botón Restablecer) y tareas activas. Nueva tarea: título, tipo (`KINDS`), complejidad, calidad, ruta del proyecto (acepta `C:\…` y convierte a `/mnt/c/…`), brief, rutas permitidas, worktree; errores por campo; al crear, navega al seguimiento.
  - Pruebas Vitest: estados de tarjeta, validación del formulario, conversión de ruta.
  - Verificar: verificación base y comandos de `web/` de T15.
  - Aceptación: con `nexus serve`, el panel muestra una tarjeta por proveedor con datos de `GET /api/doctor` y una tarea creada desde el formulario (ruta `C:\…`) aparece en `GET /api/tasks` con la ruta convertida.

- [ ] **T17. Seguimiento en vivo e historial** (R8.3, R8.5, R6.4, R6.6) — implementa: Kiro; revisa: Codex
  - Detalle de tarea: línea de etapas (spec/implement/review/aprobación) con intento, proveedor y duración; visor SSE monoespaciado con auto-scroll pausable; pestañas de artefactos (`plan.md`, `summary.md`, `diff.patch`, `review.md`); Aprobar/Rechazar con confirmación y Detener. Historial: tabla con filtros por estado, proyecto y proveedor; detalle de ejecuciones y métricas.
  - Pruebas: el auto-scroll se pausa al subir; Aprobar pide confirmación; SSE reconecta.
  - Verificar: verificación base y comandos de `web/` de T15.
  - Aceptación: una tarea ejecutada con la CLI falsa se sigue en vivo hasta `done`, sus cuatro artefactos se ven en pestañas y Aprobar desde el navegador registra la fila de `approvals` y el estado `approved`.

- [ ] **T18. Política y Doctor en la consola** (R5.3, R5.4, R4.2, R8.5) — implementa: Kiro; revisa: Codex
  - Política: editor de `stage_preferences`, `enabled`, `cooldown_minutes` y `quota_signals` con validación del backend (`PUT /api/policy` escribe `config/agents.json` del usuario, no el `.example`). Doctor: tabla de `GET /api/doctor` con botón «Probar headless» (opt-in). `docs/console.md` con cada pantalla.
  - Verificar: verificación base y comandos de `web/` de T15; lista manual de `docs/verificacion-e2e.md`.
  - Aceptación: política con proveedor inexistente rechazada en la interfaz; nada escucha fuera de `127.0.0.1` (`ss -ltnp`).

## F5. LM Studio opcional y limpieza del legado CAO

- [ ] **T19. Adaptador LM Studio** (R1.10) — implementa: Kiro; revisa: Codex
  - `providers/lm_studio.py` sobre `local_services.chat()`/`list_models()` y `LocalConfig`; solo roles de texto; `enabled: false` por defecto en `agents.example.json`; `doctor` reutiliza `run_probe`.
  - Incluye, como opcional, la aceptación real pendiente de T02 de `local-runtime-mvp` (providers → models → chat) si LM Studio está disponible; si no, se registra el impedimento sin declararla superada.
  - Verificar: verificación base.
  - Aceptación: pruebas con servidor falso para `creative`/`spec` en texto; el router no asigna `lm_studio` a `implement` ni `review`; con `enabled: false` no aparece en el routing; resultado de la aceptación real (superada o impedimento) registrado en `docs/revisiones/mpo-t19-aceptacion.md`.

- [ ] **T20. Retirada del legado CAO** (R9.6) — implementa: Kiro; revisa: Codex
  - Eliminar `profiles/`, `scripts/{start,stop,install-profiles,setup-wsl}.sh` y `config/routing.yaml`; mover `.kiro/specs/nexus-console/` y `docs/{ARCHITECTURE,SECURITY,MULTI_HOST,MACOS,WINDOWS_WSL2,setup-windows}.md` a `docs/archivo/` con nota de procedencia; sustituir el `doctor` heredado por `doctor.py` (retira la comprobación de `cao-server` y `urlopen`); actualizar `structure.md` y README.
  - Verificar: verificación base; `grep -rniI --exclude-dir=archivo --exclude-dir=revisiones "cao" AGENTS.md README.md .kiro docs src tests config` y revisión de cada coincidencia: solo se admiten menciones que presentan CAO como retirado o histórico (p. ej. la regla de retirada en AGENTS, steering y esta spec, o documentos fechados); ninguna lo presenta como plan, dependencia ni código activo. El resultado se adjunta al dictamen.
  - Aceptación: `src/` y `tests/` sin referencias a CAO ni a `cao-server`; `profiles/`, los scripts CAO y `routing.yaml` ya no existen; `nexus-console` y las guías heredadas están en `docs/archivo/` con nota de procedencia.

- [ ] **T21. Normalización del código heredado** (R9.3) — implementa: Codex; revisa: Claude
  - Quitar las exclusiones de ruff de `pyproject.toml`; tipado y mensajes en español en `cli.py`, `core.py`, `store.py`, `platform_support.py` y sus pruebas; cerrar las conexiones SQLite de `TaskStore` (deuda de Windows nativo).
  - Sin cambios de comportamiento: las pruebas foundation siguen pasando sin modificar sus aserciones. Si alguna aserción depende de un mensaje en inglés que deba traducirse, se reporta con una propuesta antes de tocarla.
  - Verificar: verificación base sin exclusiones de ruff.
  - Aceptación: `pyproject.toml` sin `extend-exclude` de archivos foundation; ruff limpio en todo el repo; misma cantidad de pruebas en verde y aserciones foundation intactas.
