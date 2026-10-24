# Windows y WSL2: estado del trabajo local

**Actualizado el 23 de octubre de 2026.** La spec activa es [local-runtime-mvp](../.kiro/specs/local-runtime-mvp/tasks.md). La guía anterior mezclaba instalación de todos los proveedores con scripts locales aún sin commit. La copia íntegra anterior está en `.build/reconcile-2026-10-23/originals/docs/setup-windows.md`.

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

Un clon de `main` no contiene automáticamente esta conciliación sin commit ni los scripts locales. No cambiar de rama siguiendo una guía histórica. Las guías foundation [WSL2](WINDOWS_WSL2.md) y [macOS](MACOS.md) se conservaron como referencia de su etapa; no sustituyen este estado ni la spec activa.
