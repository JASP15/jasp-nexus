# Diseño: JASP Nexus Multi-Provider Orchestrator

**Spec activa desde el 6 de noviembre de 2026.** Requisitos en [requirements.md](requirements.md); tareas en [tasks.md](tasks.md); procedencia en [la decisión](../../../docs/decision-2026-11-06.md). Este diseño amplía la base existente (argparse, setuptools, librería estándar, `TaskStore`, `local_*`); no la reemplaza.

## Punto de partida

| Pieza | Archivo | Estado real (6 de noviembre de 2026) |
|---|---|---|
| CLI `doctor/create/list/show/route/history/advance` | `src/jasp_nexus/cli.py` | Funciona. `doctor` solo hace `shutil.which` de `claude/codex/kiro-cli/cmdc` y un `urlopen` a `cao-server` (deuda: proxies y redirecciones). |
| Routing | `core.py`: `load_agents()`, `route(kind, complexity, quality, agents) -> Plan(coordinator, worker, reviewer)` | Simulado: elige por `cost_rank`, `specialties` y `max_complexity` de `config/agents.example.json`; revisor con `id != worker`; coordinador restringido a `{claude, codex}`. Sin binario, login ni cuota. |
| Tareas | `store.py`: `TaskStore.create/get/list/history/assign/advance`, tablas `tasks`/`events`, `TRANSITIONS`, `attempt`/`max_attempts=3` | Funciona. `assign()` exige `worker != reviewer`; `advance('approved'\|'changes_requested')` exige `actor == reviewer` y nota; `advance('in_review')` exige nota. Actor no autenticado. |
| Conexión local | `local_config.py`, `local_http.py`, `local_services.py` (`list_models`, `chat`, `run_probe`, `Usage`), `local_runs.py` (`RunStore`, `local_runs`/`local_run_events`), `local_cli.py` | Probada contra servidor falso (`tests/local_fakes.py`). Aceptación real contra LM Studio nunca superada; ruff nunca ejecutado en WSL. |
| CI | `.github/workflows/ci.yml` | Linux/macOS × Python 3.11/3.12, solo unittest. |

54 pruebas unittest verificadas en WSL. El legado CAO (`profiles/`, `scripts/`, `config/routing.yaml`) nunca se validó y se retira en F5.

## Arquitectura

```text
nexus CLI (argparse)  ──┐
                        ├─ pipeline.py ── router.py ── core.route + agents.json (aditivo)
consola Nuxt (web/) ────┤      │
   HTTP+SSE 127.0.0.1   │      ├─ providers/{claude,codex,kiro,lm_studio}.py  (contrato común)
server.py (stdlib) ─────┘      │        └─ providers/process.py  (Popen lista de args, plazo, env filtrado)
                               ├─ artifacts.py   .nexus/tasks/<id>/{brief,plan,summary,review}.md + diff.patch
                               └─ store.py (tasks/events) + provider_runs.py (tablas aditivas, sin contenido)
```

## 1. Capa de adaptadores (`src/jasp_nexus/providers/`) — R1

Contrato común en `providers/base.py`:

```python
@dataclass(frozen=True)
class RunRequest:
    provider: str                   # "claude" | "codex" | "kiro" | "lm_studio"
    role: str                       # "spec" | "implement" | "review" | "creative"
    workdir: Path                   # repo objetivo (absoluto, existente)
    prompt: str                     # nunca se persiste; va por stdin cuando la CLI lo admite
    allowed_paths: tuple[str, ...]  # rutas relativas que puede tocar; () = solo lectura
    timeout_seconds: float          # plazo total del proceso
    max_turns: int | None           # si la CLI lo soporta; si no, se documenta
    resume: str | None              # id de sesión previa de ese proveedor
    output_schema: dict | None      # JSON Schema de la respuesta final (si la CLI lo soporta)
    model: str | None

@dataclass(frozen=True)
class RunResult:
    status: str                # succeeded | failed | timeout | quota | auth | not_installed | killed | invalid_output
    exit_code: int | None
    session_id: str | None     # para reanudar
    final_text: str            # mensaje final del agente: va a artefacto en disco, no a SQLite
    structured: dict | None    # salida validada contra output_schema
    usage: Usage               # reutiliza local_services.Usage; cost_usd opcional aparte
    num_turns: int | None
    error_category: str | None # estable, sin texto remoto
    quota_signal: str | None   # clave de la señal detectada, no la línea

class Adapter(Protocol):
    name: str
    def probe(self) -> ProviderStatus: ...         # instalado, versión, login, headless_ok, última señal
    def build_command(self, req: RunRequest) -> Command: ...  # argv (lista), stdin, env permitido, cwd
    def parse(self, exit_code: int, stdout: str, stderr: str, req: RunRequest) -> RunResult: ...
```

