# Puesta en marcha — macOS (equipo de trabajo)

**No se ha instalado nada en tu Mac.** Sigue este documento solamente si las políticas de tu trabajo permiten instalar y utilizar estas herramientas con el código correspondiente.

CAO soporta macOS de forma nativa, sin Docker ni WSL2. Puedes usar Claude Code y Codex como coordinadores locales. La versión 0.1 de Nexus **NO** lanza agentes.

## Requisitos

- Mac Intel o Apple Silicon con Homebrew disponible.
- Python 3.11+ para Nexus; CAO exige Python 3.10+.
- tmux 3.3+ y uv.
- Git, y las CLI que quieras ejecutar, instaladas/autenticadas en macOS.

Abre Terminal y, si tienes permiso de instalación:

    brew install git tmux uv python@3.12
    tmux -V
    uv --version
    python3.12 --version

Si ya tienes esas versiones, omite la instalación. La documentación de CAO es la fuente de verdad de los prerrequisitos: https://awslabs.github.io/cli-agent-orchestrator/

## CAO externo

Instala inicialmente mediante la guía oficial (el ejemplo sigue upstream main; para reproducibilidad conviene fijar luego una versión/tag):

    uv tool install git+https://github.com/awslabs/cli-agent-orchestrator.git@main
    cao --help
    cao install code_supervisor

En una ventana de Terminal:

    cao-server

Abre http://localhost:9889 y http://localhost:9889/health. Mantén el servicio en localhost. Esto no inicia automáticamente ningún agente.

Antes de lanzar sesiones, consulta docs/SECURITY.md: ciertos perfiles de CAO pueden usar flags de permisos amplios. Verifica perfiles restrictivos en un repositorio de prueba y no utilices --yolo ni --dangerously-skip-permissions en proyectos reales.

## Nexus

En otra ventana:

    git clone https://github.com/JASP15/jasp-nexus.git
    cd jasp-nexus
    git switch feat/foundation-cao-mvp
    python3.12 -m venv .venv
    source .venv/bin/activate
    python -m pip install -e .
    nexus doctor
    nexus create --title "Prueba en macOS" --kind visual --complexity 1 --quality 3
    nexus list

Para probar routing simulado: nexus route ID_DE_TAREA. No comprueba cuota, login ni ejecuta CLIs.

Cuando se integren adaptadores reales, instala y autentica cada CLI nativa siguiendo la guía del proveedor. La configuración y tokens de tu Windows/WSL2 NO se transfieren automáticamente.

## Estado en equipos distintos

Cada host tiene su propia base .nexus/state.sqlite3 y sus sesiones CAO. No copies bases SQLite activas entre hosts; no subas credenciales al repositorio. Consulta docs/MULTI_HOST.md para el plan de continuidad entre casa y trabajo.
