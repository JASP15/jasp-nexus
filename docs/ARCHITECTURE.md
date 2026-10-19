# JASP Nexus — Arquitectura

CAO es un proceso independiente; no vendoreamos su código ni hacemos un fork. CAO ofrece CLI, API HTTP, MCP, tmux y Web UI. JASP Nexus mantiene decisiones de rol, calidad y seguimiento de tareas en su propia SQLite.

La versión 0.1 solo soporta routing SIMULADO basado en especialidades, complejidad, calidad y costo relativo. No observa cuotas ni inicia agentes. Claude o Codex pueden coordinar. Kiro y Command Code figuran como trabajadores lógicos; Command Code requiere adaptador propio y OpenRouter se integraría en una fase posterior como API.

Estados: backlog -> assigned -> running -> in_review -> approved o changes_requested. El rechazo permite una nueva asignación hasta el límite. El almacén conserva eventos auditables.

Para sesiones reales usaremos los IDs del servidor CAO y registraremos el vínculo tarea/ejecución, pruebas y artifacts. El cambio de coordinador necesitará una lease de liderazgo exclusiva, versión de estado y paquete de handoff. Ninguno de esos mecanismos está implementado todavía.

El argumento --actor de la CLI no se autentica. Es un registro de revisión, no autorización de seguridad. Los niveles de calidad y costo son parámetros configurados, no resultados de benchmarks.

## Soporte dual Windows + macOS

CAO corre en un proceso POSIX local: Ubuntu/WSL2 en casa y macOS nativo en el trabajo. Nexus es Python 3.11+ portable; CI verifica ambos sistemas. Los CLI y sus credenciales se configuran por host. No asumir que una autenticación de escritorio Windows está disponible en WSL ni que la sesión de Mac existe en la PC.

Cada instalación actual usa CAO y SQLite locales; **no** sincronizar el archivo SQLite por Git, Drive o carpetas compartidas. El diseño futuro multi-host contempla un registro seguro de nodos, almacén persistente central, leases de coordinador, IDs de ejecución namespaced por host, transporte autenticado y reconciliación idempotente. Esto aún no está implementado. Ver docs/MULTI_HOST.md.