`providers/process.py` ejecuta un `Command` con `subprocess.Popen(argv, cwd=..., stdin=PIPE, stdout=PIPE, stderr=PIPE, start_new_session=True, env=allowlist)`, nunca `shell=True`. Plazo total con reloj monotónico y `os.killpg` del grupo propio al vencer. Un hilo lector de líneas alimenta un `sink` (SSE en F4, artefacto raw opcional) y el runner devuelve stdout/stderr acotados por bytes. Un `Launcher` inyectable permite probar sin procesos.

Entorno del hijo (R1.4): lista blanca de nombres (`PATH`, `HOME`, `LANG`, `TERM`, `XDG_*`, `CLAUDE_CONFIG_DIR`, `CODEX_HOME`, `KIRO_API_KEY`) que se **pasan por nombre** desde el entorno de Nexus al hijo. Nexus nunca lee el valor para otra cosa, ni lo imprime ni lo guarda. Si una CLI necesita otra variable para su login, se amplía la lista por nombre; nunca se pasa el entorno completo.

### Comandos por CLI

Supuestos a confirmar en T03 con fixtures reales. Versiones vistas en macOS el 6 de noviembre de 2026: `claude` 2.1.303, `codex` 0.163.0.

| Proveedor | argv (sin prompt) | Salida | Sesión | Permisos |
|---|---|---|---|---|
| `claude` | `claude -p --output-format json\|stream-json --permission-mode <acceptEdits\|dontAsk\|plan> --allowedTools ... --add-dir <workdir> [--json-schema S] [--resume ID] [--model M] [--setting-sources user] [--bare]`; prompt por stdin | `json`: objeto final `{type:"result", subtype, is_error, result, session_id, usage, total_cost_usd, num_turns, duration_ms, structured_output?}`; `stream-json`: JSONL con el mismo `result` al final | `session_id` → `--resume` | `--permission-mode` + `--allowedTools`. `--max-turns` no aparece en 2.1.303 (verificar): el límite será por plazo y por instrucción. |
| `codex` | `codex exec - --json -C <workdir> --sandbox <read-only\|workspace-write> -o <last.md> [--output-schema S] [--model M] [--skip-git-repo-check]`; prompt por stdin (`-`). Revisor: `codex exec review`. Continuar: `codex exec resume <id> -` | JSONL de eventos (`thread.started{thread_id}`, `item.completed{agent_message}`, `turn.completed{usage}`, `error`) y último mensaje en `-o` | `thread_id` → `exec resume` (mismo cwd) | `--sandbox`; en headless, `-c approval_policy=never` o `--approve-for-me` (verificar cuál no bloquea) |
| `kiro` | `kiro-cli chat --no-interactive --trust-tools=<lista> "<prompt>"` (verificar si admite stdin); `--resume` si existe | Texto plano; el adaptador pide un bloque JSON final y lo valida contra `output_schema` | Id de conversación si la CLI lo expone (verificar) | `--trust-tools` con nombres documentados (`fs_read`, `fs_write`, `execute_bash`…); nunca `--trust-all-tools` fuera de un worktree |
| `lm_studio` | Ninguno: `local_services.chat()` (F5) | Texto + `Usage` | Sin sesión | Sin herramientas: solo `creative`/`spec` en texto |

Mapeo de etapa a permisos (R1.8): `spec`, `review` y `creative` en solo lectura (`--permission-mode plan` o lista de herramientas de lectura; `--sandbox read-only`; `--trust-tools=fs_read`); `implement` con escritura en el repo objetivo (`acceptEdits` + `--allowedTools` acotado; `workspace-write`; `fs_read,fs_write` y, si la tarea lo exige, `execute_bash` solo en worktree).

## 2. Router determinista (`router.py`) — R5

`router.py` reutiliza `core.load_agents()` y `core.route()` como invariantes (revisor independiente, complejidad, coordinador Claude/Codex) y **añade** claves a `config/agents.example.json`. El formato sigue siendo JSON, legible con la librería estándar; `core.load_agents()` sigue leyendo solo `agents` y las claves nuevas las lee `router.py`.

