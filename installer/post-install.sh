#!/usr/bin/env bash
# Runs after self-extractor unpacks payload. Starts setup wizard.
set -euo pipefail

PAYLOAD="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
DATA="${MYOFFICE_DATA:-$HOME/.local/share/myoffice}"

mkdir -p "$DATA"
rsync -a --delete \
  --exclude 'dist/' --exclude 'build/' \
  "$PAYLOAD/" "$DATA/install/"

export MYOFFICE_ROOT="$DATA/install"
export MYOFFICE_DATA="$DATA"
export PYTHONPATH="$MYOFFICE_ROOT${PYTHONPATH:+:$PYTHONPATH}"

# Symlink launchers into ~/.local/bin if present
mkdir -p "$HOME/.local/bin"
for name in myoffice-launch myoffice-settings myoffice-doctor; do
  ln -sf "$DATA/install/bin/$name" "$HOME/.local/bin/$name"
done

exec python3 "$MYOFFICE_ROOT/wizard/app.py"
