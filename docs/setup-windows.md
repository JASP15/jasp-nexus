# Windows y WSL2: estado del trabajo local

> **Sin vigencia desde el 6 de noviembre de 2026.** Esta guía describe la línea CAO, retirada por la [decisión del 6 de noviembre](decision-2026-11-06.md); la spec activa es `multi-provider-orchestrator` y la guía de entorno vigente es [setup-wsl.md](setup-wsl.md). No ejecutar los scripts que menciona. Se archiva en F5.

**Actualizado el 23 de octubre de 2026.** En esa fecha la spec activa era [local-runtime-mvp](../.kiro/specs/local-runtime-mvp/tasks.md). Foundation y scripts locales están guardados en `main`, base consolidada `e120277`; T01 obtuvo [APROBADO externo en ronda 2](revisiones/local-runtime-mvp-t01.md). La copia de la guía anterior a la conciliación está en `.build/reconcile-2026-10-23/originals/docs/setup-windows.md`.

## Probar el checkout actual

El entorno principal es Ubuntu en WSL2. No es necesario instalar ni autenticar CAO, Claude, Codex o Kiro para probar la base Python recuperada.

Desde `/mnt/c/laragon/www/jasp-nexus`, con Python 3.11+:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m jasp_nexus.cli --help
```

La [página principal](../README.md) incluye un ensayo de tareas con SQLite descartable. Aún no existen los comandos `providers/models/chat`; T02 los añadirá. La conexión real a LM Studio y ComfyUI no está validada. Que un servicio escuche en Windows no garantiza que el mismo loopback sea alcanzable desde WSL; la configuración explícita y su diagnóstico corresponden a T02, sin abrir servicios a la red automáticamente.

## Scripts CAO conservados, pendientes de revisión

`scripts/setup-wsl.sh`, `install-profiles.sh`, `start.sh` y `stop.sh` se preservan como trabajo previo. No se ejecutaron ni corrigieron durante T01. No usar esta guía como receta de instalación o arranque de agentes.

Los hallazgos de la [revisión local](revision-local-2026-10-23.md) siguen pendientes: `start.sh` puede anunciar éxito sin salud confirmada; el respaldo de perfiles puede seleccionar un revisor del mismo proveedor; `stop.sh` hace una parada global. **No ejecutar `scripts/stop.sh`, `cao shutdown --all`, `nexus down --all` ni `tmux kill-server`: pueden terminar sesiones ajenas.**

La instalación/integración CAO se retomará tras el flujo local y validación de su contrato. En ese momento habrá que verificar la versión, perfiles, permisos y propiedad de las sesiones. Una CLI instalada o autenticada en Windows no implica que exista en WSL.

## Distribución y otros equipos

La `main` local contiene la conciliación y los scripts conservados desde `e120277`, más el cierre documental revisado de T01. Los cambios no se han publicado: un clon de GitHub solo recibirá lo que exista en el remoto. Continuar en `main`; no cambiar de rama siguiendo una guía histórica. Las guías foundation [WSL2](WINDOWS_WSL2.md) y [macOS](MACOS.md) se conservaron como referencia de su etapa; no sustituyen este estado ni la spec activa.
