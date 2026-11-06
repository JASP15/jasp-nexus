# T02: entrega para revisión (local-runtime-mvp)

**Implementador:** Claude (Anthropic), 23 de octubre de 2026, en `main` sobre `8f98514`. **Estado:** pendiente de revisión por un proveedor distinto (Codex/GPT). Sin casilla `[x]` ni commit hasta su dictamen.

## Corrección ronda 1 (pendiente de nueva revisión)

5 de noviembre de 2026, sobre `e6a9731` (commit «update», que contiene esta entrega y coincide con `origin/main`). Atiende el [dictamen de Codex, ronda 1](local-runtime-mvp-t02-codex-ronda-1.md), que pidió cambios y no se ha modificado. Los cambios no tienen commit y T02 sigue sin marcar. Kiro (modelo Claude Opus 5.5, Anthropic) hizo el transporte y la comprobación de longitud; el orquestador (Claude) añadió las pruebas de goteo. Como todo procede de Anthropic, la revisión corresponde a otro proveedor (Codex/GPT). Esta sección sustituye la descripción de `local_http.py` del apartado «Alcance implementado»: ya no es cierto que el peor caso sea el plazo más un timeout de socket.

- **Plazo total.** `timeout_seconds` limita todo el intercambio desde el inicio de la petición, con reloj monotónico. Cada operación bloqueante recibe como timeout solo el tiempo restante: la conexión a cada dirección resuelta, el handshake TLS, cada envío y cada `recv` de la línea de estado, las cabeceras y el cuerpo. Si no queda tiempo, falla con `timeout` antes de volver a esperar, así que un servicio que entrega bytes poco a poco ya no alarga la espera.
- **Transporte.** `local_http.py` usa `http.client` directamente en lugar de `urllib`. `http.client` no consulta proxies del entorno ni sigue redirecciones; un 3xx sigue dando `redirect` sin leer el cuerpo. Se retiran `build_local_opener` y el parámetro `opener` de `request_json`, que no usaba ningún módulo ni prueba.
- **Cuerpo truncado.** Si hay `Content-Length` y llegan menos bytes, el resultado es `connection_error` («Respuesta incompleta»). Antes, un cuerpo parcial que fuera JSON válido se aceptaba como éxito.
- **Sin cambios:** límites de configuración, `max_response_bytes` (declarado y por flujo), categorías de error, mensajes sin cuerpo remoto, códigos de salida, comandos, `--db`, tablas SQLite y ausencia de dependencias.

Pruebas nuevas en `tests/test_local_http.py`, apoyadas en `Route.drip_interval` y `drip_headers` de `tests/local_fakes.py`:

- `test_trickled_body_respects_total_deadline` y `test_trickled_headers_respect_total_deadline`, del orquestador: el servidor envía un byte cada 0,1 s y, con plazo de 0,5 s, se exige `timeout` en menos de 1,5 s. Según el orquestador, fallan con el `local_http.py` de `e6a9731`.
- `test_truncated_body_is_not_success`: declara 100 bytes y envía 2, sin esperas.

Verificación:

- WSL Ubuntu 24.04, Python 3.12.3: `PYTHONPATH=src python3 -m unittest discover -s tests -v` da 54 pruebas OK.
- Comprobaciones manuales en loopback, con un script fuera de la suite (`.build/`, ignorado por Git) y plazo de 0,5 s. Un servidor que acepta TCP y no responde da `timeout` a los 0,51 s por HTTP y durante el handshake HTTPS. Un POST de 64 MiB a un servidor que no lee da `timeout` a los 0,51 s. `localhost` funciona contra un servicio en 127.0.0.1, y HTTPS contra un servidor HTTP plano da `connection_error`.
- No verificado: ruff (no está instalado en WSL ni en Windows, y no se instaló), Python 3.11, Windows nativo, `nexus --help` y `git diff --check` de esta ronda. Solo se comprobó a mano que `local_http.py` no tiene líneas de más de 100 caracteres ni espacios finales.

Limitaciones:

- La resolución de `localhost` (`getaddrinfo`) queda fuera del plazo; las demás URLs admitidas usan IP numéricas.
- Entre operaciones pueden sumarse milisegundos de CPU sobre el plazo.
- El lector acotado depende de dos detalles no documentados de `http.client`: el atributo `response_class` y el lector `HTTPResponse.fp`. Existen en CPython 3.11 a 3.13, pero solo se ha ejecutado 3.12.
- HTTPS solo se ha probado sin certificado válido; falta una prueba con TLS completo.
- Ante una respuesta incompleta (`connection_error`), la CLI puede mostrar la pista de red de WSL aunque el servicio haya respondido.
- La aceptación real sigue pendiente y no se inició ningún proveedor. README y steering se concilian al cerrar T02.

