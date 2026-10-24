# Stack técnico y compatibilidad

Dirección conciliada con autorización del usuario del 23 de octubre de 2026. No agregar dependencias ni cambiar tecnologías sin que el orquestador lo apruebe dentro de la tarea activa.

## Base vigente: local-runtime-mvp

- Python **3.11+**, layout `src/`, paquete `jasp-nexus` y build **setuptools**.
- CLI **argparse**, entrypoint `nexus = "jasp_nexus.cli:main"`. Mantener comandos, opciones y comportamiento existente.
- Librería estándar, sin dependencias de ejecución: `sqlite3`, `urllib`, `json`, `argparse`, etc.
- Catálogo actual: `config/agents.example.json`; política de perfiles CAO: `config/routing.yaml`. No tratarlos como formatos intercambiables ni sustituir uno automáticamente por otro.
- Datos actuales: `.nexus/state.sqlite3`, configurable mediante `--db`. Preservar `tasks`, `events`, estados y APIs de `TaskStore`.
- Pruebas existentes: **unittest**, 15 casos recuperados. CI Linux/macOS y Python 3.11/3.12. No requiere CAO, credenciales ni modelos para pasar.
- T01 conserva la base exacta: no migra a Typer, hatchling, pytest ni otra ruta de SQLite. Deuda heredada de tipado, mensajes y formato documentada; no declararla resuelta por la recuperación.

## Conexiones locales previstas (T02, aún sin implementar)

- LM Studio compatible con OpenAI: descubrir IDs con `GET /v1/models`; chat con `POST /v1/chat/completions`. La presencia en la lista no demuestra que un modelo esté cargado ni su calidad.
- URLs de LM Studio y ComfyUI explícitas en configuración sin secretos; timeout finito configurable; respuestas y errores acotados. No instalar SDKs ni requerir claves de API en T02.
- Acceder solo a loopback o a un host privado WSL declarado por el usuario; rechazar URLs con credenciales, query o fragmento. No seguir redirecciones ni usar proxies implícitos.
- Añadir metadatos de ejecución en SQLite de forma aditiva, sin almacenar prompts, respuestas, variables de entorno o cuerpos arbitrarios de error. No modificar el significado de los eventos de transición existentes.

## Stack reservado para la consola pospuesta

Cuando se reactive `nexus-console`: FastAPI + uvicorn, httpx, pydantic v2/pydantic-settings, ruamel.yaml; pytest/pytest-asyncio/respx y ruff. Añadirlos mediante una tarea revisada, conservando compatibilidad. La CLI y el build siguen en argparse/setuptools salvo futura migración explícita.

Frontend previsto: React 18 + TypeScript estricto + Vite, Tailwind CSS, TanStack Query, React Router, ansi_up, Vitest/Testing Library, Node LTS y npm. No hay frontend implementado todavía.

## Integración con CAO

Default existente: `http://127.0.0.1:9889`. `docs/cao/contract.md` será la única referencia de su API y **todavía no existe**. No inventar endpoints ni afirmar compatibilidad con OpenCode. Obtener el contrato real antes del adaptador; usar `mock_cli` en pruebas si la instalación validada lo soporta. Nunca detener sesiones ajenas.

## Verificar la tarea activa

T01 y regresión de la base (desde la raíz, en WSL/POSIX):

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m jasp_nexus.cli --help
git diff --check
```

T02 añadirá pruebas con servidor HTTP local simulado y SQLite temporal, incluidas desconexión y timeout; la prueba con el servicio real se registra aparte y no se inventa si está caído. Para código nuevo o modificado exigir tipado, mensajes españoles y ruff; su configuración y disponibilidad se resuelven dentro de esa tarea sin declarar verde una herramienta no ejecutada.

Los comandos `uv run pytest -m "not e2e"`, `uv run ruff check .`, `uv run ruff format --check .` y los checks npm pertenecen a tareas futuras una vez incorporadas sus herramientas/configuración. Ejecutar los comandos "Verificar" aplicables a cada tarea antes de revisión.
