# Producto: JASP Nexus

JASP Nexus es una herramienta personal para coordinar trabajo de desarrollo y generación visual con proveedores locales y, cuando estén disponibles, agentes comerciales. CAO sigue siendo un motor externo posible, sin fork; el primer flujo local debe funcionar sin depender de Claude ni de CAO.

## Dirección autorizada el 23 de octubre de 2026

El usuario aprobó la propuesta de `docs/revision-local-2026-10-23.md` con «sigamos tu propuesta». Se conserva el trabajo local y se recupera el contenido de foundation (`8683b6568ff026cb957866225115743b8b01d4f8`). La spec activa es `local-runtime-mvp`; `nexus-console` queda pospuesta.

Posteriormente pidió reunir el historial y los cambios en una sola rama: se consolida todo en `main` mediante commits de conservación y merge local. Esta operación de Git no cierra T01 ni sustituye su revisión externa, que sigue pospuesta. No se publica en GitHub como efecto de la consolidación.

Orden único: **conexión local real → agente acotado → ComfyUI → orquestación y consola**. T01 concilia documentación y recupera código existente; no implementa conexiones ni inicia agentes.

## Usuario y entornos

Un desarrollador que habla español. El entorno prioritario es Windows 11 con WSL2 y proyectos en `C:\laragon\www` (`/mnt/c/laragon/www`). La base portable y sus comprobaciones en macOS se conservan. Cada host mantiene sus datos, autenticación y sesiones independientes; no existe continuidad multi-host.

## Estado observable

- Recuperado: CLI `doctor/create/list/show/route/history/advance`, routing determinista simulado, tareas y eventos de transición en SQLite, catálogo JSON y 15 pruebas unitarias.
- `route` no ejecuta agentes ni comprueba disponibilidad, login o cuotas. El campo `--actor` no autentica una revisión.
- Conservado como trabajo local: perfiles CAO, scripts, política YAML y diseño de consola. No son evidencia de un sistema de agentes funcionando.
- Pendiente: conexión a LM Studio, modelos descubiertos, chat real, agente acotado, integración ComfyUI, contrato CAO, monitor de cuota y consola.

## Resultados buscados

1. Descubrir servicios y modelos locales, hacer una petición de chat acotada y registrar resultado medido sin ejecutar herramientas del modelo.
2. Ensayar un agente en un repositorio descartable, con archivos permitidos, límites y pruebas originales protegidas; verificar proceso, diff y pruebas antes de revisión humana.
3. Integrar generación visual con ComfyUI y artefactos comprobables.
4. Integrar CAO solo tras verificar su API; construir la consola sobre un flujo real reutilizando la CLI y persistencia existentes.

La revisión humana es un criterio del futuro flujo local; no sustituye la revisión de otro proveedor exigida para cerrar las tareas de construcción de este repositorio.

## Principios y límites

- Local: todo servidor propio escucha solo en `127.0.0.1`; no exponer CAO, PTY ni terminales hacia afuera.
- La política determinista decide asignación y límites. Un mensaje del modelo no acredita finalización ni aprobación.
- Español en documentación, interfaz y mensajes nuevos; identificadores de código en inglés.
- Sin multiusuario, login, despliegue público, aplicación Electron/Tauri ni sincronización de SQLite entre hosts en este MVP.
- No instalar todos los proveedores como prerrequisito del flujo local. No fijar como requisito el modelo del experimento externo.
