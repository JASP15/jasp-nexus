# Requisitos: JASP Nexus Local Runtime MVP

**Spec activa desde el 23 de octubre de 2026.** Autorización: el usuario respondió «sigamos tu propuesta» al informe `docs/revision-local-2026-10-23.md`. La dirección acordada es conexión local real → agente acotado → ComfyUI → orquestación y consola. Esa aprobación no equivale a revisión técnica ni a tener estas funciones implementadas.

## R1. Conciliación y compatibilidad (T01)

**Estado vigente tras la consolidación autorizada:** `main` contiene foundation y el trabajo local en el merge `e120277e7930b77766f81201fa08cac6b79be1fd`. Las restricciones anteriores de recuperación sin merge y HEAD inalterado son históricas. La consolidación no aprueba T01 ni modifica la revisión exigida en R4.3.

- **R1.1** Verificar que foundation `8683b6568ff026cb957866225115743b8b01d4f8` es ancestro de `main`, que se conservó el trabajo local y que los 11 archivos enumerados en T01 son idénticos byte a byte al commit fuente. El árbol debe estar limpio antes de las correcciones y después del commit de cierre; durante la revisión solo contendrá las correcciones documentales inventariadas. No hacer push ni cambiar de rama.
- **R1.2** Respaldar cada archivo local antes de modificarlo y registrar procedencia y hashes. La recuperación inicial consta en `.build/reconcile-2026-10-23/`, la consolidación en `.build/git-consolidation-2026-10-23/` y las correcciones de revisión en `.build/review-t01-main-e120277/round2-originals/`. No leer ni copiar secretos.
- **R1.3** Mantener Python 3.11+, argparse, setuptools, librería estándar, unittest, entrypoint `cli:main`, comandos existentes, `--agents`, `--db` y `.nexus/state.sqlite3`.
- **R1.4** Conservar `TaskStore`, tablas `tasks/events`, IDs, estados, historial y límite de intentos. No abrir ni migrar bases de usuario durante la conciliación.
- **R1.5** Alinear AGENTS, steering, README y specs; posponer `nexus-console` y sustituir sus instrucciones de recrear CLI/SQLite por extensiones compatibles.
- **R1.6** Distinguir capacidades recuperadas, planes y evidencia real. Los 13 commits foundation están incorporados mediante el merge de conservación `e120277`; este no constituye aprobación técnica ni cierre de T01. La recuperación selectiva sin incorporar historial describe únicamente la etapa anterior.

## R2. Primera conexión local real (T02, pendiente)

- **R2.1** Añadir comandos `providers`, `models` y `chat` a la CLI actual sin cambiar el comportamiento de comandos anteriores ni requerir CAO o proveedores comerciales.
- **R2.2** Aceptar configuración JSON sin secretos para URLs de LM Studio y ComfyUI y timeouts finitos. Defectos: `http://127.0.0.1:1234/v1` y `http://127.0.0.1:8188`. Un loopback inaccesible desde WSL debe dar un diagnóstico útil; no cambiar el bind de servidores ni abrir puertos automáticamente.
- **R2.3** Permitir solo loopback o una dirección privada numérica del host WSL declarada explícitamente. Rechazar credenciales embebidas, query, fragmento, redirecciones y proxies implícitos. No descubrir direcciones mediante shell ni leer variables de entorno para conexiones.
- **R2.4** `providers` debe reportar por servicio qué se comprobó, resultado y duración. Una URL configurada o puerto abierto no demuestra servicio saludable, autenticación, cuota o disponibilidad de modelos. Usar únicamente comprobaciones HTTP de lectura documentadas; errores de un servicio no impiden informar del otro.
- **R2.5** `models` debe devolver los IDs reales publicados por LM Studio. Una lista vacía es un resultado válido y distinto de conexión fallida. La presencia en la lista no demuestra que un modelo esté cargado (puede existir carga JIT).
- **R2.6** `chat` debe exigir un ID elegido de la lista descubierta y una petición explícita, enviar una sola solicitud no streaming y limitar timeout, tamaño de respuesta y tokens solicitados. No seleccionar un modelo fijo ni reintentar silenciosamente.
- **R2.7** Distinguir en español conexión rechazada, timeout, error HTTP, JSON inválido, respuesta inesperada, lista vacía y modelo no anunciado. Una respuesta válida muestra el texto al usuario y registra métricas observadas. Si no se informa consumo de tokens, registrarlo como desconocido.
- **R2.8** No ejecutar herramientas del modelo, comandos, agentes, scripts de instalación, workflows de ComfyUI ni acciones CAO. T02 prueba comunicación; el agente corresponde a un hito posterior.

## R3. Evidencia de ejecución (T02, pendiente)

- **R3.1** Guardar metadatos de petición y eventos de inicio/resultado en tablas nuevas, con identificador de ejecución, servicio, operación, modelo cuando aplique, hora UTC, duración, estado y categoría de error. No confundirlos con transiciones de tareas.
- **R3.2** No guardar prompts, respuestas del chat, cuerpos de errores externos, tokens de autenticación, cabeceras, variables de entorno ni archivos del usuario en SQLite/logs.
- **R3.3** Registrar solo métricas observadas; no inventar éxito, tiempos, token usage ni disponibilidad. La pérdida del proceso puede dejar ejecución sin resultado y nunca debe mostrarse como éxito.
- **R3.4** La ampliación de SQLite debe ser aditiva e idempotente, preservando filas y comportamiento de `tasks/events`. Probar con una base anterior temporal; no migrar datos reales como efecto de las pruebas.

## R4. Calidad y cierre

- **R4.1** La base recuperada debe superar sus 15 pruebas y un recorrido CLI con base temporal. No confundir esos resultados con funcionamiento de servicios locales.
- **R4.2** T02 debe tener pruebas deterministas de cliente HTTP, errores, límites y persistencia, sin exigir modelos reales. Validar aparte la petición real cuando LM Studio esté disponible; si no lo está, registrar el bloqueo y no declarar completada la aceptación real.
- **R4.3** Una tarea de construcción solo se marca y permite commit después de revisión por un proveedor distinto del implementador. Si no está disponible, queda pendiente; no aprobarse a sí mismo ni sustituirlo tácitamente por revisión humana.
- **R4.3a** La excepción de conservación Git ya ejecutada no cierra T01. Tras dictamen externo **APROBADO**, su commit de cierre incluirá las correcciones documentales revisadas, la casilla `[x]` y el registro del dictamen y alcance, con las verificaciones en verde. No se reutiliza `e120277` como commit de tarea.
- **R4.4** No implementar hitos posteriores antes de cerrar su predecesor y detallar/validar su diseño. Conservar español, seguridad de AGENTS y comandos de verificación aplicables.

## Hitos posteriores (aún sin criterios ejecutables)

- **H3 — Agente acotado:** evaluar OpenCode en repositorio descartable con archivos permitidos, pruebas originales protegidas, límites de tiempo e intentos, diffs y revisión humana del resultado.
- **H4 — ComfyUI:** generación visual con workflow y entradas explícitos, seguimiento de ejecución, cancelación propia y artefactos verificados.
- **H5 — Orquestación y consola:** política determinista, contrato CAO real, revisión cruzada según implementador real, recuperación y UI sobre los flujos ya comprobados.

Estos hitos no autorizan instalaciones, ejecución autónoma ni cambios de scripts en T01/T02.
