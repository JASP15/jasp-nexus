# JASP Nexus

Herramienta personal y modular para coordinar agentes de desarrollo de software.

> Estado: inicialización del repositorio. La implementación se construye en ramas de trabajo mediante pull requests.

## Objetivo

Aprovechar [CLI Agent Orchestrator (CAO)](https://github.com/awslabs/cli-agent-orchestrator) como motor externo para Claude Code, Codex y Kiro, y agregar política propia de asignación, revisión y recuperación de tareas sin mantener un fork del motor.

**Seguridad:** ningún agente ni proveedor se ejecuta automáticamente desde este repositorio. El uso de credenciales y los permisos de ejecución se configuran localmente.
