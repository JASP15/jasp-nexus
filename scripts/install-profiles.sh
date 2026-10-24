#!/usr/bin/env bash
# Instala los perfiles de JASP Nexus en CAO.
# Sustituye {{NEXUS_HOME}} por la ruta real del repo (para config/routing.yaml) y
# {{NEXUS_DATA}} por el directorio de datos (para state/quota.json).
# Vuelve a correrlo cada vez que cambies un archivo de profiles/.
set -euo pipefail

NEXUS_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NEXUS_DATA="${NEXUS_DATA_DIR:-$HOME/.jasp-nexus}"
BUILD_DIR="$NEXUS_HOME/.build/profiles"
export PATH="$HOME/.local/bin:$PATH"

command -v cao >/dev/null || { echo "cao no está instalado. Corre scripts/setup-wsl.sh primero." >&2; exit 1; }

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

for src in "$NEXUS_HOME"/profiles/*.md; do
  out="$BUILD_DIR/$(basename "$src")"
  sed -e "s#{{NEXUS_HOME}}#$NEXUS_HOME#g" -e "s#{{NEXUS_DATA}}#$NEXUS_DATA#g" "$src" > "$out"
  echo "Instalando $(basename "$src" .md)"
  cao install "$out"
done

echo
echo "Perfiles instalados. Arranca con: ./scripts/start.sh /ruta/a/tu/proyecto"
