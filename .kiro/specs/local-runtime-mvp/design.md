# Diseño: JASP Nexus Local Runtime MVP

## Decisiones de conciliación (T01)

**Estado vigente tras la consolidación autorizada:** foundation y trabajo local ya están incorporados en `main`, merge `e120277e7930b77766f81201fa08cac6b79be1fd`. T01 obtuvo APROBADO de Claude en ronda 2 tras las correcciones documentales de ronda 1. El procedimiento y respaldo constan en `docs/consolidacion-git-2026-10-23.md`; el cierre se registra en `docs/revisiones/local-runtime-mvp-t01.md`.

La recuperación selectiva inicial desde foundation `8683b6568ff026cb957866225115743b8b01d4f8`, sin cambiar HEAD, índice ni rama, es una etapa histórica. La revisión actual verifica foundation como ancestro de `main` y los 11 archivos de T01 idénticos al origen, junto con compatibilidad y respaldo del trabajo local. Los originales de recuperación están en `.build/reconcile-2026-10-23/originals/`; las correcciones actuales tienen copia y manifiesto en `.build/review-t01-main-e120277/round2-originals/`.

Solo tras dictamen externo APROBADO y verificaciones satisfactorias se hará el commit de cierre con las correcciones documentales revisadas, la casilla y el registro del dictamen/alcance. El árbol estaba limpio antes de estas correcciones y debe quedar limpio tras ese commit. El merge de conservación no cierra T01.

La base se mantiene intacta: setuptools, argparse, librería estándar, unittest, `nexus = "jasp_nexus.cli:main"`, `TaskStore` y `.nexus/state.sqlite3`. El JSON de agentes alimenta routing simulado; `routing.yaml` se conserva como política de perfiles CAO y no sustituye al JSON. No se introducen migraciones de CLI ni de datos.

`nexus-console` permanece como diseño pospuesto. Su T02 debe ampliar el paquete existente y su T04 reutilizar `TaskStore` mediante tablas complementarias, nunca ejecutar un segundo `CREATE TABLE tasks/events` incompatible.

## Estado actual

La CLI crea tareas, propone roles y registra transiciones; no autentica actores ni ejecuta agentes. El coordinador lógico todavía se restringe a Claude/Codex. Esto no bloquea el futuro chat directo: T02 no usa `route` para hablar con LM Studio.

Los mensajes ingleses y falta de tipado/formato de la base son deuda heredada visible, conservada para que T01 sea una recuperación verificable. Código nuevo o modificado debe seguir AGENTS; no introducir un refactor general en esta tarea.

`doctor` usa `urlopen` con proxies de entorno y redirecciones por defecto. Se conserva como deuda heredada; T02 debe implementar y probar transporte sin proxies implícitos ni redirecciones, sin copiar ese patrón.

## Ampliación prevista T02 (no implementada por T01)

Flujo: **CLI argparse → configuración/validación → cliente HTTP estándar → LM Studio o comprobación de ComfyUI → metadatos en SQLite**.

Separar parseo/presentación de CLI, validación de configuración, transporte HTTP y persistencia. Añadir módulos pequeños según necesidad; no un framework de agentes. Mantener los tests actuales y usar unittest con servidor HTTP efímero de loopback o transporte inyectado. No añadir dependencias de ejecución.

### Configuración y comandos

Ejemplo propuesto `config/local.example.json`:

```json
{
  "lm_studio_url": "http://127.0.0.1:1234/v1",
  "comfyui_url": "http://127.0.0.1:8188",
  "timeout_seconds": 30,
  "max_response_bytes": 1048576,
  "max_tokens": 512
}
```

Validar números positivos y finitos, con límites superiores documentados antes de implementar. Configuración explícita por `--local-config`; no leer `.env`, almacenes de credenciales ni proxies de entorno. Mantener `--db` y `--agents` existentes. Nuevos comandos previstos:

