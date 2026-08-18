#!/usr/bin/env bash
# Stream Live Translate - macOS / Linux launcher
# Double-click on macOS or run from terminal on Linux.
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

EXE="$ROOT/stream-live-translate"
if [ ! -x "$EXE" ]; then
  chmod +x "$EXE" 2>/dev/null || true
fi
if [ ! -x "$EXE" ]; then
  echo "[error] stream-live-translate binary not found in $ROOT" >&2
  exit 1
fi

# Open admin panel in default browser.
( sleep 1 && ( open "http://127.0.0.1:8787/admin" 2>/dev/null \
             || xdg-open "http://127.0.0.1:8787/admin" 2>/dev/null ) & ) >/dev/null 2>&1

exec "$EXE" "$@"
