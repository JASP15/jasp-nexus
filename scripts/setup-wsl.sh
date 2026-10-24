#!/usr/bin/env bash
# Prepara Ubuntu (WSL2) para JASP Nexus: tmux, uv, Node, CLIs de agentes y CAO.
# Es idempotente: lo que ya está instalado se omite. No inicia sesión en ningún proveedor.
set -euo pipefail

log() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }

if ! grep -qi microsoft /proc/version 2>/dev/null; then
  echo "Aviso: no parece WSL. El script está pensado para Ubuntu en WSL2." >&2
fi

log "Paquetes base (tmux, git, curl, python3)"
sudo apt-get update -y
sudo apt-get install -y tmux git curl ca-certificates python3 build-essential

tmux_ver=$(tmux -V | grep -oE '[0-9]+\.[0-9]+' | head -1)
if awk -v v="$tmux_ver" 'BEGIN { exit !(v < 3.3) }'; then
  echo "tmux $tmux_ver es menor a 3.3, que CAO requiere. Actualiza la distro (Ubuntu 24.04 trae 3.4)." >&2
  exit 1
fi

if ! have uv; then
  log "Instalando uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"

export NVM_DIR="$HOME/.nvm"
if ! have node; then
  log "Instalando Node LTS con nvm"
  [ -s "$NVM_DIR/nvm.sh" ] || curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
  # shellcheck disable=SC1091
  . "$NVM_DIR/nvm.sh"
  nvm install --lts
fi

have claude || { log "Instalando Claude Code"; npm install -g @anthropic-ai/claude-code; }
have codex  || { log "Instalando Codex CLI";  npm install -g @openai/codex; }
have kiro-cli || { log "Instalando Kiro CLI"; curl -fsSL https://cli.kiro.dev/install | bash; }

log "Instalando/actualizando CAO"
uv tool install "git+https://github.com/awslabs/cli-agent-orchestrator.git@main" --upgrade

log "Listo. Versiones:"
for c in tmux uv node claude codex kiro-cli cao; do
  printf '  %-9s ' "$c"; ("$c" --version 2>/dev/null || echo "(no encontrado)") | head -1
done

cat <<'EOF'

Siguiente paso: inicia sesión en cada CLI (una sola vez, de forma interactiva):
  claude          # sigue el login en el navegador y luego sal con /exit
  codex login
  kiro-cli login
Después: ./scripts/install-profiles.sh
EOF
