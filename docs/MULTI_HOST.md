# Estrategia multi-host — Windows (casa) y macOS (trabajo)

## Objetivo de producto

Permitir usar JASP Nexus en **dos estaciones ejecutoras**:
- Windows doméstico: Ubuntu dentro de WSL2 + CAO y las CLIs instaladas dentro de Ubuntu.
- Mac del trabajo: CAO y CLIs nativas de macOS.

Ambos hosts deben poder coordinar, trabajar, revisar y recuperar tareas. Ninguno será relegado a un cliente móvil.

## Situación real de 0.1

- Nexus funciona como CLI local, su asignación de roles es simulada.
- CAO tiene una UI web local en cada host, independiente.
- Las tareas se guardan en una SQLite local en .nexus/.
- Clonar Git en otro equipo copia el código, NO traslada el SQLite, las sesiones activas, los tokens de los proveedores ni el workspace in-memory.
- No hay asignación remota de tareas, continuidad de conversación entre hosts, sincronización de cuotas o arbitraje global de líder.
- No usar Dropbox/iCloud/Drive/Git para sincronizar bases SQLite en vivo o carpetas de credenciales.

## Evolución propuesta, no implementada

Fase A: operación dual independiente, mismo código y configuración declarativa (sin secretos).
Fase B: paquete de handoff exportable con tareas, criterios de aceptación, commits, diffs relevantes, artefactos aprobados y eventos de revisión, siempre excluyendo secretos y datos no autorizados.
Fase C: backend persistente compartido, identidad de host, IDs de tareas globales, autorización por proyecto, cifrado TLS, almacenamiento de artefactos y leases con epoch para garantizar **un solo coordinador por proyecto**.
Fase D: nodos ejecutores capaces de recibir asignaciones de forma segura; reconciliación, deduplicación e idempotencia al perder conexión.

## Decisión importante

No se debe publicar un CAO de WSL2/Mac con bind 0.0.0.0 o abrir sus puertos sin autenticación y autorización. Una eventual red privada/VPN no sustituye la autorización por tarea, el registro de auditoría ni el control de permisos.

**Mac de empresa**: no usar automáticamente repositorios personales, credenciales privadas ni enviar código corporativo a servicios externos. Revisar políticas de la organización y separar ámbitos personal/profesional.

## Ensayo de aceptación futuro

1. Registrar un proyecto y tarea en PC.
2. Transferir estado mediante mecanismo autenticado, sin subir SQLite ni tokens.
3. Continuar en Mac y obtener el mismo ID lógico de tarea, con nuevo ID de ejecución/host.
4. Verificar que nunca hay dos coordinadores autorizados para ese proyecto.
5. Simular pérdida de red, reintentos y rollback; verificar que no se duplican los merges.
6. Auditar quién inició, revisó y aprobó cada etapa.

No declarar continuidad real entre hosts hasta superar este ensayo.
