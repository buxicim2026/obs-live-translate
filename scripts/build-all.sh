#!/usr/bin/env bash
# Cross-platform build + package script for Stream Live Translate
# (standalone engine distribution). Produces `release/<platform>/` with the
# binary and all static assets, then zips it.
#
# NOTE: for the OBS plugin package (copy-into-OBS folder distribution), use
# scripts/package-plugin.sh instead (see docs/PLUGIN.md).
set -euo pipefail
cd "$(dirname "$0")/.."

PLATFORM="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"
case "$PLATFORM-$ARCH" in
  linux-x86_64)   TARGET="x86_64-unknown-linux-gnu";     OUTDIR="release/linux-x64" ;;
  linux-aarch64)  TARGET="aarch64-unknown-linux-gnu";    OUTDIR="release/linux-arm64" ;;
  darwin-arm64)   TARGET="aarch64-apple-darwin";         OUTDIR="release/macos-arm64" ;;
  darwin-x86_64)  TARGET="x86_64-apple-darwin";          OUTDIR="release/macos-x64" ;;
  mingw*_x86_64)  TARGET="x86_64-pc-windows-gnu";       OUTDIR="release/windows-x64" ;;
  *)              echo "Unsupported platform: $PLATFORM-$ARCH" >&2; exit 1 ;;
esac

echo "==> Building for $TARGET"
rustup target add "$TARGET" >/dev/null 2>&1 || true
cargo build --release --target "$TARGET"

mkdir -p "$OUTDIR/bin"
cp "target/$TARGET/release/stream-live-translate" "$OUTDIR/bin/"
cp -R dist/overlay dist/admin "$OUTDIR/"
cp dist/launcher.sh "$OUTDIR/launcher.sh"
chmod +x "$OUTDIR/launcher.sh"
cp dist/launcher.bat "$OUTDIR/" 2>/dev/null || true
cp dist/README.txt "$OUTDIR/"

# Pick a friendly exe name on Windows.
if [[ "$TARGET" == *windows* ]]; then
  mv "$OUTDIR/bin/stream-live-translate" "$OUTDIR/bin/stream-live-translate.exe"
fi

OUTFILE="$OUTDIR.tar.gz"
rm -f "$OUTFILE"
(cd release && tar -czf "$(basename "$OUTFILE")" "$(basename "$OUTDIR")")
echo "==> Built $(realpath "$OUTFILE")"
