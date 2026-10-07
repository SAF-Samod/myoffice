#!/usr/bin/env bash
# Build MyOffice-Setup.run — self-extracting installer (makeself or fallback).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$ROOT/dist/MyOffice-Setup.run}"
STAGE="$ROOT/build/stage"
PAYLOAD="$STAGE/myoffice"

rm -rf "$STAGE"
mkdir -p "$PAYLOAD"

rsync -a \
  --exclude 'poc/' \
  --exclude 'build/' \
  --exclude 'dist/' \
  --exclude '.git/' \
  "$ROOT/" "$PAYLOAD/"

chmod +x "$PAYLOAD/bin/"* "$PAYLOAD/poc/"*.sh 2>/dev/null || true
chmod +x "$PAYLOAD/installer/post-install.sh"

mkdir -p "$(dirname "$OUT")"

if command -v makeself >/dev/null 2>&1; then
  makeself --nox11 "$PAYLOAD" "$OUT" "MyOffice Setup" ./installer/post-install.sh
else
  # Fallback: tar.gz + stub script
  ARCHIVE="$STAGE/payload.tar.gz"
  tar -czf "$ARCHIVE" -C "$STAGE" myoffice
  cat > "$OUT" << 'STUB'
#!/usr/bin/env bash
set -euo pipefail
TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT
ARCHIVE="$TMP/payload.tar.gz"
LINE=$(( $(grep -a -n '^__ARCHIVE__$' "$0" | cut -d: -f1) + 1 ))
tail -n +"$LINE" "$0" > "$ARCHIVE"
tar -xzf "$ARCHIVE" -C "$TMP"
exec "$TMP/myoffice/installer/post-install.sh" "$TMP/myoffice"
exit 0
__ARCHIVE__
STUB
  cat "$ARCHIVE" >> "$OUT"
  chmod +x "$OUT"
fi

echo "Built: $OUT"
