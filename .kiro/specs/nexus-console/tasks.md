# Tareas: JASP Nexus Console

**POSPUESTA desde el 23 de octubre de 2026.** La spec activa es `../local-runtime-mvp/`. No ejecutar este plan hasta completar el flujo local y revalidar su alcance. Los números Tnn de este documento pertenecen solo a la consola.

Reglas de este plan:
- Se ejecutan **en orden**. Una tarea solo empieza cuando la anterior está marcada `[x]`.
- Cada tarea cita los requisitos (R*) de `requirements.md` y sigue `design.md`.
- "Verificar" lista los comandos que deben quedar en verde antes de pedir revisión.
- Al aprobarse, el desarrollador marca la casilla `[x]` y hace commit: `T<nn>: <título>`.
- Si una tarea es imposible tal como está escrita, **no improvises**: reporta al orquestador el bloqueo y una propuesta.

---

## Fase 0: Cimientos

- [ ] **T01. Contrato real de la API de CAO**
  - Con `cao-server` ya corriendo, descarga `http://localhost:9889/openapi.json` a `docs/cao/openapi.json`.
  - Escribe `docs/cao/contract.md` documentando, para cada operación que usará Nexus (ver lista en design.md › Cliente de CAO): método, ruta, parámetros (query/body) con tipos, respuesta de ejemplo y códigos de error. Incluye cuál es el campo/valor que indica que una terminal está **lista para recibir entrada** y cómo se obtiene su **proveedor**.
  - Captura respuestas reales a `tests/fixtures/cao/*.json` creando una sesión con el proveedor `mock_cli` (instala un perfil de prueba en `tests/e2e/profiles/nexus_mock_supervisor.md` con `provider: mock_cli`). **Borra solo la sesión que creaste.**
  - Hecho cuando: los tres artefactos existen y cada operación de la lista tiene su sección.
  - Verificar: `python3 -m json.tool docs/cao/openapi.json > /dev/null`.

- [ ] **T02. Ampliar el paquete Python existente** (R9.1)
  - Reutilizar `pyproject.toml`, setuptools, layout `src/`, Python ≥ 3.11 y entrypoint `nexus = "jasp_nexus.cli:main"`. No recrear el paquete, cambiarlo a hatchling/Typer ni sustituir comandos existentes.
  - Añadir solo dependencias de consola de tech.md cuando se reactive esta spec, su configuración de pytest (marca `e2e`) y ruff. Preservar los tests unittest y la CLI de la spec local.
  - Añadir `version` a argparse si sigue siendo necesario, usando `__version__` existente sin reinicializarlo.
  - Comprobar `.gitignore` y empaquetado sin eliminar protecciones existentes.
  - Verificar: `PYTHONPATH=src python3 -m unittest discover -s tests -v`; checks pytest/ruff de la ampliación y smoke de comandos anteriores; `nexus version` cuando exista.

- [ ] **T03. Settings y política de asignación** (R7.1, R7.2, R7.3)
  - `settings.py` según design.md (rechazar `host` distinto de `127.0.0.1`).
  - `routing.py`: modelos pydantic que reflejen **exactamente** `config/routing.yaml` (incluido `cooldown_minutes`), `load_routing()`, `validate_routing(r, profile_names)` (error por perfil inexistente) y `save_routing()` con ruamel.yaml preservando comentarios.
  - Pruebas: carga del archivo real, perfil inexistente rechazado, guardado conserva comentarios (comparar que una línea `#` siga presente).
  - Verificar: `uv run pytest tests/test_routing.py tests/test_settings.py`