```json
{
  "agents": [ "...igual que hoy, más \"command\": {\"model\": null, \"permission_mode\": \"acceptEdits\"}" ],
  "stage_preferences": {
    "spec":      ["claude", "codex"],
    "creative":  ["codex", "claude", "lm_studio"],
    "implement": ["kiro", "codex", "claude"],
    "review":    ["claude", "codex"]
  },
  "review": {"cross_provider": true, "effective_provider": {"kiro": "anthropic", "claude": "anthropic", "codex": "openai", "lm_studio": "local"}},
  "cooldown_minutes": 60,
  "quota_signals": ["rate limit", "usage limit", "limit reached", "quota", "429", "try again later"]
}
```

- `router.plan(task, agents, states) -> Assignment(spec, implementer, reviewer)`: filtra por disponibilidad real (`doctor` + `provider_state`), recorre `stage_preferences` y exige `effective_provider[reviewer] != effective_provider[implementer]`. Sin revisor de otra empresa → tarea `blocked` con nota «sin revisor cruzado disponible».
- Agentes sin adaptador registrado o sin `effective_provider` (p. ej. `commandcode`) se excluyen del routing real; siguen visibles para el `route` heredado.
- `effective_provider` es configurable porque el modelo de Kiro puede cambiar (supuesto S4). Mientras Kiro use modelos de Anthropic, toda revisión de lo que implementa va a Codex.
- `config/routing.yaml` queda obsoleto: sus `cooldown_minutes` y `quota_signals` se migran en T10 y el archivo se elimina en F5. `nexus route` sigue llamando a `core.route` sin cambios.

## 3. Pipeline de una tarea (`pipeline.py`, `artifacts.py`) — R6, R7

Se reutilizan los estados de `TaskStore` tal cual (`backlog → assigned → running → in_review → approved | changes_requested | blocked`); las etapas viven en la tabla aditiva `task_steps`.

```text
create (backlog) ─router→ assign() → assigned ─[spec: plan.md]→ assigned
   ─[implement en workdir]→ advance(running) … advance(in_review, actor=implementador, nota="diff sha256 + resumen de archivos")
   ─[review: lee diff.patch + plan.md → review.md con dictamen APROBADO|CAMBIOS]→
        CAMBIOS  → advance(changes_requested, actor=revisor) → assign() (attempt+1, máx. max_attempts=3) → assigned → running …
        APROBADO → espera humana: nexus approve <id> | nexus reject <id> --note
   ─approve→ advance(approved, actor=revisor, nota="operador confirmó dictamen <hash>")  |  reject → advance(changes_requested, actor=revisor, nota del operador)
```

- **Aprobación humana (R6.4):** se registra en `approvals(task_id, decision, note, created_at)`. La transición `approved` la ejecuta el pipeline en nombre del revisor designado porque `TaskStore.advance` exige `actor == reviewer`; `store.py` no cambia. La nota de `events` identifica el hash de `review.md` y que hubo confirmación del operador.
- **Sin revisor cruzado:** `advance(blocked)` desde el estado en curso con la nota de R5.2; desde `blocked` solo se sale con un nuevo `assign()`.
- **Artefactos (R3.2, R6.3):** `.nexus/tasks/<id>/brief.md` (del usuario), `plan.md` (etapa spec), `summary.md` (mensaje final del implementador), `diff.patch` + `files.txt` (`git diff` y `git status --porcelain` del workdir tras implementar), `review.md` (dictamen). Cada prompt de etapa se compone desde estos archivos con plantillas de `prompts.py`; el prompt no se guarda. El flujo bruto de la CLI (`raw/<run_id>.jsonl`) solo se conserva con `--keep-raw`. `nexus clean <id>` borra la carpeta.
- **Dictamen (R6.5):** `review.md` empieza con una línea fija `Dictamen: APROBADO` o `Dictamen: CAMBIOS`; cualquier otra forma es `invalid_output`. El dictamen se contrasta con el sha256 de `diff.patch` vigente.
- **Protección del repo objetivo (R7):** árbol limpio o `--allow-dirty`; `--worktree` opcional (`git worktree add` por tarea, eliminado al cerrar); si `files.txt` contiene rutas fuera de `allowed_paths` o pruebas marcadas como protegidas (`protected_paths` en el brief), el pipeline fuerza `changes_requested` con nota de política, sin invocar la CLI del revisor. Como `TRANSITIONS` solo permite `running → in_review | blocked` y `advance('changes_requested')` exige `actor == reviewer`, lo hace con dos transiciones válidas: `advance(in_review, actor=implementador, nota="diff <sha256>; violación de política")` y, a continuación, `advance(changes_requested, actor=revisor designado, nota="rechazo automático de política; revisor no invocado: <rutas>")`, igual que la aprobación humana actúa en nombre del revisor. `task_steps` registra el paso de revisión como `policy_rejected` sin `run_id`. El reintento sigue el camino normal (`assign()`, `attempt+1`). Si el repo objetivo contiene `CLAUDE.md`, `AGENTS.md`, `.codex/` o hooks, se añade un aviso a `review.md` (supuesto S7).

