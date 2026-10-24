#!/usr/bin/env bash
# Cierra todas las sesiones de agentes de CAO y el servidor.
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"

cao shutdown --all || true
tmux kill-session -t nexus-server 2>/dev/null || true
echo "JASP Nexus detenido."
