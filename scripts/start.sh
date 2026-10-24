#!/usr/bin/env bash
# Levanta cao-server en una sesión tmux en segundo plano y lanza un supervisor de JASP Nexus
# en el directorio del proyecto indicado.
#   Uso: ./scripts/start.sh [ruta-del-proyecto] [perfil-supervisor]
#   Por defecto: el directorio actual y nexus_supervisor (Claude orquesta).
#   Modo construcción (GPT orquesta a Kiro): ./scripts/start.sh <repo> nexus_build_codex
set -euo pipefail

PROJECT_DIR="$(cd "${1:-$PWD}" && pwd)"
AGENT="${2:-nexus_supervisor}"
SERVER_SESSION="nexus-server"
export PATH="$HOME/.local/bin:$PATH"

command -v cao-server >/dev/null || { echo "cao-server no está instalado. Corre scripts/setup-wsl.sh." >&2; exit 1; }

if ! tmux has-session -t "$SERVER_SESSION" 2>/dev/null; then
  echo "Iniciando cao-server en la sesión tmux '$SERVER_SESSION'"
  tmux new-session -d -s "$SERVER_SESSION" "cao-server"
fi

for _ in $(seq 1 30); do
  # Cualquier respuesta HTTP significa que el puerto ya acepta conexiones.
  curl -s -o /dev/null http://localhost:9889/ && break
  sleep 1
done

echo "Servidor arriba (Web UI: http://localhost:9889). Ver logs: tmux attach -t $SERVER_SESSION"
echo "Lanzando $AGENT en $PROJECT_DIR"
cd "$PROJECT_DIR"
exec cao launch --agents "$AGENT"