## Alcance implementado

- `config/local.example.json` y `src/jasp_nexus/local_config.py`: JSON validado con claves cerradas. Límites: `timeout_seconds` de 0,1 a 300, `max_response_bytes` de 1024 a 16 MiB y `max_tokens` de 1 a 8192. Se aceptan URLs `http`/`https` hacia loopback (`127.0.0.0/8`, `::1`, `localhost`) o hacia una IP privada numérica declarada en `allowed_private_hosts`. Se rechazan credenciales, query, fragmento, hosts por nombre y puertos inválidos.
- `src/jasp_nexus/local_http.py`: `urllib` con `ProxyHandler({})`, que ignora proxies del entorno o del registro, y con redirecciones convertidas en error. La lectura está limitada por bytes, tanto por `Content-Length` como por flujo. El plazo total se comprueba entre bloques, por lo que el peor caso es el plazo más un timeout de socket. Los errores se clasifican en categorías estables y nunca se copia el cuerpo remoto.
- `src/jasp_nexus/local_services.py`:
  - LM Studio: `GET /v1/models` (`data[].id`) y `POST /v1/chat/completions` con `stream=false` y `max_tokens`, sin `tools`.
  - ComfyUI: `GET /system_stats`, cuyo objeto debe incluir `system` y `devices`. Una raíz que responde 200 no basta.
- `src/jasp_nexus/local_runs.py`: tablas nuevas `local_runs` y `local_run_events`, creadas de forma idempotente. No tienen columnas de prompt, respuesta, cuerpo, cabeceras ni URL. Una ejecución que quede en `running` se presenta como `no_confirmado`. El `task_id` es opcional, se valida y no altera `tasks/events`.
- `src/jasp_nexus/local_cli.py` y un enganche de 5 líneas en `cli.py`: opción global `--local-config` y comandos `providers`, `models`, `chat --model --prompt [--max-tokens] [--task-id]` y `runs [--limit]`. Códigos de salida: 0 éxito, 2 entrada o configuración inválida (incluido un modelo no anunciado, sin enviar la petición) y 3 servicio o transporte.
- `pyproject.toml`: configuración de ruff. Se excluyen los archivos heredados, incluido `cli.py`, cuya única modificación es el enganche.

## Decisiones para el revisor

1. **`runs`** no figura en R2.1. Se añadió porque el diseño exige mostrar como no confirmado lo que quedó en `running`, y para comprobar metadatos sin herramientas externas.
2. **`cli.py` queda fuera de ruff.** Normalizarlo supondría tocar código heredado (tipado, imports, formato), y AGENTS exige para eso alcance y revisión propios. Las líneas nuevas son las del diff.
3. **`chat`** registra primero una ejecución `models` para el descubrimiento y después la ejecución `chat`. Si el modelo no está anunciado, la ejecución `chat` queda `failed/model_not_announced` con `model_id` nulo.
4. **Pista para WSL:** ante un fallo de red hacia loopback en WSL, el error sugiere activar el modo de red mirrored o declarar la IP del host. No se ejecutan comandos para descubrirla.

## Verificación ejecutada

- WSL Ubuntu 24.04, Python 3.12.3: `PYTHONPATH=src python3 -m unittest discover -s tests -v` da 51 pruebas OK (15 foundation y 36 nuevas). `python3 -m jasp_nexus.cli --help` y `git diff --check` también pasan.
- ruff 0.14.0, instalado en un venv temporal fuera del repositorio: `ruff check .` y `ruff format --check .` pasan sobre los archivos no excluidos.
- Windows nativo, Python 3.13: las 36 pruebas nuevas pasan. Las 5 de `test_store.py` (foundation) fallan al borrar el directorio temporal porque `TaskStore` no cierra sus conexiones SQLite (WinError 32). Es deuda heredada, fuera de la matriz CI Linux/macOS, y no se corrige aquí.

## Aceptación real: no superada

El 23/24 de octubre de 2026 (UTC 03:54) se ejecutó `providers` y `models` con base temporal y `config/local.example.json`. LM Studio y ComfyUI respondieron `connection_refused` en `127.0.0.1:1234` y `127.0.0.1:8188`. Los metadatos `failed/connection_refused` quedaron registrados. No se inició ningún proveedor. Queda pendiente repetir providers → models → chat con LM Studio en marcha y un modelo anunciado.