- `providers`: comprobaciones HTTP de lectura independientes por servicio; resultado y latencia. Para ComfyUI, verificar primero el endpoint y respuesta en documentación oficial; no asumir que raíz HTTP 200 acredita API ni encolar workflows.
- `models`: `GET /v1/models`, IDs exactamente como los publica el servidor.
- `chat --model ID --prompt TEXTO`: descubrir/validar el ID y realizar una sola llamada a `POST /v1/chat/completions` con `stream=false` y límite explícito de tokens. El texto solo se imprime al usuario; no se persiste.

URLs permitidas: loopback o dirección privada numérica del host WSL declarada por el usuario. Validar esquema HTTP/HTTPS, destino y forma antes de pedir; no seguir redirecciones, no usar proxies implícitos ni ejecutar comandos para localizar servicios. T02 no cambia binds ni configuración de servidores. Ante conexión rechazada, explicar servicio y URL esperada sin volcar credenciales o cuerpo remoto.

La lista de modelos contiene modelos visibles y puede incluir modelos descargados que se cargan bajo demanda. No mostrar “cargado” por inferencia ni elegir el modelo del experimento anterior como defecto. Una lista vacía se muestra como tal; `chat` falla antes de enviar la petición si el modelo no está anunciado.

### Tiempo, errores y métricas

Timeout de red y plazo total finitos; limitar lectura por bytes para evitar respuestas indefinidas. La salida parcial, JSON inválido, HTTP no satisfactorio o esquema inesperado no se considera éxito. Clasificar errores sin copiar cuerpos remotos al historial y usar códigos de salida estables: 0 éxito, 2 entrada/configuración inválida, 3 error de servicio/transporte. En `providers`, emitir todos los resultados aunque uno falle; salir 3 si alguna comprobación falla.

Medir duración con reloj monotónico y marcas temporales UTC. Consumo de tokens opcional solo si el servidor devuelve valores válidos; campo nulo si no existe. Sin estimaciones de VRAM, velocidad, coste, cuota o calidad derivadas de un simple ping.

### Persistencia aditiva

No modificar ni renombrar las tablas `tasks` y `events`, ni sus APIs. Añadir tablas con nombres propios, por ejemplo `local_runs` y `local_run_events`, mediante creación idempotente. Una ejecución de comunicación no necesita tarea de routing ni cambia sus estados. Puede vincularse opcionalmente mediante task_id a una tarea existente; validar ese ID si se proporciona, sin exigir route ni alterar estados.

Metadatos previstos: ID, servicio/operación enumerados, ID de modelo validado cuando aplique, inicio/fin UTC, duración, estado `running/succeeded/failed`, categoría de error, código HTTP y uso de tokens opcional. Eventos: inicio y resultado con campos permitidos. No columnas de payload libre, prompts, respuestas ni cuerpos de errores. La ejecución que quede en `running` tras cierre abrupto no se interpreta como éxito; la presentación debe indicar resultado no confirmado.

Pruebas con base temporal de esquema foundation poblada: conservar filas e historial, abrir repetidamente sin duplicados, registrar éxito/fallo, omitir contenido sensible y no corromper estados por errores de red.

### Fuentes para T02

- [LM Studio: modelos compatibles con OpenAI](https://lmstudio.ai/docs/developer/openai-compat/models).
- [LM Studio: chat completions](https://lmstudio.ai/docs/developer/openai-compat/chat-completions).
- El contrato de ComfyUI se comprueba en sus fuentes oficiales durante T02; la ejecución de workflows pertenece a H4.
- CAO no participa en T02. Su futura integración exige `docs/cao/contract.md`.

## Límites de hitos posteriores

H3 detallará aislamiento, permisos, proceso, diff y pruebas originales antes de ejecutar un agente. H4 detallará workflows, artefactos y seguimiento ComfyUI. H5 validará CAO y reactivará la consola con una política coherente. No definirlos como implementados ni ejecutar sus scripts durante la conciliación.

La revisión humana del resultado del futuro agente local y la revisión cruzada de tareas de construcción son controles distintos: se conserva la segunda para cerrar cualquier Tnn de este repositorio.
