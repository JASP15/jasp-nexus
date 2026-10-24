# Conciliación local — 23 de octubre de 2026

**Estado vigente:** el contenido y el historial foundation están consolidados en `main`, sobre el merge `e120277e7930b77766f81201fa08cac6b79be1fd`. Sus padres son `9e661af670baa2e56884cc3990ab4469d92f2eca` (conservación del trabajo local) y `8683b6568ff026cb957866225115743b8b01d4f8` (foundation). Claude emitió **CAMBIOS REQUERIDOS** en ronda 1 y **APROBADO** en ronda 2 tras las correcciones documentales; T01 se marca con las comprobaciones de cierre satisfactorias. Véanse la [consolidación](consolidacion-git-2026-10-23.md) y el [registro de revisión](revisiones/local-runtime-mvp-t01.md).

## Autorización y alcance

El usuario respondió «sigamos tu propuesta» al [informe de revisión](revision-local-2026-10-23.md). Se aplica su primera etapa: conservar los cambios locales, reutilizar foundation y unificar fuentes de verdad. La spec activa pasa a `local-runtime-mvp`; la consola queda pospuesta. El orden es conexión local real → agente acotado → ComfyUI → orquestación y consola.

La autorización de la dirección no equivalía a aprobación técnica de T01. Kiro CLI no estaba disponible y Codex actuó como implementador de respaldo; la revisión correspondió a Claude, otro proveedor, y terminó con APROBADO en ronda 2. Codex no aprobó su propio trabajo.

## Procedencia y preservación: preparación histórica

Fuente exacta: `8683b6568ff026cb957866225115743b8b01d4f8` de `feat/foundation-cao-mvp`. Se recuperaron archivos ausentes mediante lectura de blobs Git:

- `src/jasp_nexus/`, `tests/`, `pyproject.toml`, `config/agents.example.json` y `.github/workflows/ci.yml`.
- Documentación foundation: arquitectura, seguridad, Windows/WSL2, macOS, multi-host y roadmap. El roadmap se concilia con la nueva secuencia; las demás guías se identifican como referencia histórica.

En aquella preparación no se hizo checkout, merge, staging, commit ni push: se trabajaba en `feat/estructura-inicial`, HEAD `caeb82e`, copiando contenido sin incorporar aún los 13 commits foundation. Ese estado terminó con la consolidación autorizada. Hoy los commits sí están incorporados en `main`; no es un criterio vigente mantener aquel HEAD ni el contenido sin commit.

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

`doctor` usa `urllib.request.urlopen`, que admite proxies del entorno por defecto y sigue redirecciones. Es deuda heredada conservada en T01; no acredita el aislamiento de red exigido a T02. El cliente nuevo de `providers/models/chat` deberá desactivar explícitamente proxies y redirecciones y probarlo, sin heredar ese patrón ni corregir `doctor` dentro de esta conciliación.

## Verificación registrada de la preparación histórica

- El orquestador verificó que los 11 archivos de código, tests, pyproject, catálogo y CI recuperados son idénticos byte a byte al commit fuente.
- En el checkout actual, WSL Ubuntu 24.04 / Python 3.12.3: **15/15 pruebas unittest aprobadas**.
- Smoke CLI con SQLite temporal: create → route → show/history/list aprobado; estado `assigned`, trabajador y revisor distintos, dos eventos y aviso `SIMULATION ONLY`. No se ejecutaron proveedores.
- En esa preparación se registraron 16 copias de originales verificadas por hash, 11 archivos foundation conservados byte a byte y `git diff --check` sin errores. HEAD, rama e índice no cambiaron durante esa etapa; la consolidación posterior sí cambió el historial y la rama.
- No se ejecutaron ruff, pytest, frontend, proveedores ni CI remoto en esta conciliación. No se presentan como comprobaciones verdes.

## Criterios vigentes de revisión y cierre

La revisión evalúa el estado consolidado en `e120277` y sus correcciones documentales: foundation como ancestro de `main`, los 11 archivos enumerados en T01 idénticos al origen, respaldos íntegros, compatibilidad CLI/SQLite y 15 pruebas con smoke temporal en verde. El árbol estaba limpio antes de estas correcciones y deberá volver a estarlo después del cierre; durante revisión solo se admiten cambios documentales inventariados.

El dictamen externo **APROBADO** de ronda 2 y las comprobaciones repetidas después de recibirlo permiten el commit de cierre con las correcciones revisadas, la casilla `[x]` y el registro del dictamen y su alcance. Las 15 pruebas y el smoke temporal pasaron; los 11 archivos siguen idénticos a foundation. Esta evidencia fue comprobada por Codex, no ejecutada por Claude. El merge de conservación no aprueba la tarea. T02 no ha comenzado.
