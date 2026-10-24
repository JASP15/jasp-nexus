# Roadmap de JASP Nexus

Dirección autorizada el 23 de octubre de 2026 mediante la propuesta de [revisión local](revision-local-2026-10-23.md). La fuente ejecutable es [.kiro/specs/local-runtime-mvp/tasks.md](../.kiro/specs/local-runtime-mvp/tasks.md); este documento no marca tareas por sí mismo.

1. **T01 — Conciliación y compatibilidad.** Recuperar la base foundation, preservar trabajo local y alinear documentación. Código recuperado, cierre pendiente de revisión cruzada.
2. **T02 — Conexión local real.** Configuración explícita LM Studio/ComfyUI, detección, modelos, chat acotado y metadatos medidos. Sin agentes ni herramientas del modelo.
3. **H3 — Agente acotado.** Ensayar OpenCode en repositorio descartable con archivos permitidos, pruebas originales protegidas, límites, evidencia y revisión humana. Falta detallar diseño y tareas antes de ejecutar.
4. **H4 — ComfyUI.** Generación visual con workflows explícitos y artefactos verificables. Pendiente.
5. **H5 — Orquestación y consola.** Política determinista, revisión según proveedor efectivo, contrato CAO real y UI sobre flujos funcionales. La spec nexus-console queda pospuesta.

La base actual tiene routing simulado y SQLite. No hay agentes locales autónomos, cuota medida, continuidad multi-host ni consola. La migración de CLI, backend de empaquetado o ubicación de datos no forma parte de T01/T02.

Se conserva la portabilidad Windows/WSL2 y macOS. Handoff, control remoto, leasing y sincronización entre hosts siguen fuera del MVP local; no sincronizar SQLite con Git o carpetas compartidas.

Este orden sustituye el piloto CAO como primer paso del roadmap foundation. Su contenido anterior se conserva en el commit fuente y en la copia local de procedencia.
