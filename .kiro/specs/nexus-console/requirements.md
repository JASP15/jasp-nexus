# Requisitos: JASP Nexus Console

> **REEMPLAZADA el 6 de noviembre de 2026 por la fase F4 de [multi-provider-orchestrator](../multi-provider-orchestrator/requirements.md)** ([decisión](../../../docs/decision-2026-11-06.md)). No se ejecutan sus tareas: CAO, tmux, perfiles, `routing.yaml`, FastAPI y React quedan fuera del plan. Se conserva como referencia hasta F5/T20, que la archiva en `docs/archivo/`, porque sus requisitos de seguridad local (R2.1–R2.3 y R2.5: bind en `127.0.0.1`, `Host`/`Origin`, sin secretos en logs) y la prohibición de exponer PTY (R2.4) se reutilizan en F4. El texto siguiente es histórico.

**POSPUESTA desde el 23 de octubre de 2026.** La spec activa es `../local-runtime-mvp/`. Estos requisitos describen una etapa futura, no funciones implementadas. Al reactivarla debe conservarse la CLI, datos y pruebas existentes.

Formato: CUANDO <condición>, EL SISTEMA DEBE <comportamiento>. Cada requisito tiene un id (R*.*) que las tareas citan.

## R1. Arranque y ejecutable
- **R1.1** CUANDO el usuario ejecuta `nexus up` en WSL, EL SISTEMA DEBE iniciar `cao-server` en la sesión tmux `nexus-server` si no responde en la URL configurada, iniciar la Consola en `http://127.0.0.1:8765` y abrir el navegador de Windows (salvo `--no-browser`).
- **R1.2** CUANDO `cao-server` ya está corriendo, EL SISTEMA DEBE reutilizarlo y no iniciar otro.
- **R1.3** CUANDO el usuario hace doble clic en `launchers/windows/JASP-Nexus.cmd`, EL SISTEMA DEBE ejecutar `nexus up --no-browser` dentro de WSL, esperar a que el puerto 8765 responda (máximo 60 s) y abrir el navegador predeterminado en la Consola.
- **R1.4** CUANDO el usuario ejecuta `nexus down`, EL SISTEMA DEBE detener solo la Consola. La propuesta anterior de `--all` queda excluida por la prohibición de AGENTS: ninguna parada puede cerrar sesiones ajenas. Cualquier parada futura de recursos CAO debe identificar propiedad por tarea y validarse antes de implementación.
- **R1.5** CUANDO el usuario ejecuta `nexus doctor`, EL SISTEMA DEBE reportar en una tabla el estado de: WSL, tmux (≥ 3.3), uv, node, `claude`, `codex`, `kiro-cli`, `cao`, conexión con CAO y perfiles `nexus_*` instalados, con una sugerencia de arreglo por cada falla.
- **R1.6** SI falta el build del frontend, `nexus up` DEBE terminar con un mensaje que indique correr `scripts/build.sh`.

## R2. Seguridad local
- **R2.1** EL SISTEMA DEBE escuchar únicamente en `127.0.0.1`.
- **R2.2** EL SISTEMA DEBE rechazar con 403 cualquier petición cuyo encabezado `Host` no sea `127.0.0.1:<puerto>` o `localhost:<puerto>` (protección contra DNS rebinding).
- **R2.3** EL SISTEMA DEBE rechazar con 403 las peticiones que no sean GET cuyo `Origin` exista y no coincida con el origen de la Consola.
- **R2.4** EL SISTEMA NUNCA DEBE reenviar la WebSocket PTY de CAO ni exponer endpoints que escriban teclas arbitrarias en terminales de trabajadores. Solo se permite enviar mensajes al supervisor de una tarea creada por la Consola.
- **R2.5** EL SISTEMA NUNCA DEBE registrar en logs ni en la base de datos variables de entorno, tokens ni contenido de archivos `.env`.

## R3. Panel de estado
- **R3.1** EL SISTEMA DEBE mostrar si CAO responde (`/health`) y actualizarlo cada 5 s.
- **R3.2** EL SISTEMA DEBE mostrar una tarjeta por proveedor de `config/routing.yaml` con uno de estos estados: `disponible`, `en enfriamiento hasta HH:MM` (con motivo), `no instalado` (según `/agents/providers` de CAO).
- **R3.3** CUANDO el usuario pulsa "Restablecer" en un proveedor en enfriamiento, EL SISTEMA DEBE marcarlo como disponible.
- **R3.4** EL SISTEMA DEBE listar las tareas activas con proyecto, supervisor, estado y tiempo transcurrido.