## 4. Persistencia aditiva y `doctor` real — R2, R3, R4

Tablas nuevas en el mismo archivo SQLite, creadas de forma idempotente y **sin columnas de contenido** (patrón de `local_runs.py`):

| Tabla | Columnas |
|---|---|
| `provider_runs` | `id, task_id?, step_id?, provider, agent_id, role, started_at, finished_at, duration_ms, status, error_category, exit_code, session_id, prompt_tokens, completion_tokens, total_tokens, cost_usd, num_turns, quota_signal` |
| `provider_run_events` | `run_id, event (started\|finished\|killed), status, created_at` |
| `provider_state` | `provider PK, status (disponible\|enfriamiento\|no_instalado\|sin_login), until, reason_key, updated_at` |
| `task_steps` | `id, task_id, stage, provider, agent_id, run_id, attempt, status, artifact, created_at` |
| `approvals` | `task_id, decision, note, created_at` |

`task_steps.artifact` guarda el nombre del archivo, no su contenido. Una fila de `provider_runs` en `running` tras un cierre abrupto se presenta como «no confirmada» (R2.4).

`nexus doctor [--json] [--probe]` (`doctor.py`, F2/T09): por CLI, binario y versión (`<bin> --version`), login (`claude auth status`, `codex login status`, equivalente de Kiro a verificar), headless real solo con `--probe`, estado de `provider_state` y acumulados de 5 h y 24 h desde `provider_runs`. Nunca muestra «cuota restante». El `doctor` heredado de `cli.py` queda como alias hasta F5.

## 5. Decisión: backend de la consola en librería estándar, no FastAPI — R8, R9.2

- **Decisión:** `server.py` con `http.server.ThreadingHTTPServer` ligado a `127.0.0.1`, enrutado propio (~12 endpoints JSON), SSE (`text/event-stream`) por hilo para la salida en vivo, comprobaciones de `Host` y `Origin` (R8.2). Los manejadores viven en `api/handlers.py` como funciones puras `(request) -> (status, body)` independientes del servidor.
- **Por qué:** el repo es stdlib puro y sus pruebas ya levantan servidores HTTP efímeros en loopback (`tests/local_fakes.py`); el trabajo de fondo es `subprocess` + hilos + SQLite, donde asyncio no aporta; cero dependencias de ejecución mantiene `pip install -e .` como única instalación en WSL y macOS y la CI tal cual. FastAPI traería uvicorn, pydantic, httpx y `uv` como requisito de ejecución para una docena de rutas.
- **Coste asumido:** validación JSON y documentación de la API a mano (`docs/api.md`), sin OpenAPI.
- **Salida de emergencia:** si la API supera ~20 rutas o necesita WebSocket, se migra a FastAPI en una tarea propia revisada, conservando `api/handlers.py`. Hasta entonces FastAPI figura como «reservado» en `tech.md`, no como plan.
- Cola de trabajos en hilo: un pipeline a la vez por proveedor (supuesto S13); SQLite con el `timeout=10` existente.

## 6. Consola Nuxt (`web/`) y SSE — R8

- `web/` con Nuxt 4 (`ssr: false`, SPA), Vue 3, TypeScript `strict` sin `any`, Tailwind, TanStack Query (`@tanstack/vue-query`), Vitest y ESLint; Node LTS en WSL; textos en español.
- Producción: `nuxi generate` → copia a `src/jasp_nexus/static/` (ignorado por Git), servido por `server.py` con fallback SPA; `pyproject.toml` incluye `static/**` como package-data. `nexus serve [--port 8765] [--open] [--no-browser]` arranca todo; abre el navegador con `explorer.exe` desde WSL o `open` en macOS y, si falla, imprime la URL.
- Desarrollo: `nuxi dev --host 127.0.0.1 --port 3000` con `nitro.devProxy` de `/api` hacia `http://127.0.0.1:8765`.
- API: `GET /api/health`, `GET /api/doctor`, `GET/PUT /api/policy`, `GET/POST /api/tasks`, `GET /api/tasks/{id}`, `POST /api/tasks/{id}/run|approve|reject|stop`, `GET /api/runs?task=`, `GET /api/tasks/{id}/artifacts/{name}`.
- **SSE** `GET /api/runs/{id}/stream`: eventos `line`, `status` y `done`; solo lectura, sin entrada de teclado hacia el agente (R8.3). TanStack Query hace polling de 5 s en el resto.
- Pantallas: barra lateral (Panel · Nueva tarea · Tareas · Política · Doctor), píldora de estado del backend, modo claro/oscuro. `PUT /api/policy` escribe `config/agents.json` del usuario, nunca el `.example`.

