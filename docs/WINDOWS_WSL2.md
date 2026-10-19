# Puesta en marcha — Windows + WSL2

Estas instrucciones no se han ejecutado en tu PC. Se validarán en un entorno Windows real.

1. En PowerShell como administrador ejecuta: wsl --install -d Ubuntu. Reinicia si Windows lo solicita.
2. En Ubuntu instala herramientas: sudo apt update && sudo apt install -y git curl tmux python3 python3-venv python3-pip
3. Comprueba versiones: tmux -V y python3 --version. CAO requiere tmux 3.3+ y Python 3.10+; Nexus Python 3.11+.
4. Instala uv siguiendo https://docs.astral.sh/uv/getting-started/installation/
5. Instala CAO según su README oficial: uv tool install git+https://github.com/awslabs/cli-agent-orchestrator.git@main
6. Verifica: cao --help. Prepara perfil supervisor: cao install code_supervisor
7. En una terminal Ubuntu inicia cao-server. Visita http://localhost:9889 y http://localhost:9889/health desde Windows.
8. Clona JASP Nexus y dentro de su carpeta inicia: python3 -m venv .venv
9. Activa: source .venv/bin/activate
10. Instala: python -m pip install -e .
11. Diagnóstico: nexus doctor
12. Simulación: nexus create --title "RSVP visual" --kind visual --complexity 1 --quality 3
13. Obtén ID: nexus list; luego ejecuta nexus route ID y nexus history ID.

IMPORTANTE: los comandos de Nexus no lanzan agentes. Las CLIs de Claude, Codex y Kiro deben instalarse/autenticarse dentro de WSL para utilizarlas posteriormente, aunque estén instaladas en Windows. Sigue las guías oficiales de CAO. No utilices --yolo ni omitas permisos en proyectos personales; revisa docs/SECURITY.md antes de cualquier ejecución real.

Para estabilidad fijaremos una versión/tag/commit de CAO después del primer piloto, en lugar de seguir main indefinidamente.
