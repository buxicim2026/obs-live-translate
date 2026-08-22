#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# package-plugin.sh — build the OBS plugin package on Linux (x64) or macOS
# (Apple Silicon).
#
# Output:
#   Linux:  release/stream-live-translate-obs-linux-x64-<version>.tar.gz
#   macOS:  release/stream-live-translate-obs-macos-arm64-<version>.tar.gz
#           (contains stream-live-translate.plugin bundle)
#
# Prerequisites: Rust toolchain, C/C++ compiler, cmake, git.
#
# Like the Windows script this does NOT build OBS itself. It needs:
#   * libobs headers  -> shallow clone of obs-studio at a pinned tag
#   * Linux: a stub libobs.so with soname libobs.so.0 (symbols resolve at
#     runtime against the installed OBS)
#   * macOS: nothing extra; the module is linked with -undefined dynamic_lookup
# ---------------------------------------------------------------------------
set -euo pipefail

OBS_VERSION="${OBS_VERSION:-30.2.3}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$ROOT/build/plugin-sdk"
STAGE="$ROOT/build/stage-unix"

step() { printf '\n==> %s\n' "$*"; }

VERSION="$(sed -n 's/^version = "\(.*\)"/\1/p' "$ROOT/Cargo.toml" | head -n1)"
step "Packaging Stream Live Translate OBS plugin v$VERSION"

case "$(uname -s)" in
    Linux)  OS=linux ;;
    Darwin) OS=macos ;;
    *) echo "unsupported platform: $(uname -s)" >&2; exit 1 ;;
esac

# --- 1. Engine -------------------------------------------------------------
step "Building Rust engine (release)"
(cd "$ROOT" && cargo build --release)

if [ "$OS" = "linux" ]; then
    ENGINE="$ROOT/target/release/stream-live-translate"
else
    ENGINE="$ROOT/target/release/stream-live-translate"
fi
[ -f "$ENGINE" ] || { echo "engine binary missing: $ENGINE" >&2; exit 1; }

# --- 2. OBS SDK headers ------------------------------------------------------
mkdir -p "$WORK"
OBS_SRC="$WORK/obs-studio"
if [ ! -f "$OBS_SRC/libobs/obs-module.h" ]; then
    step "Fetching libobs headers (obs-studio $OBS_VERSION, shallow clone)"
    git clone --depth 1 --branch "$OBS_VERSION" \
        https://github.com/obsproject/obs-studio "$OBS_SRC"
fi

# --- 3. Platform-specific link target ---------------------------------------
CMAKE_EXTRA=()
if [ "$OS" = "linux" ]; then
    STUB_DIR="$WORK/sdk-lib"
    mkdir -p "$STUB_DIR"
    if [ ! -f "$STUB_DIR/libobs.so" ]; then
        step "Creating stub libobs.so (soname libobs.so.0)"
        printf '/* link-time stub; real symbols come from OBS at runtime */\n' \
            > "$STUB_DIR/stub.c"
        cc -shared -Wl,-soname,libobs.so.0 -o "$STUB_DIR/libobs.so" "$STUB_DIR/stub.c"
    fi
    CMAKE_EXTRA+=("-DOBS_STUB_LIB=$STUB_DIR/libobs.so")
fi

# --- 4. Build the plugin -----------------------------------------------------
step "Building plugin (CMake)"
BUILD_DIR="$ROOT/build/plugin-build-$OS"
cmake -S "$ROOT/plugin" -B "$BUILD_DIR" \
    -DCMAKE_BUILD_TYPE=Release \
    -DLIBOBS_INCLUDE_DIR="$OBS_SRC/libobs" \
    "${CMAKE_EXTRA[@]:-}"
cmake --build "$BUILD_DIR"

# --- 5. Assemble --------------------------------------------------------------
rm -rf "$STAGE"
mkdir -p "$ROOT/release"

if [ "$OS" = "linux" ]; then
    SO="$(find "$BUILD_DIR" -name 'stream-live-translate.so' | head -n1)"
    [ -n "$SO" ] || { echo "plugin .so not found" >&2; exit 1; }
    PKG="$STAGE/stream-live-translate"
    mkdir -p "$PKG/bin/64bit" "$PKG/data/locale" "$PKG/data/engine"
    cp "$SO" "$PKG/bin/64bit/"
    cp "$ROOT"/plugin/locale/*.ini "$PKG/data/locale/"
    cp "$ENGINE" "$PKG/data/engine/"
    cp "$ROOT/README.md" "$PKG/README.md"

    OUT="$ROOT/release/stream-live-translate-obs-linux-x64-$VERSION.tar.gz"
    step "Creating $OUT"
    tar -czf "$OUT" -C "$STAGE" stream-live-translate
else
    # macOS: .plugin bundle layout expected by OBS.
    DYLIB="$(find "$BUILD_DIR" -name 'stream-live-translate' -type f | head -n1)"
    [ -n "$DYLIB" ] || { echo "plugin module not found" >&2; exit 1; }
    BUNDLE="$STAGE/stream-live-translate.plugin"
    mkdir -p "$BUNDLE/Contents/MacOS" "$BUNDLE/Contents/Resources/data/locale" \
             "$BUNDLE/Contents/Resources/data/engine"
    cp "$DYLIB" "$BUNDLE/Contents/MacOS/stream-live-translate"
    chmod +x "$BUNDLE/Contents/MacOS/stream-live-translate"
    cp "$ROOT"/plugin/locale/*.ini "$BUNDLE/Contents/Resources/data/locale/"
    cp "$ENGINE" "$BUNDLE/Contents/Resources/data/engine/"
    cat > "$BUNDLE/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleIdentifier</key>
    <string>com.streamlivetranslate.obs-plugin</string>
    <key>CFBundleName</key>
    <string>Stream Live Translate</string>
    <key>CFBundleVersion</key>
    <string>$VERSION</string>
</dict>
</plist>
EOF
    cp "$ROOT/README.md" "$STAGE/README.md"

    OUT="$ROOT/release/stream-live-translate-obs-macos-arm64-$VERSION.tar.gz"
    step "Creating $OUT"
    tar -czf "$OUT" -C "$STAGE" stream-live-translate.plugin README.md
fi

# --- 6. Checksum ---------------------------------------------------------------
if command -v sha256sum >/dev/null 2>&1; then
    ( cd "$ROOT/release" && sha256sum "$(basename "$OUT")" > "$(basename "$OUT").sha256" )
else
    ( cd "$ROOT/release" && shasum -a 256 "$(basename "$OUT")" > "$(basename "$OUT").sha256" )
fi

step "Done: $OUT"
if [ "$OS" = "linux" ]; then
    echo "    Install: extract into ~/.config/obs-studio/plugins/"
else
    echo "    Install: extract into ~/Library/Application Support/obs-studio/plugins/"
fi