## 7. Papel de cada proveedor

| Proveedor | En el producto | Construyendo este repo |
|---|---|---|
| Claude Code | `spec` (plan.md), `review` por defecto, depuración compleja | Escribe specs y diseño; revisa lo que implementa Codex; **no** revisa lo que implementa Kiro mientras Kiro use modelos de Anthropic |
| Codex | `creative` (textos, UX, propuestas), `review` alternativo, implementación acotada | Revisa el código de Kiro y las specs/documentación de Claude; implementa la consola si Kiro no tiene cuota |
| Kiro CLI | `implement` (primera opción), pruebas | Implementa cada `T<nn>`; su revisor es Codex |
| LM Studio | `creative`/`spec` en texto, gratuito, sin herramientas | Sin papel |

## 8. Supuestos verificables y riesgos

Numerados `S<n>` para no confundirlos con los requisitos `R<n>`.

| # | Supuesto | Cómo se verifica | Si falla |
|---|---|---|---|
| S1 | `claude -p --output-format json` devuelve `{type:"result", subtype, is_error, result, session_id, usage, total_cost_usd, num_turns}` y `--json-schema` añade `structured_output` | T03, fixture real en WSL | Parser sobre el fixture real; sin `structured_output`, se pide un bloque JSON por prompt y se valida |
| S2 | `codex exec --json` emite `thread.started{thread_id}`, `item.completed`, `turn.completed{usage}`, `error`; `-o` escribe el último mensaje; `exec resume <id>` funciona en headless con el mismo cwd | T03 | Parser sobre fixture; sin resume, cada etapa es sesión nueva con contexto por artefactos |
| S3 | Kiro CLI headless: `chat --no-interactive`, `--trust-tools` con nombres documentados, prompt por stdin, algún `--resume`, comando de estado de login y `KIRO_API_KEY` sin navegador | T03 + `kiro-cli --help` en WSL; documentación oficial de Kiro CLI headless | Sin stdin: prompt por argumento, documentado; sin resume: sesiones nuevas; login solo por navegador: `doctor` lo indica |
| S4 | Modelo efectivo de Kiro: si es de Anthropic, Claude no puede revisar lo que Kiro implementa | T03 registra el modelo que Kiro anuncia | `review.effective_provider` configurable; con un solo revisor de otra empresa (Codex), toda revisión de Kiro va a Codex |
| S5 | `claude --max-turns` no existe en 2.1.303 | `claude --help` (observado en macOS) | Límite por plazo e instrucción; `num_turns` se registra |
| S6 | `--permission-mode acceptEdits` + `--allowedTools` evita bloqueos de permisos de Claude en headless; Codex `workspace-write` no pide aprobación con `-c approval_policy=never`; el sandbox de Codex funciona en el kernel de WSL2 | T03 con escrituras y `git diff` | `dontAsk` + lista explícita; para Codex, `--approve-for-me` o solo en worktree con `danger-full-access` documentado como último recurso |
| S7 | Las CLIs leen instrucciones del repo objetivo (`CLAUDE.md`, `AGENTS.md`, `.codex`, hooks): riesgo de inyección de prompt desde un repo ajeno | Probar `--setting-sources user`/`--bare` (Claude) e `--ignore-rules`/`--ignore-user-config` (Codex) en T03 | Aviso en `review.md` (R7.4); revisor y aprobación humana como control |
| S8 | Pérdida de sesión: ids inválidos tras actualizar la CLI o `resume` ligado al cwd | Aceptación real T06/T07 | `error_category=session_lost`, sesión nueva con artefactos (R1.7) |
| S9 | No existe API de cupo restante en headless; `--max-budget-usd` de Claude solo aplica con clave API | T03 | Solo señales observadas → enfriamiento; el panel muestra «observado», nunca «restante» (R4.5) |
| S10 | Prompt por stdin y entorno por lista blanca sin romper el login de cada CLI (credenciales bajo `HOME`) | Pruebas de T04 + aceptación real T06–T08 | Ampliar la lista blanca por nombre; nunca pasar el entorno completo |
| S11 | Interpretación de R3.2: los artefactos de `.nexus/tasks/` son entregables del usuario, no logs | Escrita en `requirements.md`, aprobada con el plan | Si se revoca: `plan.md`/`summary.md`/`review.md` se borran al cerrar la tarea y solo queda `diff.patch` |
| S12 | Nuxt 4 + Tailwind + `@tanstack/vue-query` con Node LTS en WSL y rutas `/mnt/c` (rendimiento de `node_modules` en NTFS) | T15 | Clonar el repo en el sistema de archivos de WSL, documentado en `docs/setup-wsl.md` |
| S13 | Un pipeline a la vez por proveedor; SQLite con `timeout=10` | T14 | Cola FIFO en `server.py`, documentada |