## R4. Lanzar tareas
- **R4.1** EL SISTEMA DEBE ofrecer un formulario con: ruta del proyecto (con lista de rutas recientes), supervisor (`nexus_supervisor` o `nexus_build_codex`, con descripción), casilla "Usar git worktree" y la petición en texto libre.
- **R4.2** SI la ruta no existe dentro de WSL, EL SISTEMA DEBE rechazar la tarea con un mensaje claro. SI se pidió worktree y la ruta no está en un repo git, también.
- **R4.3** CUANDO la tarea es válida, EL SISTEMA DEBE crear una sesión en CAO con el perfil de supervisor elegido y el directorio de trabajo indicado, esperar a que el supervisor esté listo para recibir entrada (máximo 120 s), enviarle la petición y guardar la tarea.
- **R4.4** SI CAO falla al crear la sesión o el supervisor no queda listo a tiempo, EL SISTEMA DEBE marcar la tarea como `error` con el detalle devuelto por CAO, y cerrar la sesión creada.
- **R4.5** EL SISTEMA DEBE aceptar rutas de Windows (`C:\laragon\www\x`) y convertirlas a la ruta de WSL (`/mnt/c/laragon/www/x`).

## R5. Seguimiento de tareas
- **R5.1** EL SISTEMA DEBE mostrar, por tarea, el árbol de terminales de su sesión: supervisor y trabajadores, con proveedor, perfil, descripción y estado.
- **R5.2** CUANDO el usuario selecciona una terminal, EL SISTEMA DEBE mostrar su salida reciente con colores ANSI, actualizándola cada 2 s y con desplazamiento automático que se pausa si el usuario sube.
- **R5.3** EL SISTEMA DEBE permitir enviar un mensaje de texto al supervisor de la tarea.
- **R5.4** CUANDO el usuario pulsa "Detener" y confirma, EL SISTEMA DEBE cerrar la sesión de CAO de esa tarea y marcarla como `detenida`.
- **R5.5** CUANDO la sesión de una tarea desaparece de CAO, EL SISTEMA DEBE marcar la tarea como `finalizada`.
- **R5.6** EL SISTEMA DEBE ofrecer un enlace a la Web UI de CAO para la sesión.
- **R5.7** EL SISTEMA DEBE listar el historial de tareas con filtros por estado y proyecto.

## R6. Cuota
- **R6.1** MIENTRAS haya tareas activas, EL SISTEMA DEBE revisar cada 15 s la salida **nueva** de cada terminal y buscar, sin distinguir mayúsculas, las cadenas de `quota_signals`.
- **R6.2** CUANDO detecta una señal, EL SISTEMA DEBE marcar el proveedor de esa terminal en enfriamiento durante `cooldown_minutes` (de `routing.yaml`, 60 por defecto) y registrar el evento con la línea que lo provocó.
- **R6.3** EL SISTEMA DEBE escribir el estado de cuota en `~/.jasp-nexus/state/quota.json` (formato en design.md) cada vez que cambie, para que los supervisores lo lean.
- **R6.4** CUANDO vence el enfriamiento, EL SISTEMA DEBE volver el proveedor a `disponible`.
- **R6.5** EL SISTEMA DEBE conservar el estado de cuota entre reinicios.

## R7. Política de asignación
- **R7.1** EL SISTEMA DEBE mostrar y permitir editar `config/routing.yaml`: orden de `prefer` por tipo de tarea, `quota` por proveedor, revisores, `max_rounds`, `quota_signals` y `cooldown_minutes`.
- **R7.2** SI la política referencia un perfil que no existe en `profiles/`, EL SISTEMA DEBE rechazar el guardado indicando cuál.
- **R7.3** CUANDO guarda, EL SISTEMA DEBE preservar los comentarios del archivo.

## R8. Perfiles
- **R8.1** EL SISTEMA DEBE listar los perfiles de `profiles/` indicando si están instalados en CAO.
- **R8.2** CUANDO el usuario pulsa "Reinstalar perfiles", EL SISTEMA DEBE renderizar y ejecutar `cao install` para cada perfil (misma lógica que `scripts/install-profiles.sh`) y mostrar el resultado por perfil.

## R9. Calidad
- **R9.1** Cada módulo de backend DEBE tener pruebas unitarias; el cliente de CAO se prueba con respuestas reales guardadas en `tests/fixtures/cao/`.
- **R9.2** DEBE existir una prueba e2e (marca `e2e`) que use `cao-server` real con el proveedor `mock_cli` para crear, seguir y detener una tarea.
- **R9.3** La interfaz DEBE funcionar desde 1024 px de ancho y ser usable con teclado (foco visible, formularios etiquetados).
