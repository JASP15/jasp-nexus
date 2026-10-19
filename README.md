# JASP Nexus

Capa personal y modular de coordinación multiagente. Basada en CAO de AWS Labs como motor externo.

**Estado: base 0.1, sin ejecutar agentes.** El comando nexus route crea un plan lógico, no utiliza créditos ni ejecuta ningún proveedor.

## Componentes de esta base
- CLI de diagnóstico (lee localhost:9889/health) y gestión de tareas.
- Routing determinista: Claude o Codex como coordinador; trabajadores y revisores intercambiables.
- SQLite con transiciones, historial y limite de correcciones.
- Catálogo configurable de agentes, tests y GitHub Actions.
- Instrucciones de instalación Windows/WSL2 y límites de seguridad.

## Prueba local
Consulta docs/WINDOWS_WSL2.md; una vez en Python 3.11+ y dentro del checkout de este repositorio:

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -e .
    nexus doctor
    nexus create --title "Maquetar RSVP" --kind visual --complexity 1 --quality 3
    nexus list
    nexus route ID_DE_LA_TAREA

No existe conexión automática con CAO. El enrutamiento no comprueba la disponibilidad real de CLIs, suscripción ni cuotas.

## Referencias
- docs/ARCHITECTURE.md
- docs/SECURITY.md
- docs/ROADMAP.md
- docs/WINDOWS_WSL2.md
- AGENTS.md

CAO: https://github.com/awslabs/cli-agent-orchestrator (Apache-2.0, software externo). La licencia del código propio de Nexus sigue pendiente de decisión.
