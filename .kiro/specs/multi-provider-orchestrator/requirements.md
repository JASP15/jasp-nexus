# Requisitos: JASP Nexus Multi-Provider Orchestrator

**Spec activa desde el 6 de noviembre de 2026.** El usuario aprobó el plan del orquestador multi-proveedor ([decisión y procedencia](../../../docs/decision-2026-11-06.md)). Sustituye a `local-runtime-mvp` (cerrada) y reemplaza a `nexus-console` (su fase F4). Esa aprobación autoriza la dirección y el orden de tareas; no equivale a revisión técnica ni a tener estas funciones implementadas.

Cada requisito tiene un id (`R<n>.<m>`) que citan las tareas de [tasks.md](tasks.md). «DEBE» indica obligación verificable; «NUNCA DEBE», prohibición. El diseño está en [design.md](design.md).

## Glosario

- **Proveedor:** CLI o servicio que ejecuta trabajo de un agente: `claude` (Claude Code), `codex` (Codex CLI), `kiro` (Kiro CLI), `lm_studio` (opcional).
- **Proveedor efectivo:** empresa del modelo que generó el cambio (`anthropic`, `openai`, `local`…), no la CLI que lo ejecutó. Se configura por agente y se registra por ejecución cuando la CLI informa del modelo.
- **Etapa:** `spec` (plan), `implement` (cambio en el repo objetivo), `review` (dictamen), `creative` (texto o propuesta sin cambiar código).
- **Repo objetivo:** repositorio del usuario sobre el que trabaja una tarea; puede ser distinto de este.
- **Artefactos de tarea:** archivos de `.nexus/tasks/<id>/` que transportan el contexto entre etapas (R6.3).

## R1. Adaptadores de proveedores

- **R1.1** Cada proveedor DEBE tener un adaptador que implemente un contrato común: comprobar su estado (`probe`), construir el comando (`build_command`) e interpretar el resultado (`parse`), sin lógica de proceso propia.
- **R1.2** Los procesos DEBEN lanzarse con `subprocess` y lista de argumentos; NUNCA DEBE usarse `shell=True` ni componer comandos como cadena de shell.
- **R1.3** El prompt DEBE enviarse por stdin cuando la CLI lo admita, para que no aparezca en la lista de procesos. Si una CLI solo lo acepta como argumento, DEBE documentarse esa exposición en `docs/providers/<proveedor>.md`.
- **R1.4** El entorno del proceso hijo DEBE construirse desde una lista blanca de **nombres** de variables. Nexus NUNCA DEBE leer, imprimir, registrar ni guardar el valor de esas variables ni de ninguna otra con secretos.
- **R1.5** Cada ejecución DEBE tener un plazo total finito medido con reloj monotónico. Al vencer, Nexus DEBE terminar el grupo de procesos que él mismo inició y clasificar el resultado como `timeout`. stdout y stderr DEBEN acotarse por bytes.
- **R1.6** El resultado DEBE clasificarse en un estado estable (`succeeded`, `failed`, `timeout`, `quota`, `auth`, `not_installed`, `killed`, `invalid_output`) y una categoría de error sin texto remoto. Una salida parcial, un JSON inválido o la falta del evento final NUNCA DEBEN interpretarse como éxito.
- **R1.7** Cuando la CLI lo exponga, el adaptador DEBE devolver el id de sesión del proveedor y permitir reanudarla. Una reanudación fallida DEBE clasificarse como `session_lost` y la etapa DEBE poder continuar con una sesión nueva a partir de los artefactos.
- **R1.8** Los permisos de cada CLI DEBEN fijarse de forma explícita y mínima según la etapa: solo lectura para `spec`, `review` y `creative`; escritura limitada al repo objetivo para `implement`. NUNCA DEBEN usarse modos de permisos irrestrictos (p. ej. `--trust-all-tools`, `danger-full-access`, `--dangerously-skip-permissions`) fuera de un worktree descartable y sin que la tarea lo documente.
- **R1.9** El argv, formato de salida, sesión, permisos y comportamiento ante timeout y falta de login de cada CLI DEBEN basarse en evidencia capturada (fixtures depurados y `docs/providers/*.md`), no en supuestos.
- **R1.10** LM Studio DEBE poder usarse como proveedor opcional, deshabilitado por defecto, solo para etapas de texto (`creative`, `spec`) y sin herramientas, reutilizando la configuración y el transporte local existentes.

## R2. Ejecución individual y métricas

