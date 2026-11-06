# T02: revisión Codex, ronda 1

**Dictamen: cambios solicitados.** Revisión de la entrega de Claude incorporada en `e6a9731`; no constituye aprobación ni aceptación real de T02.

## Hallazgo

El transporte comprueba el plazo total antes de cada llamada a `HTTPResponse.read`, pero dicha llamada puede esperar mientras el servicio entrega bytes paulatinamente dentro del timeout de socket. Por tanto, una respuesta lenta puede superar el plazo total configurado, en contra de `local-runtime-mvp/design.md`, sección de errores y límites. El mismo riesgo debe considerarse durante la recepción de cabeceras. Corregir con una prueba determinista de entrega lenta que acredite un plazo total finito, sin proxies ni redirecciones.

## Verificación y pendientes

- En WSL, `PYTHONPATH=src python3 -m unittest discover -s tests -v`: 51 pruebas correctas.
- `python -m jasp_nexus.cli --help` y `git diff --check`: correctos.
- Ruff no estaba disponible en el PATH de WSL en esta revisión; no se declara verificado.
- La aceptación real `providers → models → chat` sigue pendiente; la entrega anterior registra conexión rechazada. No se iniciaron proveedores.
- La documentación principal y steering describen T02 como aún no implementada, aunque existe una entrega en `e6a9731`. Conciliar el estado al cerrar la tarea, sin atribuirle aceptación no demostrada.

La corrección debe volver a verificarse y revisarse antes de marcar T02. La consola y los hitos posteriores siguen pospuestos conforme a la spec activa.
