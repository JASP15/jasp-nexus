# T02: revisión del orquestador (Claude), ronda 2

**Dictamen: sin defectos bloqueantes en el alcance revisado. No es revisión cruzada de proveedor.**

## Limitación de gobernanza

Kiro implementó con el modelo Claude Opus 5.5 y el orquestador es Claude, de modo que esta revisión no procede de un proveedor distinto del implementador efectivo (`AGENTS.md`). El usuario decidió mantener el trabajo entre el orquestador y Kiro, sin Codex. Esta decisión no modifica `AGENTS.md`: la casilla de T02 y el commit de cierre siguen requiriendo que el usuario acepte expresamente esta excepción.

## Alcance revisado

Corrección de la ronda 1 de Codex: `src/jasp_nexus/local_http.py`, `tests/local_fakes.py`, `tests/test_local_http.py`.

- Un único plazo total cubre conexión, TLS, envío, cabeceras y cuerpo; cada operación bloqueante solo recibe el tiempo restante.
- Hallazgo de Codex resuelto: pruebas deterministas de entrega lenta (cuerpo y cabeceras) que fallan con `local_http.py` de HEAD y pasan con la corrección.
- Cuerpo más corto que `Content-Length` se rechaza como `CONNECTION_ERROR`, con prueba.
- Sin proxies ni redirecciones: `http.client` no lee proxies y las respuestas 3xx se rechazan sin leer el cuerpo.

## Verificación

- WSL: `PYTHONPATH=src python3 -m unittest discover -s tests`: 54 pruebas correctas. `git diff --check` sin errores.

## Pendiente (no declarado como superado)

- Ruff no está instalado: lint y formato sin verificar.
- La ruta HTTPS solo se probó con un script ad hoc (servidor mudo y servidor HTTP plano), no con pruebas de la suite.
- Aceptación real providers → models → chat contra LM Studio: pendiente.

## Cierre

El 5 de noviembre de 2026 el usuario aceptó expresamente cerrar T02 con esta revisión interna, sin revisor de otro proveedor. Queda registrado como excepción de esa decisión, no como aprobación cruzada. Siguen pendientes la aceptación real con LM Studio y la verificación con ruff.