- **R2.1** `nexus run --provider <p>` DEBE ejecutar una etapa sobre un directorio de trabajo con un brief o prompt, imprimir estado, duración, tokens, id de sesión y ruta del artefacto de resumen, y salir con códigos estables: 0 éxito, 2 entrada o configuración inválida, 3 error del proveedor o del proceso.
- **R2.2** Cada ejecución DEBE registrarse en tablas aditivas con proveedor, agente, etapa, inicio y fin UTC, duración, estado, categoría de error, código de salida, id de sesión, tokens, coste si el proveedor lo informa, número de turnos y clave de señal de cuota.
- **R2.3** Solo DEBEN registrarse métricas observadas: tokens, coste y turnos ausentes se guardan como nulos, nunca estimados.
- **R2.4** Una ejecución interrumpida (proceso de Nexus muerto a mitad) DEBE quedar como no confirmada y NUNCA mostrarse como éxito.

## R3. Evidencia y privacidad de datos

- **R3.1** Los datos de ejecución DEBEN separarse de las transiciones de tareas: `provider_runs` y sus eventos no alteran el significado de `tasks`/`events`.
- **R3.2** SQLite y los logs de Nexus NUNCA DEBEN contener prompts, respuestas de los modelos, cuerpos de errores externos, tokens de autenticación, cabeceras, variables de entorno ni archivos del usuario.
  - **Interpretación aprobada con el plan del 6 de noviembre de 2026:** los artefactos de tarea de `.nexus/tasks/<id>/` (`brief.md`, `plan.md`, `summary.md`, `diff.patch`, `files.txt`, `review.md` y, solo con `--keep-raw`, `raw/<run_id>.jsonl`) **son entregables del usuario, no logs**. Viven en disco dentro de `.nexus/` (ignorado por Git), pueden contener texto de los modelos y se borran con `nexus clean <id>`. SQLite solo guarda sus nombres o rutas y hashes, nunca su contenido.
  - Si el usuario revoca esta interpretación, `plan.md`, `summary.md` y `review.md` DEBEN borrarse al aprobar o rechazar la tarea y solo conservarse `diff.patch`.
- **R3.3** Ningún prompt compuesto por Nexus DEBE persistirse; se reconstruye desde los artefactos cuando haga falta.
- **R3.4** La ampliación de SQLite DEBE ser aditiva e idempotente, preservando filas y comportamiento de `tasks`, `events`, `local_runs` y `local_run_events`, y probarse sobre una base anterior poblada en un archivo temporal.

## R4. Disponibilidad, `doctor` y cuota observada

- **R4.1** `nexus doctor [--json]` DEBE mostrar por proveedor: binario encontrado, versión, estado de login, estado (`disponible`, `enfriamiento`, `no_instalado`, `sin_login`), enfriamiento hasta, y tokens y coste acumulados en 5 h y 24 h desde `provider_runs`.
- **R4.2** La comprobación headless real (`--probe`) DEBE ser opcional y explícita, porque consume cuota.
- **R4.3** Nexus DEBE detectar señales de cuota (lista configurable, sin distinguir mayúsculas) en la salida **nueva** de cada ejecución y poner el proveedor en enfriamiento durante `cooldown_minutes`. Solo DEBE guardarse la clave de la señal, no la línea.
- **R4.4** El enfriamiento DEBE vencer solo, persistir entre reinicios y poder restablecerse a mano (`nexus providers reset <p>`).
- **R4.5** Nexus NUNCA DEBE mostrar «cuota restante»: solo uso observado y señales.

## R5. Router y política

- **R5.1** El router DEBE asignar cada etapa recorriendo una lista de preferencias por etapa y excluyendo proveedores deshabilitados, no instalados, sin login o en enfriamiento.
- **R5.2** El revisor DEBE tener un proveedor efectivo distinto del del implementador. Si no hay ninguno disponible, la tarea DEBE quedar `blocked` con la nota «sin revisor cruzado disponible»; NUNCA DEBE autoaprobarse ni sustituirse en silencio por revisión humana.
- **R5.3** La política DEBE vivir en claves aditivas de `config/agents.example.json` (o el `config/agents.json` del usuario), legible con la librería estándar. El formato actual sin claves nuevas DEBE seguir cargando, y `core.load_agents()`, `core.route()` y `nexus route` DEBEN conservar su comportamiento.
- **R5.4** Una política que referencie un proveedor o agente inexistente DEBE rechazarse indicando cuál.

## R6. Pipeline de tarea y aprobación humana

- **R6.1** `nexus run --task <id>` DEBE recorrer las etapas `spec → implement → review` sobre los estados existentes de `TaskStore` y sus transiciones, sin modificar `store.py` ni su máquina de estados.
- **R6.2** Con dictamen CAMBIOS, la tarea DEBE volver a asignarse y reintentarse hasta `max_attempts`; agotado el límite, queda bloqueada para decisión humana.
- **R6.3** El contexto entre proveedores DEBE pasar **solo** por artefactos en disco (R3.2); cada prompt de etapa se compone desde ellos con plantillas en español.
- **R6.4** Con dictamen APROBADO, la tarea DEBE esperar la decisión humana: `nexus approve <id>` o `nexus reject <id> --note`. La decisión DEBE registrarse en una tabla aditiva `approvals`. Solo entonces el pipeline registra `approved` en `TaskStore` en nombre del revisor designado, con nota que identifica el dictamen y la confirmación del operador.
- **R6.5** Un mensaje de un modelo NUNCA DEBE acreditar por sí solo finalización ni aprobación: el dictamen se lee de `review.md` con formato fijo y se contrasta con el diff capturado.
- **R6.6** `nexus status <id>` DEBE mostrar etapas, intentos, proveedores, artefactos y ejecuciones de la tarea.

