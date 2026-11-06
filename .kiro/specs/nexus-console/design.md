# Diseño: JASP Nexus Console

> **REEMPLAZADA el 6 de noviembre de 2026 por la fase F4 de [multi-provider-orchestrator](../multi-provider-orchestrator/requirements.md)** ([decisión](../../../docs/decision-2026-11-06.md)). No se ejecutan sus tareas: CAO, tmux, perfiles, `routing.yaml`, FastAPI y React quedan fuera del plan. Se conserva como referencia hasta F5/T20, que la archiva en `docs/archivo/`, porque sus requisitos de seguridad local (R2.1–R2.3 y R2.5: bind en `127.0.0.1`, `Host`/`Origin`, sin secretos en logs) y la prohibición de exponer PTY (R2.4) se reutilizan en F4. El texto siguiente es histórico.

**POSPUESTO desde el 23 de octubre de 2026.** Primero se ejecuta `../local-runtime-mvp/`. La consola es una extensión de la base existente: argparse/setuptools y `TaskStore`, no un paquete nuevo. Sus dependencias, endpoints y componentes siguen sin implementar.

## Decisión: aplicación web local, no app de escritorio

CAO, tmux y las CLIs de agentes viven dentro de WSL. Una app de escritorio de Windows (Electron/Tauri) tendría que cruzar a WSL para todo, y además requiere empaquetar, firmar y actualizar binarios. Una web local servida desde WSL:
- habla directo con CAO en `localhost:9889`;
- se abre desde Windows porque WSL2 reenvía `localhost`;
- se "ejecuta" con doble clic mediante un lanzador `.cmd`;
- si después se quiere ventana propia, el mismo frontend se envuelve en Tauri sin reescribirlo.

## Arquitectura

```
Windows                               WSL2 (Ubuntu)
┌──────────────┐   http://127.0.0.1:8765   ┌───────────────────────────────┐
│ Navegador    │ ───────────────────────▶ │ Consola (uvicorn + FastAPI)    │
│ (React SPA)  │                           │  ├─ /api/*  routers            │
└──────────────┘                           │  ├─ QuotaMonitor (asyncio)     │
┌──────────────┐  wsl.exe nexus up         │  ├─ SQLite .nexus/      │
│ JASP-Nexus   │ ───────────────────────▶ │  └─ static/ (build de web/)    │
│ .cmd         │                           └──────────────┬────────────────┘
└──────────────┘                                          │ httpx
                                           ┌──────────────▼────────────────┐
                                           │ cao-server :9889 (tmux)        │
                                           │  supervisor ─ trabajadores     │
                                           │  (claude / codex / kiro-cli)   │
                                           └───────────────────────────────┘
```

## Configuración (`settings.py`)

`NexusSettings` con prefijo de entorno `NEXUS_`:

| Campo | Defecto |
|---|---|
| `host` | `127.0.0.1` (no configurable a otra interfaz: validar y rechazar) |
| `port` | `8765` |
| `cao_url` | `http://localhost:9889` |
| `home` | raíz del repo: `NEXUS_HOME` o, si no, el directorio que contiene `config/routing.yaml` subiendo desde el paquete |
| `data_dir` | `~/.jasp-nexus` (solo cuota/logs auxiliares; no otra base SQLite) |
| `db_path` | `.nexus/state.sqlite3` (misma opción `--db` de la CLI, ruta explícita compartida) |
| `poll_quota_seconds` | `15` |
| `supervisor_ready_timeout` | `120` |

## Persistencia: ampliar la base existente

La única base canónica sigue siendo `.nexus/state.sqlite3`, salvo ruta explícita `--db`. La consola debe resolver la misma ruta al arrancar; no crear `~/.jasp-nexus/nexus.db` ni trasladar datos silenciosamente.

Foundation ya define `tasks(id,title,kind,complexity,quality,state,coordinator,worker,reviewer,attempt,max_attempts)` y `events(id,task_id,from_state,to_state,actor,note,created_at)`. Se conservan esas tablas y las APIs de `TaskStore`; `events` sigue representando transiciones del dominio. Las tablas de ejecuciones locales que añada la spec activa también se conservan.

La consola añade metadatos en tablas propias; este es el esquema complementario previsto, que debe revalidarse en T04 contra las migraciones ya existentes:

