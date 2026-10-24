# Tareas: JASP Nexus Local Runtime MVP

**Plan activo desde el 23 de octubre de 2026**, por autorización del usuario a la propuesta del informe local. Ejecutar una tarea a la vez, en orden. Una casilla se marca solo después de verificación y aprobación de un revisor de otro proveedor. No confundir aprobación de la dirección con revisión de la implementación.

## Trabajo detallado

**Consolidación Git autorizada después de la preparación:** el usuario pidió una sola rama local con todo fusionado. La operación permite respaldar, guardar cambios en commits de conservación, incorporar el historial foundation y continuar desde `main`; es una excepción a las restricciones Git de preparación de T01. No cambia sus casillas ni aprueba técnicamente la tarea. La revisión externa sigue pospuesta y T02 sigue pendiente.

- [ ] **T01. Conciliación de foundation y compatibilidad** (R1.*, R4.1, R4.3)
  - Conservar rama, HEAD, índice y cambios locales durante la preparación; recuperar únicamente archivos seguros ausentes del commit `8683b6568ff026cb957866225115743b8b01d4f8`: paquete, tests, catálogo JSON, pyproject, CI y documentos foundation.
  - Copiar originales seguros antes de cambiarlos a `.build/reconcile-2026-10-23/originals/`; registrar hashes y procedencia en manifiesto. No copiar secretos.
  - Conciliar AGENTS, steering, README y gitignore; documentar deuda heredada y estado real de capacidades.
  - Crear esta spec y dejar `nexus-console` pospuesta. Adaptar sus T02/T04 y diseño para ampliar la CLI/SQLite existentes sin reemplazo.
  - Registrar la procedencia sin afirmar que se incorporaron los commits foundation al historial.
  - No implementar T02, corregir scripts de arranque/parada, instalar herramientas, iniciar proveedores ni hacer staging/commit antes de revisión aprobada.
  - Verificar desde raíz WSL/POSIX: `PYTHONPATH=src python3 -m unittest discover -s tests -v`; `PYTHONPATH=src python3 -m jasp_nexus.cli --help`; `git diff --check`.
  - Verificar además: hashes de archivos foundation de código/config/tests/CI idénticos al commit fuente; originales respaldados íntegros; smoke de create → route → show/history/list en base temporal (sin proveedores); rama y HEAD sin cambios durante la preparación.
  - Aceptación: documentación coherente, 15 pruebas existentes y smoke aprobados; revisión cruzada registrada. Mantener esta casilla vacía hasta esa revisión.

- [ ] **T02. Conexión local real y evidencia medida** (R2.*, R3.*, R4.2–R4.4)
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
