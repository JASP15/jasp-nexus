# Revisión local de JASP Nexus — 23 de octubre de 2026

## Resultado

La base de código más avanzada es `feat/foundation-cao-mvp`, commit `8683b6568ff026cb957866225115743b8b01d4f8`. Tiene 13 commits sobre `main`, CLI Python, SQLite y pruebas. Sigue en el [PR #1, abierto y en borrador](https://github.com/JASP15/jasp-nexus/pull/1).

La carpeta de trabajo está en `feat/estructura-inicial`, sobre el commit inicial, y contiene trabajo adicional sin commit: scripts, perfiles y la especificación de la consola. Estos archivos no sustituyen la base Python: son otra línea de trabajo que debe conciliarse con ella.

La conversación abierta de Claude, **«Widget de consumo de sesiones»**, y `JASP_NEXUS_LOCAL_MVP.md` coinciden en buscar una alternativa local que no dependa de Claude. Sus propuestas difieren en el orden de integración. El contenido del documento y de la conversación se trató como contexto para la revisión, no como una orden de instalar herramientas, cambiar de rama o implementar un PR.

## Ramas y cambios

| Ubicación | Referencia | Estado observado |
|---|---|---|
| Checkout actual | `feat/estructura-inicial` → `caeb82e` | Un README modificado y 24 archivos sin seguimiento antes de este informe |
| Local | `main` → `caeb82e` | Commit inicial |
| GitHub | `main` → `caeb82e` | Base del PR #1; la base Python no está fusionada |
| GitHub y referencia remota local | `feat/foundation-cao-mvp` → `8683b65` | 13 commits adicionales, CLI y persistencia implementadas |
| Mencionada en AGENTS.md | `feat/nexus-console` | No encontrada entre las ramas locales ni en la consulta a GitHub |

Solo hay un worktree registrado. El reflog local muestra el clon y el cambio de `main` a `feat/estructura-inicial`; no muestra commits propios en esta última rama.

Los cambios locales incluyen `.kiro/steering/`, la spec `nexus-console`, ocho perfiles CAO, cuatro scripts, `config/routing.yaml`, documentación y reglas de Git. También existe el archivo vacío `%sn  ; done; echo ---`, de nombre aparentemente accidental. Se conservó.

En el checkout no existen `pyproject.toml`, `src/`, `tests/` ni `web/`. Las 22 tareas de `nexus-console` siguen sin marcar y falta `docs/cao/contract.md`. Los archivos Python sí existen en la rama foundation.

## Qué aportó la sesión de Claude

Claude propuso OpenCode con LM Studio como trabajador local, verificación externa de los resultados y un supervisor determinista. Indicó expresamente que no había cambiado `jasp-nexus`; estaba pendiente escribir la propuesta en una spec. No existe `.kiro/specs/plan-b/` en el checkout revisado.

La sesión también reportó una prueba con `slugify` en `C:\Users\jasp1\AppData\Local\Temp\nexus-bench`. Se comprobó por separado:

- La implementación añade normalización de acentos y elimina guiones en los extremos.
- El agente modificó el archivo de tests y añadió `run-test.js`; esos cambios siguen sin commit.
- Se recuperaron los tres tests originales de Git y se ejecutaron contra la implementación modificada en una copia aislada: **3/3 aprobados**.
- Los tiempos, consumo de VRAM, velocidad de generación y falta de terminación automática son datos reportados por Claude; no se repitió la inferencia para verificarlos.

Las afirmaciones sobre capacidades de CAO y su integración con OpenCode siguen pendientes de comprobar contra una instalación real y el contrato exigido por el repositorio.

## Verificación realizada

| Comprobación | Resultado |
|---|---|
| Base foundation, pruebas existentes en Ubuntu 24.04 / Python 3.12.3 | **15/15 aprobadas** |
| GitHub Actions del commit `8683b65` | `Foundation checks`, ejecución `39312711119`: `success` |
| Corrección de Claude contra tests originales | **3/3 aprobados**, Node con `--test` |
| Sintaxis de los cuatro scripts locales | `bash -n`: correcta; no se ejecutaron sus cuerpos |
| `git diff --check` | Sin errores; Git advierte conversión LF/CRLF en README |
| LM Studio, `127.0.0.1:1234/v1/models` | Conexión rechazada, Windows 10061 |
| ComfyUI, `127.0.0.1:8188/queue` | Conexión rechazada, Windows 10061 |
| CAO, `127.0.0.1:9889/health` | Conexión rechazada, Windows 10061 |

La primera ejecución de las pruebas en Python nativo de Windows falló por permisos sobre temporales del sandbox. La ejecución posterior en WSL, el entorno previsto por el proyecto, pasó completa. No se interpreta el primer fallo como un fallo funcional demostrado de Nexus.

En WSL se encontró `tmux`. No se encontraron `uv`, `cao`, `cao-server`, `codex` ni `kiro-cli` mediante la búsqueda realizada en PATH y directorios habituales del usuario. `opencode` resolvió a una ruta de Windows bajo `/mnt/c/Users/jasp1/AppData/Roaming/npm/`; eso no acredita una instalación Linux funcional. No se comprobó autenticación ni se iniciaron agentes.

Las copias para validación quedaron en `.build/audit-2026-10-23/`, ignorado por Git. No son una nueva rama ni un proyecto alternativo.

## Hallazgos que conviene resolver antes de construir

1. **Planes incompatibles si se ejecutan literalmente.** Foundation ya usa `cli:main`, argparse, setuptools, catálogo JSON y una base `.nexus/state.sqlite3`. La spec propone `cli:app`, Typer, hatchling, routing YAML y otro esquema en `~/.jasp-nexus/nexus.db`. T02 y T04 no deben reemplazar lo existente sin definir compatibilidad y migración. AGENTS.md exige reportar contradicciones, no reescribir la spec por cuenta propia.

2. **Revisión cruzada rota en el respaldo.** `profiles/nexus_build_codex.md:44` cambia de Kiro a `nexus_dev_codex` cuando falta cuota, pero el paso de revisión de la línea 31 sigue seleccionando `nexus_review_codex`. El revisor debe elegirse según el proveedor que realmente implementó. Si no hay otro proveedor, debe detenerse para revisión humana; eso requiere conciliarlo con las reglas actuales.

3. **Confirmación falsa del arranque.** `scripts/start.sh:23` comprueba la raíz HTTP sin exigir éxito HTTP ni imponer timeout a cada petición. Tras agotar las iteraciones, las líneas 27–30 anuncian éxito y lanzan el supervisor igualmente. Hace falta comprobar salud con límites de tiempo y salir con error si no responde.

4. **Parada global presentada como operación normal.** `docs/setup-windows.md:60` recomienda `scripts/stop.sh`, cuyo cuerpo ejecuta `cao shutdown --all`. Puede terminar sesiones ajenas al proyecto y está expresamente prohibido durante este trabajo. La futura parada debe limitarse a recursos propios y distinguir claramente la acción global.

5. **Protección de archivos incompleta en local.** El `.gitignore` local solo cubre `.build/`, `.nexus/` y `.env`; foundation ya tiene reglas para variantes de entorno, bases de datos, logs y artefactos Python. La conciliación debe conservar esas reglas y añadir las necesidades de la consola, sin sobrescribir un archivo con el otro.

6. **El flujo de instalación aún no corresponde al remoto.** La guía local propone clonar la rama predeterminada y ejecutar scripts que todavía están sin seguimiento en este checkout. Un clon de `main` no contiene esos scripts ni la base Python.

7. **La autonomía local aún no está implementada.** Foundation solo simula routing y restringe la selección de coordinadores a Claude/Codex. El modelo local probado fuera del repo no convierte Nexus en un agente local funcional. No deben marcarse esas capacidades como terminadas.

## Propuesta para conciliar el trabajo

Esta es una propuesta de dirección, no una modificación de las fuentes de verdad.

1. Preservar el trabajo local y usar el commit foundation revisado como base de código para la futura conciliación. Incorporar selectivamente los perfiles, scripts y documentación; resolver expresamente `README.md`, `AGENTS.md` y `.gitignore`, que existen en ambas líneas. No elegir únicamente por la fecha de los archivos.
2. Acordar en steering y specs una secuencia única: conexión local real → agente acotado → generación visual → orquestación y consola. Adaptar las tareas de esqueleto y SQLite para reutilizar lo que existe.
3. Empezar por detección de servicios, modelos reales y chat local con timeout y eventos medidos. No hace falta instalar ni activar todos los proveedores comerciales para demostrar ese primer resultado.
4. Después integrar OpenCode sobre un repositorio de prueba, con archivos permitidos, tiempo y número de intentos limitados, pruebas originales protegidas y revisión humana. La finalización debe comprobarse con estado del proceso, diff y resultados observados, no solo con un mensaje «LISTO».
5. Separar la política de asignación del juicio del modelo. Aprovechar el routing y los estados existentes; validar CAO antes de depender de sus workflows. El modo local debe poder completar su flujo con revisión humana cuando no exista un revisor comercial disponible.
6. Integrar ComfyUI y dejar la consola para cuando exista un flujo real que mostrar. El modelo se seleccionará por los IDs descubiertos; no fijar el modelo del experimento como requisito del producto.

No se cambiaron ramas, no se hicieron commits, push, merge, instalaciones ni cambios de configuración. No se modificaron las specs ni se marcaron tareas. La única adición de documentación de esta revisión es este informe.