```sql
CREATE TABLE console_tasks (
  task_id TEXT PRIMARY KEY REFERENCES tasks(id),
  project_path TEXT NOT NULL,
  prompt TEXT NOT NULL,
  supervisor_profile TEXT NOT NULL,
  use_worktree INTEGER NOT NULL,
  cao_session TEXT,
  status TEXT NOT NULL,
  error TEXT,
  created_at TEXT NOT NULL,
  ended_at TEXT
);
CREATE TABLE console_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id TEXT NOT NULL REFERENCES console_tasks(task_id),
  kind TEXT NOT NULL,
  data TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE provider_state (
  provider TEXT PRIMARY KEY,
  status TEXT NOT NULL,
  until TEXT,
  reason TEXT
);
CREATE TABLE output_cursor (
  terminal_id TEXT PRIMARY KEY,
  last_hash TEXT NOT NULL,
  last_len INTEGER NOT NULL
);
```

Los estados de sesión `iniciando/activa/finalizada/detenida/error` pertenecen a `console_tasks.status`; no sustituyen los estados de `TaskStore`. Crear la tarea base y sus metadatos en una transacción: T04 debe definir la adaptación explícita de atributos de tarea y transiciones según evidencia. No usar un evento de consola para fingir una aprobación del revisor.

Migraciones aditivas con versión de esquema, reconociendo bases anteriores sin versión y extensiones de local-runtime-mvp; respaldar y validar antes de cambios de datos reales. Probar la apertura de una base anterior poblada, conservación del historial e idempotencia. Las funciones de consola viven en un servicio/adaptador; no sobrescriben `TaskStore.create/get/list/history/assign/advance`.

La política de retención del prompt y payload de eventos de consola se debe revalidar antes de activar esta spec; T02 local-runtime-mvp solo guarda metadatos, nunca mensajes ni cuerpos remotos.

## `~/.jasp-nexus/state/quota.json` (R6.3)

Lo leen los supervisores antes de delegar. Escritura atómica (archivo temporal + `os.replace`).

```json
{
  "updated_at": "2026-10-20T15:04:05Z",
  "providers": {
    "codex":       { "status": "enfriamiento", "until": "2026-10-20T16:04:05Z", "reason": "usage limit" },
    "claude_code": { "status": "disponible" },
    "kiro_cli":    { "status": "disponible" }
  }
}
```

## Cliente de CAO (`cao_client.py`)

- `CaoClient(base_url)` sobre `httpx.AsyncClient` con timeout de 10 s.
- Métodos (nombres orientativos; los parámetros exactos salen de `docs/cao/contract.md`): `health()`, `providers()`, `profiles()`, `create_session(provider, agent_profile, working_directory, use_worktree, description)`, `list_sessions()`, `get_session(name)`, `list_terminals(session)`, `get_terminal(id)`, `get_output(id, mode="full")`, `send_input(id, text)`, `delete_session(name)`.
- Errores: `CaoUnavailable` (conexión rechazada/timeout) y `CaoError(status, detail)` (respuesta 4xx/5xx con `detail`).
- **El proveedor de una terminal** se toma de la respuesta de CAO; si no viene, del perfil instalado.

## API de la Consola

Todas bajo `/api`, JSON, errores como `{"detail": "..."}` en español.

| Método y ruta | Descripción | Req |
|---|---|---|
| `GET /api/health` | `{nexus: "ok", cao: "ok"|"caido", version}` | R3.1 |
| `GET /api/providers` | Proveedores de routing.yaml + instalado (CAO) + estado de cuota | R3.2 |
| `GET /api/quota` · `POST /api/quota/{provider}/reset` | Estado de cuota / restablecer | R3.3, R6 |
| `GET /api/tasks?status=&project=` | Historial | R5.7 |
| `POST /api/tasks` | Body `{project_path, prompt, supervisor_profile, use_worktree}` → 201 tarea | R4 |
| `GET /api/tasks/{id}` | Tarea + terminales de su sesión | R5.1 |
| `POST /api/tasks/{id}/message` | Body `{text}`, solo al supervisor | R5.3 |
| `POST /api/tasks/{id}/stop` | Cierra la sesión | R5.4 |
| `GET /api/terminals/{id}/output` | Salida reciente; solo terminales de tareas de la Consola | R5.2 |
| `GET /api/projects/recent` | Últimas 10 rutas usadas | R4.1 |
| `GET /api/routing` · `PUT /api/routing` | Leer/guardar política | R7 |
| `GET /api/profiles` · `POST /api/profiles/install` | Listar / reinstalar | R8 |

Cualquier otra ruta que no empiece con `/api` sirve `static/index.html` (fallback de SPA).

