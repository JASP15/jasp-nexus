# Conciliación local — 23 de octubre de 2026

**Actualización posterior:** el usuario aclaró que quería una sola rama con todo fusionado. El contenido y el historial foundation se consolidan en `main` mediante commits de conservación y merge local; la revisión externa de T01 sigue pendiente. Las referencias a «sin commit» o «historial no incorporado» de este informe describen el estado de preparación anterior a esa [consolidación](consolidacion-git-2026-10-23.md).

## Autorización y alcance

El usuario respondió «sigamos tu propuesta» al [informe de revisión](revision-local-2026-10-23.md). Se aplica su primera etapa: conservar los cambios locales, reutilizar foundation y unificar fuentes de verdad. La spec activa pasa a `local-runtime-mvp`; la consola queda pospuesta. El orden es conexión local real → agente acotado → ComfyUI → orquestación y consola.

T01 queda **pendiente de revisión de otro proveedor**. La autorización de la dirección no equivale a aprobación técnica de la tarea. Kiro CLI no estaba disponible y Codex actuó como implementador de respaldo; Codex no puede cerrar su propia revisión.

## Procedencia y preservación

Fuente exacta: `8683b6568ff026cb957866225115743b8b01d4f8` de `feat/foundation-cao-mvp`. Se recuperaron archivos ausentes mediante lectura de blobs Git:

- `src/jasp_nexus/`, `tests/`, `pyproject.toml`, `config/agents.example.json` y `.github/workflows/ci.yml`.
- Documentación foundation: arquitectura, seguridad, Windows/WSL2, macOS, multi-host y roadmap. El roadmap se concilia con la nueva secuencia; las demás guías se identifican como referencia histórica.

No se hizo checkout, merge, staging, commit ni push durante la preparación. La rama se mantiene en `feat/estructura-inicial` y el HEAD de partida es `caeb82e`. **No se incorporaron al historial los 13 commits foundation**; su contenido recuperado está sin commit. Un futuro commit T01, únicamente tras revisión aprobada, registra la conciliación sin convertirla en un merge de aquel historial.

Los archivos seguros existentes antes de editarlos se copiaron a `.build/reconcile-2026-10-23/originals/`. El manifiesto `.build/reconcile-2026-10-23/manifest.json` registra paths explícitos, hashes, origen y resultado. No se leyeron ni copiaron `.env`, claves, tokens, credenciales o variables de entorno con secretos. Los originales de documentos foundation modificados también se conservan con su hash fuente.

Se conservaron perfiles, scripts, política YAML, `.gitattributes` y el archivo accidental identificado en la revisión. No se ejecutaron scripts, instalaciones, servicios ni agentes de desarrollo como efecto de esta recuperación.

## Compatibilidad acordada

| Área | Decisión |
|---|---|
| CLI | argparse, `jasp_nexus.cli:main`; conservar comandos y opciones actuales |
| Paquete | setuptools, Python 3.11+, sin dependencias de ejecución |
| Pruebas | unittest y las 15 pruebas originales |
| Datos | `.nexus/state.sqlite3` o `--db`; mantener `TaskStore`, tablas `tasks/events`, estados e historial |
| Catálogos | JSON para routing simulado; YAML de perfiles CAO separado hasta integración explícita |
| Conexiones locales | T02 pendiente, con límites y metadatos aditivos; no herramientas ni agentes |
| Consola | T02 amplía paquete, T04 amplía SQLite con tablas propias; no recrear CLI ni esquema |
| Seguridad y revisión | Mantener AGENTS, prohibición de paradas globales y revisor de otro proveedor |

La spec de consola ya no propone una segunda base canónica ni migrar automáticamente a Typer/hatchling. La propuesta de parada global queda excluida por AGENTS; sus scripts permanecen sin corregir hasta una tarea con alcance propio.

## Estado real y deuda heredada

La base recuperada simula asignación de roles. `route` no comprueba disponibilidad/login/cuota ni ejecuta proveedores. `--actor` es un registro declarado, no identidad autenticada. Tampoco se ha implementado LM Studio, OpenCode, ComfyUI, contrato CAO, cuota ni interfaz web.

Foundation conserva mensajes en inglés, tipado parcial y formato previo; esta tarea no los normaliza ni declara ruff aprobado. Código nuevo/modificado posterior debe cumplir AGENTS y prever su verificación. Las pruebas y la procedencia exacta evitan ocultar una reescritura de la base bajo la conciliación.

## Verificación

- El orquestador verificó que los 11 archivos de código, tests, pyproject, catálogo y CI recuperados son idénticos byte a byte al commit fuente.
- En el checkout actual, WSL Ubuntu 24.04 / Python 3.12.3: **15/15 pruebas unittest aprobadas**.
- Smoke CLI con SQLite temporal: create → route → show/history/list aprobado; estado `assigned`, trabajador y revisor distintos, dos eventos y aviso `SIMULATION ONLY`. No se ejecutaron proveedores.
- Revisión de consistencia documental y espacios finales aprobada; 16 copias de originales verificadas por hash, 11 archivos foundation conservados byte a byte y `git diff --check` sin errores. HEAD, rama e índice permanecen sin cambios. Git avisa únicamente de conversión LF/CRLF en README.
- No se ejecutaron ruff, pytest, frontend, proveedores ni CI remoto en esta conciliación. No se presentan como comprobaciones verdes.

El resultado está listo para revisión cruzada. Solo después de aprobación cruzada puede marcarse T01 y prepararse su commit; T02 no ha comenzado.
