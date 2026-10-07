#!/usr/bin/env bash
# Internal PoC: create prefix and install Office via ODT. See CHECKLIST.md.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="${MYOFFICE_DATA:-$HOME/.local/share/myoffice}"
PREFIX="${MYOFFICE_PREFIX:-$DATA/prefixes/office}"
WINE="${MYOFFICE_WINE:-$DATA/runtimes/current/bin/wine}"
ODT_DIR="${MYOFFICE_ODT_DIR:-$DATA/cache/odt}"
CONFIG="$ROOT/config/odt/configuration.xml"

if [[ ! -x "$WINE" ]]; then
  echo "Wine not found at: $WINE" >&2
  echo "Extract a runner to $DATA/runtimes/current or set MYOFFICE_WINE." >&2
  exit 1
fi

mkdir -p "$PREFIX" "$ODT_DIR" "$DATA/logs"
export WINEPREFIX="$PREFIX"
export WINEDEBUG="${WINEDEBUG:--all}"
export WINEDLLOVERRIDES="${WINEDLLOVERRIDES:-mscoree,mshtml=;winemenubuilder.exe=d}"

echo "==> Wine: $($WINE --version)"
echo "==> Prefix: $WINEPREFIX"

if [[ ! -f "$PREFIX/system.reg" ]]; then
  echo "==> Creating WoW64 prefix..."
  WINEARCH=win64 "$WINE" wineboot --init
fi

echo "==> Disabling winemenubuilder..."
"$WINE" reg add 'HKCU\Software\Wine\WineDbg' /v ShowCrashDialog /d 0 /f >/dev/null 2>&1 || true
"$WINE" reg add 'HKCU\Software\Wine\WineDbg' /v ShowCrashDialog /d 0 /f >/dev/null 2>&1 || true
"$WINE" reg add 'HKCU\Software\Wine' /v ShowWineMenuSync /d 0 /f >/dev/null 2>&1 || true

if [[ ! -f "$CONFIG" ]]; then
  echo "Missing ODT config: $CONFIG" >&2
  exit 1
fi

if [[ ! -f "$ODT_DIR/setup.exe" ]]; then
  echo "==> Place Office Deployment Tool in $ODT_DIR (setup.exe + extracted files), then re-run." >&2
  echo "    Copy configuration.xml to the ODT folder and run: wine setup.exe /configure configuration.xml" >&2
  exit 1
fi

cp -f "$CONFIG" "$ODT_DIR/configuration.xml"
echo "==> Running ODT configure (this takes a long time)..."
(cd "$ODT_DIR" && "$WINE" setup.exe /configure configuration.xml) | tee -a "$DATA/logs/poc-install.log"

echo "==> PoC install finished. Run ./poc-launch-word.sh"