- [ ] **T04. Extender la persistencia SQLite existente** (R5.7, R6.5)
  - Reutilizar `TaskStore`, ubicación `.nexus/state.sqlite3` y opción `--db`; preservar tablas `tasks/events`, estados, IDs, historial, límites y APIs existentes, así como tablas que incorpore local-runtime-mvp.
  - Añadir tablas complementarias `console_tasks`, `console_events`, `provider_state` y `output_cursor` según design.md. No recrear `tasks/events` con columnas incompatibles ni abrir otra base canónica en `~/.jasp-nexus/nexus.db`.
  - Diseñar migraciones aditivas/versionadas que reconozcan una base foundation poblada y cualquier extensión local ya aplicada. Detallar la adaptación transaccional antes de implementarla.
  - Añadir servicio de consola con operaciones de creación/consulta/actualización de metadatos, eventos, cuota, cursores y proyectos recientes; no reemplazar métodos de TaskStore.
  - Probar una base temporal del esquema anterior poblada, reapertura idempotente, conservación de datos/historial y funciones nuevas. Mantener intactas las pruebas originales.
  - Verificar: pruebas unittest de regresión; `uv run pytest tests/test_console_store.py` una vez disponible pytest en T02.

- [ ] **T05. Cliente de CAO** (R9.1)
  - `cao_client.py` según design.md y **exclusivamente** según `docs/cao/contract.md`.
  - Pruebas con respx usando los fixtures de T01: éxito de cada método, `CaoUnavailable` ante conexión rechazada, `CaoError` con `detail`.
  - Verificar: `uv run pytest tests/test_cao_client.py`

## Fase 1: Backend

- [ ] **T06. App FastAPI y seguridad** (R2.1, R2.2, R2.3, R3.1, R1.6)
  - `app.py` con `create_app(settings, cao_client, store)` (inyección para pruebas), middleware de `Host` y `Origin`, `GET /api/health`, servido de `static/` con fallback a `index.html`.
  - Pruebas: Host inválido → 403; POST con Origin ajeno → 403; health con CAO arriba y caído.
  - Verificar: `uv run pytest tests/test_app.py`

- [ ] **T07. Lectura: proveedores, sesiones y salida** (R3.2, R5.1, R5.2, R2.4)
  - Routers `providers.py`, `sessions.py`: `GET /api/providers`, `GET /api/terminals/{id}/output` (403 si la terminal no pertenece a una tarea de la Consola), `GET /api/projects/recent`.
  - Verificar: `uv run pytest tests/api/`

- [ ] **T08. Tareas** (R4.*, R5.3, R5.4, R5.5)
  - Router `tasks.py` y servicio con el ciclo de vida de design.md, incluido `TaskWatcher` y conversión de rutas Windows → WSL.
  - Pruebas: ruta inexistente, worktree sin git, éxito completo con CAO simulado, timeout del supervisor (cierra sesión y marca error), enviar mensaje, detener, sesión desaparecida → finalizada.
  - Verificar: `uv run pytest tests/api/test_tasks.py`

- [ ] **T09. Monitor de cuota** (R6.*, R3.3)
  - `quota.py` (`QuotaMonitor` con reloj inyectable), router `quota.py`, escritura atómica de `quota.json`.
  - Arrancar/parar el monitor y el `TaskWatcher` en el `lifespan` de FastAPI.
  - Pruebas: detecta señal solo en salida nueva, respeta `cooldown_minutes`, vence, reset manual, sobrevive reinicio (estado en SQLite).
  - Verificar: `uv run pytest tests/test_quota.py`

- [ ] **T10. Política y perfiles por API** (R7.*, R8.*)
  - `profiles.py`: portar la lógica de `scripts/install-profiles.sh` (sustituir `{{NEXUS_HOME}}` y `{{NEXUS_DATA}}`, llamar `cao install` con `subprocess.run` y lista de argumentos, nunca `shell=True`).
  - Routers `routing.py` (`GET/PUT`) y `profiles.py` (`GET`, `POST /install`).
  - Reemplaza el cuerpo de `scripts/install-profiles.sh` por `nexus install-profiles` cuando el comando exista (T18); por ahora deja el script como está.
  - Verificar: `uv run pytest tests/api/test_routing.py tests/api/test_profiles.py`

## Fase 2: Frontend

