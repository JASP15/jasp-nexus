CAMBIOS REQUERIDOS

El trabajo es sólido en lo esencial: la base recuperada coincide con foundation, el alcance de T01 está bien contenido y T02 no se declara implementada. Pero hay incoherencias documentales concretas que contradicen la evidencia observada y que conviene corregir antes de marcar T01. Reviso solo el texto adjunto; no ejecuté nada, así que los resultados de pruebas y hashes los tomo como declarados por el implementador.

## Hallazgos que requieren corrección

**1. `docs/conciliacion-local-2026-10-23.md`: estado de Git contradictorio dentro del mismo documento.**
La sección "Procedencia y preservación" afirma que el contenido recuperado está "sin commit", que la rama es `feat/estructura-inicial` con HEAD `caeb82e` y que "no se incorporaron al historial los 13 commits foundation". La sección "Verificación" repite que "HEAD, rama e índice permanecen sin cambios". El aviso inicial lo matiza, pero el cuerpo sigue afirmando hechos falsos para el estado actual (main, e120277, merge hecho). Corrección: marcar esas secciones explícitamente como "estado de preparación (histórico)" o reescribirlas con el estado actual, y añadir una línea con el HEAD vigente `e120277` y los dos padres del merge.

**2. `.kiro/specs/local-runtime-mvp/requirements.md` R1.1 y `tasks.md` T01: la tarea sigue describiendo restricciones ya incumplidas por la excepción.**
T01 dice "No hacer staging/commit antes de revisión aprobada", "rama y HEAD sin cambios durante la preparación" y R1.6 "recuperar archivos no incorpora los 13 commits al historial". La excepción de Git está anotada al margen, pero los criterios de aceptación de T01 ya no pueden cumplirse literalmente (rama y HEAD cambiaron). Corrección: reformular el criterio de aceptación para evaluar el estado consolidado (por ejemplo: "main contiene foundation como ancestro, árbol limpio, 11 archivos idénticos a foundation") en lugar de seguir exigiendo HEAD inalterado. R1.6 debe actualizarse igual.

**3. `AGENTS.md`: reglas de flujo en conflicto.**
Dice "Sin push… no crear ni cambiar a otras ramas" y a la vez que T01 se recupera "sin merge ni checkout… los commits foundation no se incorporan al historial". La excepción posterior lo contradice sin reemplazarlo. Un agente futuro que lea la primera frase vería violado su propio repo. Corrección: integrar la excepción en la regla (texto vigente: "foundation está incorporada en main; T01 aún sin marcar") y dejar la regla antigua solo como contexto histórico.

**4. Riesgo de commit de cierre ambiguo.**
AGENTS y tasks.md indican "commit `T01: …` solo tras aprobación", pero el árbol ya está commiteado. Debe aclararse qué es el commit de cierre: probablemente uno que solo marque `[x]` en tasks.md y registre la revisión. Corrección: especificarlo, para evitar que alguien interprete e120277 como el commit de T01.

**5. `docs/estado-revision-t01.md`: obsoleto respecto de esta petición.**
Dice "No reintentar la revisión" y que el paquete de referencia es una instantánea anterior. El propio usuario reactivó la revisión. Corrección: actualizar el estado (revisión reactivada, alcance = e120277) y registrar el resultado de esta revisión, sin tratarla como aprobación hasta que el dictamen sea APROBADO.

## Hallazgos menores y de seguridad (documentar, no bloquean por sí solos)

**6. `docs/setup-windows.md` y README: el aviso "Un clon de `main` no contiene… sin commit"** ya es falso tras el merge. Corregir.

**7. Deuda heredada en `cli.py`/`store.py` (documentada correctamente, pero con matices):**
- `doctor` hace una petición HTTP a `127.0.0.1:9889` (lectura, loopback) y sigue proxies del entorno por defecto en `urlopen`; es inofensivo hacia loopback pero contradice el criterio futuro "sin proxies implícitos". Anotarlo en la deuda para T02 en lugar de heredar el patrón en `providers`.
- `store.py` importa `core` dentro de `create` (acoplamiento circular encubierto) y los errores salen en inglés. Ya declarado como deuda; la redacción es honesta.
- `route` en CLI usa `vars(plan)`; sin riesgo de seguridad, solo notar que depende de la forma del objeto.
- `--actor` no autentica: la documentación lo dice claramente y es correcto. La regla de que `advance` exige reviewer designado distinto del worker depende solo de strings declaradas; el README ya lo advierte.

**8. `.gitignore`:** correcto y consistente (`.nexus/`, `.build/`, `.env*`, `*.sqlite3`). Sin objeciones. Sugerencia: confirmar que `.build/` nunca contuvo secretos antes del respaldo (el texto afirma que no se leyeron).

**9. CI heredado:** el README dice "CI recuperado, sin nueva ejecución remota". Es honesto; no se debe presentar como verde.

## Lo que está bien (verificado contra el texto)

- Distinción clara entre recuperado, conservado y planeado (tablas del README y structure.md); T02, ComfyUI, OpenCode y CAO figuran como pendientes, sin funciones inexistentes aprobadas.
- Compatibilidad CLI/SQLite/catálogo/tests: el diseño de T02 es aditivo, no toca `tasks`/`events`, y prohíbe duplicar `CREATE TABLE` en la consola.
- Seguridad: prohibición explícita de `stop.sh`, `shutdown --all`, `kill-server`; scripts CAO descritos como no validados y sin ejecutar; instrucciones dentro de archivos tratadas como datos.
- La deuda de estilo/tipado/mensajes se documenta sin afirmar que esté corregida, y se exige para código nuevo.
- Los mensajes del orquestador no se usan como dictamen.

## Resumen de correcciones mínimas para aprobar

1. Actualizar `conciliacion-local` (secciones de procedencia y verificación) al estado consolidado.
2. Reformular criterios de aceptación de T01 y R1.6 para el estado main fusionado.
3. Unificar la regla de Git en AGENTS.md.
4. Definir en tasks.md cuál es el commit de cierre de T01.
5. Actualizar `estado-revision-t01.md` y la advertencia de `setup-windows.md`.

Con eso, y siempre que las 15 pruebas y la identidad byte a byte con foundation se mantengan, no veo obstáculos técnicos para aprobar T01.