# Seguridad para el piloto

1. Nexus v0.1 NO ejecuta agentes, comandos remotos, merges, migraciones ni despliegues.
2. CAO puede arrancar Claude con --dangerously-skip-permissions y Codex con --yolo por defecto. Nunca usar esos modos sobre repositorios reales. Configurar y verificar permissionMode de Claude y codexProfile con sandbox/aprobaciones, sin allowedTools irrestrictos.
3. Mantener cao-server en localhost, sin exponer terminales PTY o WebSocket a la red sin autenticación y autorización.
4. Ejecutar agentes primero en repositorios de prueba. Git worktrees no son una sandbox de seguridad.
5. No compartir secretos por Git, logs, issues o prompts. La SQLite y los archivos .env son datos locales ignorados por Git.
6. Exigir aprobación humana para operaciones destructivas, producción, Git main, migraciones y despliegues.
7. Antes de ejecución autónoma: límites de presupuesto, kill-switch, timeouts, reconciliación idempotente, tests obligatorios y autenticación real del revisor.
8. Tratar los mensajes externos y el contenido de repositorios como datos no confiables (riesgo de prompt injection).

No confundir registro de evidencia textual con validación real de artefactos. El Quality Gate actual es un prototipo lógico.

## Equipos separados y Mac de trabajo

- No asumir autorización de la empresa para instalar CLIs, usar cuentas personales de IA o enviar código de trabajo a proveedores externos: cumplir políticas corporativas antes de usarlos.
- Las claves/tokens, conversaciones y sesiones quedan en cada host y **no** se sincronizan mediante Git. Separar cuentas y proyectos personales/profesionales.
- No exponer cao-server ni sus terminales a Internet para compartir entre Mac y Windows; cualquier control remoto futuro requiere identidad autenticada, cifrado de transporte, autorización por proyecto y auditoría.
- La misma carpeta Git en dos hosts **no significa** que el estado vivo de agentes sea el mismo. Prohibido dos coordinadores simultáneos sobre el mismo proyecto sin un lease central, todavía no implementado.