## 9. Verificación de extremo a extremo

1. **Automática, siempre (CI y local, sin cuota):** `tests/test_e2e_fake.py` usa la CLI falsa para los tres proveedores y recorre `create → run --task → review → approve` y la API (`serve` en puerto efímero, SSE). Comprueba estados de `tasks`/`events`, filas de `provider_runs`/`task_steps`/`approvals`, artefactos y ausencia de prompts en SQLite (búsqueda de una cadena centinela del brief en todas las tablas, patrón de `tests/test_local_cli.py`).
2. **Real, bajo demanda (consume cuota):** `tests/e2e/test_real_providers.py` se salta salvo `NEXUS_E2E=1`; crea un repo Git temporal, ejecuta `nexus doctor --json` (tres proveedores con login), `nexus run --task` con Claude, Kiro y Codex, y `nexus approve`; registra el informe en `docs/revisiones/`.
3. **Consola:** con `nexus serve` y `NEXUS_E2E=1`, lista manual en `docs/verificacion-e2e.md`: panel con tres tarjetas, nueva tarea con ruta `C:\…`, seguimiento en vivo, aprobar desde el navegador, historial con métricas, política editada y rechazada cuando referencia un proveedor inexistente, y nada escuchando fuera de `127.0.0.1` (`ss -ltnp`).
4. **Gobernanza:** cada `T<nn>` tiene su dictamen en `docs/revisiones/mpo-t<nn>-*.md` con proveedor efectivo del implementador y revisor de otra empresa; `git log` muestra un commit por tarea; `git status` limpio; sin push.

## 10. Precisiones respecto al plan aprobado

Diferencias de redacción o de detalle frente al plan del 6 de noviembre de 2026, señaladas en la revisión cruzada de T01 ([ronda 1](../../../docs/revisiones/mpo-t01-codex-ronda-1.md)). No cambian la dirección ni el orden de tareas.

| Punto | Plan | Spec | Motivo |
|---|---|---|---|
| Rechazo automático por política (R7.3, §3) | «fuerza `changes_requested` automático con nota de política (sin llamar al revisor)» | Mismo efecto mediante `running → in_review → changes_requested`, el segundo paso en nombre del revisor designado | `TRANSITIONS` no admite `running → changes_requested` y `store.py` no se modifica (R6.1) |
| Numeración de riesgos | R1–R13 (§4) | S1–S13 (§8), mismo orden | Evitar colisión con los requisitos R1–R9 |
| Aceptación de T03 | Riesgos R1–R4 resueltos o «no soportado» con evidencia | S1–S4 igual; S5–S7 y S9 solo se anotan como evidencia observada, sin condicionar el cierre | Fidelidad al plan |
| Verificación de T20 | `grep -ri "cao" --exclude-dir=docs/archivo` solo devuelve menciones históricas en `docs/` | Búsqueda acotada a documentos vigentes y revisión de que cada coincidencia presenta CAO como retirado o histórico | La regla de retirada de CAO en AGENTS, steering y esta spec es una mención vigente legítima; el `grep` literal recorría `.git` |
| Aceptación de T13 / F3 | «tres empresas distintas» | Las tres CLI previstas y proveedores efectivos de empresas distintas en implementación y revisión | Si Kiro usa un modelo de Anthropic (S4), Claude y Kiro son la misma empresa y la condición literal sería imposible ([ronda 2](../../../docs/revisiones/mpo-t01-codex-ronda-2.md)) |
| Guías heredadas | Se archivan en F5 | Además, en T01 reciben una cabecera «sin vigencia» | Que ningún documento vigente siga declarando activa `local-runtime-mvp` |
