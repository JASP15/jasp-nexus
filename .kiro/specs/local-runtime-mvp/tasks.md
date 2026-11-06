# Tareas: JASP Nexus Local Runtime MVP

**Plan activo desde el 23 de octubre de 2026**, por autorización del usuario a la propuesta del informe local. Ejecutar una tarea a la vez, en orden. Una casilla se marca solo después de verificación y aprobación de un revisor de otro proveedor. No confundir aprobación de la dirección con revisión de la implementación.

## Trabajo detallado

**Estado vigente:** la consolidación Git autorizada incorporó foundation y el trabajo local en `main`, merge `e120277e7930b77766f81201fa08cac6b79be1fd`. Los criterios siguientes evalúan ese estado y las correcciones documentales; la recuperación sin merge y HEAD inalterado es histórica. T01 obtuvo APROBADO de Claude en ronda 2, con comprobaciones de cierre satisfactorias; véase `docs/revisiones/local-runtime-mvp-t01.md`. T02 se cerró con revisión interna del orquestador (excepción aceptada por el usuario, no cruzada por proveedor); su aceptación real contra LM Studio sigue pendiente. Véase `docs/revisiones/local-runtime-mvp-t02-claude-ronda-2.md`.

- [x] **T01. Conciliación de foundation y compatibilidad** (R1.*, R4.1, R4.3)
  - Conservar `main` y comprobar que foundation `8683b6568ff026cb957866225115743b8b01d4f8` es ancestro del merge `e120277`; mantener el trabajo local incorporado. No repetir la recuperación ni cambiar de rama.
  - Conservar los respaldos originales de recuperación y consolidación. Copiar los documentos seguros antes de corregirlos a `.build/review-t01-main-e120277/round2-originals/`; registrar hashes y procedencia en manifiesto. No copiar secretos.
  - Conciliar AGENTS, steering, README y gitignore; documentar deuda heredada y estado real de capacidades.
  - Crear esta spec y dejar `nexus-console` pospuesta. Adaptar sus T02/T04 y diseño para ampliar la CLI/SQLite existentes sin reemplazo.
  - Registrar la procedencia y distinguir recuperación histórica, consolidación Git y cierre técnico tras aprobación externa. El merge de conservación no aprueba T01.
  - Limitar las correcciones de revisión a documentación: no implementar T02, corregir scripts de arranque/parada, instalar herramientas ni iniciar proveedores. No hacer staging/commit de cierre antes del dictamen externo APROBADO.
  - Verificar desde raíz WSL/POSIX: `PYTHONPATH=src python3 -m unittest discover -s tests -v`; `PYTHONPATH=src python3 -m jasp_nexus.cli --help`; `git diff --check`.
  - Verificar identidad byte a byte de estos 11 archivos con foundation: `.github/workflows/ci.yml`, `config/agents.example.json`, `pyproject.toml`, `src/jasp_nexus/__init__.py`, `src/jasp_nexus/cli.py`, `src/jasp_nexus/core.py`, `src/jasp_nexus/platform_support.py`, `src/jasp_nexus/store.py`, `tests/test_core.py`, `tests/test_platform_support.py` y `tests/test_store.py`.
  - Verificar además: originales respaldados íntegros; smoke create → route → show/history/list en base temporal (sin proveedores); foundation ancestro de `main`; árbol limpio antes de corregir y, durante revisión, únicamente cambios documentales inventariados.
  - Aceptación: documentación coherente, 11 archivos idénticos, 15 pruebas y smoke aprobados; dictamen externo APROBADO con alcance registrado. Mantener esta casilla vacía hasta ese dictamen.
  - Cierre tras aprobación: commit `T01: Foundation reconciliation and compatibility` con las correcciones documentales revisadas, esta casilla `[x]` y registro del dictamen/alcance; identificar `local-runtime-mvp` en el cuerpo. Verificar árbol limpio después del commit. `e120277` es el merge de conservación, no este cierre; no hacer push.

- [x] **T02. Conexión local real y evidencia medida** (R2.*, R3.*, R4.2–R4.4)
  - Añadir configuración JSON validada para LM Studio y ComfyUI, timeouts y límites finitos; comandos `providers/models/chat` con argparse y librería estándar.
  - Consultar documentación oficial vigente de los endpoints de lectura; validar IDs reales de LM Studio y hacer chat no streaming sin herramientas ni agentes.
  - Tratar loopback/host WSL explícito, errores, redirecciones, proxies, respuestas inesperadas y límites según diseño.
  - Añadir metadatos/eventos de ejecución mediante tablas SQLite nuevas, sin afectar tareas/eventos foundation ni guardar contenido de mensajes o errores externos.
  - Mantener compatibilidad de CLI, catálogo JSON, `--db`, `TaskStore` y comandos anteriores. Incorporar configuración de ruff para código nuevo/modificado y resolver su verificación sin refactor global encubierto.
  - Pruebas: éxito, servicio caído, timeout, JSON/esquema incorrecto, respuesta demasiado grande, URL inválida, no redirección/proxy, lista vacía/modelo ausente, métricas opcionales, SQLite anterior poblada y ausencia de payloads en historial.
  - Verificar: `PYTHONPATH=src python3 -m unittest discover -s tests -v`; lint/format de los archivos nuevos o modificados con ruff; `git diff --check`; regresión CLI con base temporal.
  - Aceptación real separada: con LM Studio disponible y un modelo anunciado, ejecutar providers → models → chat de prueba y comprobar metadatos en base temporal. Si no responde, registrar impedimento; no declarar aceptación real superada.
  - Prohibido: iniciar agentes, ejecutar herramientas del modelo, instalar proveedores, lanzar workflows ComfyUI o depender de CAO.

## Hitos posteriores: deben detallarse antes de ejecución

- **H3. Agente acotado en repositorio de prueba:** evaluar OpenCode, permisos y archivos permitidos, límites de tiempo/intentos, protección de tests originales, evidencia de proceso/diff/pruebas y revisión humana.
- **H4. Generación visual con ComfyUI:** workflow explícito, validación, seguimiento y artefactos comprobables.
- **H5. Orquestación y consola:** contrato CAO real, política determinista y revisión por proveedor distinto del implementador efectivo, corrección de scripts pendientes y reactivación compatible de `nexus-console`.

Los hitos no son tareas aprobadas ni instrucciones para ejecutarlas ahora. Definir requisitos, diseño, verificación y orden concretos antes de convertir cada hito en tareas.
