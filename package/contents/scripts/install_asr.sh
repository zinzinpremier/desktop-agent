#!/usr/bin/env bash
# install_asr.sh — Build whisper.cpp + install the plasmallm-asr daemon.
#
# Usage:
#   ./scripts/install_asr.sh           # install (default base model)
#   ./scripts/install_asr.sh --model small   # install the small model instead
#   ./scripts/install_asr.sh --remove  # remove everything installed by this script
#
# What it does:
#   1. Clones whisper.cpp to ~/.local/share/build/whisper.cpp and builds
#      `whisper-cli` (CPU + Vulkan if the SDK is present).
#   2. Downloads the chosen Whisper ggml model (~140 MB for "base").
#   3. Installs asr_helper.py to ~/.local/share/plasmallm/bin/.
#   4. Registers a systemd --user service so the daemon starts on demand.
#
# No root required.

set -euo pipefail

PLASMALLM_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/plasmallm"
BUILD_DIR="${XDG_BUILD_HOME:-$HOME/.local/share/build}/whisper.cpp"
MODELS_DIR="$PLASMALLM_HOME/models/whisper"
WHISPER_BIN="$PLASMALLM_HOME/bin/whisper-cli"
WHISPER_BIN_SYMLINK="$PLASMALLM_HOME/bin/whisper.cpp"
SERVICE_DIR="$HOME/.config/systemd/user"

# Default model. Override with --model <name>.
MODEL="base"

action="install"
while [ $# -gt 0 ]; do
    case "$1" in
        --remove) action="remove" ;;
        --model)
            shift
            MODEL="${1:-base}"
            ;;
        *) echo "Unknown argument: $1" >&2; exit 1 ;;
    esac
    shift
done

remove_install() {
    echo "Stopping and disabling plasmallm-asr.service..."
    systemctl --user disable --now plasmallm-asr.service 2>/dev/null || true
    rm -f "$SERVICE_DIR/plasmallm-asr.service"
    echo "Removing whisper.cpp build, models, and helper script..."
    rm -rf "$BUILD_DIR"
    rm -rf "$MODELS_DIR"
    rm -f "$PLASMALLM_HOME/bin/whisper-cli"
    rm -f "$PLASMALLM_HOME/bin/whisper.cpp"
    rm -f "$PLASMALLM_HOME/bin/asr_helper.py"
    echo "Done."
}

if [ "$action" = "remove" ]; then
    remove_install
    exit 0
fi

# System deps
need_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "Missing required command: $1" >&2
        echo "Install: $2" >&2
        exit 2
    fi
}
need_cmd git "git"
need_cmd cmake "cmake"
need_cmd make "make"
need_cmd gcc "gcc / build-essential"
need_cmd curl "curl"

# PipeWire / wl-clipboard
if ! command -v pw-record >/dev/null 2>&1 && ! command -v pw-cat >/dev/null 2>&1; then
    echo "PipeWire client utilities are required (pw-record or pw-cat)." >&2
    echo "Install: sudo apt install pipewire-audio-client-libraries (Debian/Ubuntu)" >&2
    exit 2
fi
if [ "${XDG_SESSION_TYPE:-x11}" = "wayland" ]; then
    if ! command -v wtype >/dev/null 2>&1 && ! command -v wl-copy >/dev/null 2>&1; then
        echo "wtype or wl-copy is required on Wayland for text injection." >&2
        echo "Install: sudo apt install wtype wl-clipboard" >&2
        exit 2
    fi
else
    if ! command -v xdotool >/dev/null 2>&1; then
        echo "xdotool is required on X11 for text injection." >&2
        echo "Install: sudo apt install xdotool" >&2
        exit 2
    fi
fi

mkdir -p "$PLASMALLM_HOME/bin" "$MODELS_DIR"

# 1. Build whisper.cpp
if [ ! -x "$WHISPER_BIN" ]; then
    echo "Cloning whisper.cpp..."
    mkdir -p "$(dirname "$BUILD_DIR")"
    if [ ! -d "$BUILD_DIR" ]; then
        git clone --depth 1 https://github.com/ggerganov/whisper.cpp.git "$BUILD_DIR"
    fi
    cd "$BUILD_DIR"
    echo "Building whisper-cli (CPU)..."
    cmake -B build -DWHISPER_BUILD_TESTS=OFF -DWHISPER_BUILD_SERVER=OFF 2>&1 | tail -3
    cmake --build build --config Release -j"$(nproc)" --target whisper-cli 2>&1 | tail -3
    cp build/bin/whisper-cli "$WHISPER_BIN"
    chmod +x "$WHISPER_BIN"
    ln -sf whisper-cli "$WHISPER_BIN_SYMLINK"
    cd - >/dev/null
fi

# 2. Download model
MODEL_FILE="$MODELS_DIR/ggml-${MODEL}.bin"
if [ ! -f "$MODEL_FILE" ]; then
    echo "Downloading ggml-${MODEL}.bin..."
    URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-${MODEL}.bin"
    if ! curl -fL --connect-timeout 15 -o "$MODEL_FILE" "$URL"; then
        echo "Download failed: $URL" >&2
        rm -f "$MODEL_FILE"
        exit 3
    fi
fi

# 3. Install asr_helper.py — the source is in scripts/ next to this file
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HELPER_SRC="$SCRIPT_DIR/asr_helper.py"
HELPER_DST="$PLASMALLM_HOME/bin/asr_helper.py"
if [ -f "$HELPER_SRC" ]; then
    install -m 0755 "$HELPER_SRC" "$HELPER_DST"
else
    echo "asr_helper.py not found at $HELPER_SRC — skipping helper install." >&2
fi

# 4. systemd --user service
cat > "$SERVICE_DIR/plasmallm-asr.service" <<EOF
[Unit]
Description=PlasmaLLM ASR (whisper.cpp)
After=pipewire.service

[Service]
Type=simple
ExecStart=$HELPER_DST
Restart=on-failure
RestartSec=2

[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload

echo ""
echo "Done. To start the daemon now:"
echo "  systemctl --user enable --now plasmallm-asr.service"
echo ""
echo "Then enable ASR in Configure Desktop Agent → Appearance → Speech-to-Text,"
echo "and use the configured global hotkey (default Meta+Shift+Space)."
echo ""
echo "Model: $MODEL  ($(du -h "$MODEL_FILE" | cut -f1))"