- [ ] **T11. Esqueleto web** (R9.3)
  - `web/` con Vite + React + TS estricto + Tailwind + TanStack Query + React Router + ESLint + Vitest. `vite.config.ts`: `build.outDir = "../src/jasp_nexus/static"`, `emptyOutDir: true`, proxy `/api` → `http://127.0.0.1:8765`.
  - Layout con barra lateral, encabezado con píldora de CAO, banner "CAO caído", modo claro/oscuro, rutas vacías para cada página.
  - `web/src/api/` con cliente fetch tipado y tipos de todas las respuestas de la API.
  - Verificar: `cd web && npm run lint && npm run test -- --run && npm run build`

- [ ] **T12. Panel** (R3.*)
  - Tarjetas de proveedor, botón Restablecer, lista de tareas activas, estado vacío.
  - Prueba: render de los tres estados de proveedor.

- [ ] **T13. Nueva tarea** (R4.1, R4.2, R4.5)
  - Formulario completo de design.md con datalist de recientes, radio cards de supervisor, errores por campo y estado de carga. Al crear, navegar al detalle.
  - Prueba: validación de campos vacíos y navegación tras éxito (API simulada).

- [ ] **T14. Detalle de tarea** (R5.1–R5.4, R5.6)
  - Árbol de terminales, visor de salida con `ansi_up` y auto-scroll pausable, caja de mensaje, Detener con confirmación, enlace a Web UI de CAO.
  - Prueba: el auto-scroll se pausa al subir; Detener pide confirmación.

- [ ] **T15. Historial de tareas** (R5.7)
  - Tabla con filtros por estado y proyecto.

- [ ] **T16. Enrutamiento** (R7.*)
  - Editor de design.md; muestra errores de validación del API sin perder lo editado.
  - Prueba: reordenar `prefer` con ↑ ↓ cambia el payload enviado.

- [ ] **T17. Perfiles** (R8.*)
  - Tabla y botón de reinstalación con log por perfil.

## Fase 3: Ejecutable

- [ ] **T18. CLI completa** (R1.1, R1.2, R1.4, R1.5, R1.6)
  - `nexus up [--port] [--no-browser]`, `nexus down`, extensión compatible de `nexus doctor` y `nexus install-profiles`. Conservar todos los comandos anteriores. La variante global `--all` queda excluida; detener solo recursos propios según AGENTS y R1.4.
  - Abrir navegador desde WSL con `explorer.exe <url>`; si no existe, `xdg-open`; si falla, solo imprimir la URL.
  - Cambia `scripts/install-profiles.sh` para que delegue en `nexus install-profiles` si `nexus` está instalado.
  - Pruebas de `doctor` con `shutil.which` simulado; de `up` verificando que no inicia `cao-server` si ya responde.
  - **No ejecutes `nexus down --all` durante el desarrollo**: mataría la sesión del orquestador.

- [ ] **T19. Build y empaquetado** (R1)
  - `scripts/build.sh` según design.md; `pyproject.toml` incluye `static/` en el wheel.
  - Verificar: `bash scripts/build.sh && unzip -l dist/*.whl | grep static/index.html`

- [ ] **T20. Lanzador de Windows** (R1.3)
  - `launchers/windows/JASP-Nexus.cmd` y `crear-acceso-directo.ps1` según design.md, con finales de línea CRLF (agrega `*.cmd text eol=crlf` y `*.ps1 text eol=crlf` a `.gitattributes`).
  - No se puede probar desde WSL: documenta la prueba manual en el PR.

- [ ] **T21. Prueba e2e con mock_cli** (R9.2)
  - `tests/e2e/test_console_e2e.py`: con `cao-server` real, instalar `nexus_mock_supervisor`, levantar la app en un puerto libre, crear tarea por API, ver terminales y salida, detenerla. Saltar (`pytest.skip`) si `cao` no está en el PATH.
  - Verificar: `uv run pytest -m e2e`

- [ ] **T22. Documentación**
  - `docs/console.md` (guía de uso con cada pantalla), actualizar `README.md` (sección "Consola") y `docs/setup-windows.md` (build, `uv tool install`, lanzador y acceso directo).