## R7. Protección del repositorio objetivo

- **R7.1** Antes de implementar, el repo objetivo DEBE tener el árbol limpio, salvo `--allow-dirty` explícito. `--worktree` DEBE permitir trabajar en un `git worktree` propio de la tarea.
- **R7.2** Tras implementar, Nexus DEBE capturar `diff.patch` y `files.txt` con `git` invocado por lista de argumentos.
- **R7.3** Si los archivos cambiados incluyen rutas fuera de las permitidas o pruebas protegidas, el pipeline DEBE forzar `changes_requested` con nota de política, sin invocar la CLI del revisor. Como `TaskStore` solo admite `changes_requested` desde `in_review` y con el revisor designado como actor, el rechazo se registra con dos transiciones válidas: `running → in_review` (actor: implementador; nota con el sha256 del diff y «violación de política») y `in_review → changes_requested` (actor: revisor designado, en cuyo nombre actúa el pipeline; nota «rechazo automático de política; revisor no invocado» con las rutas afectadas). `store.py` no cambia (precisión registrada en `design.md` §10).
- **R7.4** Si el repo objetivo contiene instrucciones para agentes (`CLAUDE.md`, `AGENTS.md`, `.codex/`, hooks), el pipeline DEBE avisarlo en `review.md`; el revisor y la aprobación humana son el control.

## R8. Consola local

- **R8.1** El backend DEBE escuchar únicamente en `127.0.0.1` y rechazar cualquier otra interfaz.
- **R8.2** DEBE rechazar con 403 las peticiones cuyo `Host` no sea `127.0.0.1:<puerto>` o `localhost:<puerto>`, y las peticiones que no sean GET con `Origin` presente y ajeno (reutiliza R2.2–R2.3 de `nexus-console`).
- **R8.3** NUNCA DEBE exponer terminales, PTY ni entrada de teclado hacia los agentes; la salida en vivo es de solo lectura (SSE).
- **R8.4** «Detener» DEBE terminar solo el proceso que Nexus inició para esa tarea.
- **R8.5** La consola DEBE ofrecer panel por proveedor, nueva tarea (incluida la conversión de rutas `C:\…` a `/mnt/c/…`), seguimiento en vivo con artefactos y aprobar/rechazar con confirmación, historial con filtros, edición de política validada y doctor.
- **R8.6** Errores en JSON `{"detail": "..."}` en español; cuerpo de petición limitado por tamaño; API documentada en `docs/api.md`.
- **R8.7** La interfaz DEBE estar en español, funcionar desde 1024 px de ancho y ser usable con teclado (foco visible, formularios etiquetados).

## R9. Calidad, compatibilidad y gobernanza

- **R9.1** Las pruebas automáticas NUNCA DEBEN requerir credenciales, cuota ni CLIs reales: usan una CLI falsa y fixtures depurados. Las pruebas con CLIs reales DEBEN saltarse salvo `NEXUS_E2E=1`.
- **R9.2** Python 3.11+, setuptools, argparse, librería estándar sin dependencias de ejecución, unittest y entrypoint `jasp_nexus.cli:main` DEBEN mantenerse. `uv`, ruff y Node son herramientas de desarrollo.
- **R9.3** El código nuevo o modificado DEBE tener tipado completo, pasar ruff y emitir mensajes en español. La deuda foundation se normaliza en una tarea propia sin cambiar comportamiento.
- **R9.4** Cada tarea DEBE cerrarse solo con dictamen APROBADO de un revisor cuyo proveedor efectivo sea de otra empresa que el del implementador, registrado en `docs/revisiones/mpo-t<nn>-*.md`; sin push; un commit por tarea.
- **R9.5** Los fixtures y documentos de proveedores NUNCA DEBEN contener ids de cuenta, tokens, rutas de credenciales ni rutas personales sin depurar.
- **R9.6** Al terminar la spec, ningún documento vigente DEBE presentar CAO, `routing.yaml`, los perfiles o los scripts CAO como parte del plan; el legado se elimina o archiva con nota de procedencia.

## Fuera de alcance

ComfyUI y generación visual (H4 de `local-runtime-mvp`, no cancelado); CAO y tmux; multiusuario, login propio y despliegue público; aplicación de escritorio; sincronización de SQLite o sesiones entre hosts; «cuota restante» de cualquier proveedor.