### Ciclo de vida de una tarea (R4.3, R5.5)

1. Validar y normalizar ruta (convertir `C:\...` → `/mnt/c/...`).
2. Crear o vincular tarea base mediante el adaptador compatible y añadir metadatos `console_tasks.status=iniciando`, en transacción.
3. `create_session(provider=<del perfil>, agent_profile=<supervisor>, working_directory, use_worktree, description="Nexus: <primeros 50 caracteres de la petición>")`.
4. Esperar con polling (1 s) hasta que la terminal del supervisor esté en el estado "listo/idle" del contrato. Timeout → `error` y cerrar la sesión.
5. `send_input(terminal_supervisor, prompt)` → tarea `activa`.
6. Una tarea de fondo `TaskWatcher` (cada 10 s) marca `finalizada` las tareas activas cuya sesión ya no existe en CAO.

### QuotaMonitor (R6)

Cada `poll_quota_seconds`, para cada terminal de cada tarea activa: leer salida, quedarse con la parte posterior a la última longitud/hash conocida (si el buffer rotó, analizar todo y aceptar posibles duplicados), buscar señales, actualizar `provider_state`, registrar evento `quota_hit`, reescribir `quota.json`. También vence enfriamientos. Inyectar un reloj (`now: Callable[[], datetime]`) para poder probarlo.

## Frontend

### Navegación (barra lateral)
Panel · Nueva tarea · Tareas · Enrutamiento · Perfiles. Encabezado con píldora de estado de CAO (verde "CAO conectado" / roja "CAO caído") y versión.

### Páginas
- **Panel:** cuadrícula de tarjetas de proveedor (nombre, fortalezas, estado con color: verde disponible, ámbar enfriamiento con hora local, gris no instalado; botón Restablecer). Debajo, lista de tareas activas (clic → detalle).
- **Nueva tarea:** formulario de R4.1. La ruta tiene un datalist con recientes. Supervisor como radio cards: "Claude orquesta (nexus_supervisor)" y "GPT orquesta a Kiro (nexus_build_codex)". Botón "Lanzar" con estado de carga ("Iniciando supervisor…"). Errores del API debajo del campo correspondiente.
- **Detalle de tarea:** cabecera (estado, proyecto, supervisor, duración, botón Detener con diálogo de confirmación, enlace a Web UI de CAO). Columna izquierda: árbol de terminales. Derecha: visor de salida (fuente monoespaciada, fondo oscuro siempre, `ansi_up`, auto-scroll pausable con botón "Ir al final"). Abajo: caja para mensaje al supervisor (Enter envía, Shift+Enter nueva línea).
- **Tareas:** tabla con filtros (estado, proyecto), orden por fecha descendente.
- **Enrutamiento:** secciones Rutas (por tipo, lista ordenable con botones ↑ ↓ y selector para agregar perfil), Proveedores (cuota alta/medio/bajo), Revisión (revisor por proveedor, max_rounds), Señales de cuota (chips editables) y `cooldown_minutes`. Botón Guardar; errores de validación arriba.
- **Perfiles:** tabla nombre/proveedor/rol/instalado; botón "Reinstalar perfiles" con log de resultado.

### Estados vacíos y errores
- Sin tareas: mensaje con botón "Lanzar la primera tarea".
- CAO caído: banner en todas las páginas con el comando para arrancarlo (`nexus up`).
- Errores de red: toast no bloqueante; TanStack Query reintenta.

## Lanzador de Windows (R1.3)

`launchers/windows/JASP-Nexus.cmd`:
1. `start "JASP Nexus" /min wsl.exe -d Ubuntu-24.04 -- bash -lc "nexus up --no-browser"`
2. Bucle con `powershell -NoProfile -Command "try{(Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8765/api/health).StatusCode}catch{0}"` cada 2 s, hasta 60 s.
3. `start "" http://127.0.0.1:8765`.
4. La distro se puede cambiar con la variable `NEXUS_DISTRO`.

`launchers/windows/crear-acceso-directo.ps1` crea un acceso directo en el Escritorio que apunta al `.cmd`.

## Empaquetado (R1)

- `scripts/build.sh`: `npm ci && npm run build` en `web/` (sale a `src/jasp_nexus/static/`), luego `uv build`.
- Instalación global en WSL: `uv tool install --force .` → comando `nexus` en el PATH.
- `pyproject.toml` conserva setuptools e incluirá `static/**` mediante package-data cuando exista el frontend. No migrar el backend de build a hatchling para empaquetar estáticos.
