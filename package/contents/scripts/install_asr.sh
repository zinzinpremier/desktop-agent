#!/usr/bin/env bash
# install_asr.sh — Install the plasmallm-asr daemon using Cloudflare ASR API.
#
# Usage:
#   ./scripts/install_asr.sh           # install
#   ./scripts/install_asr.sh --remove  # remove everything installed by this script
#
# What it does:
#   1. Installs asr_helper.py to ~/.local/share/plasmallm/bin/.
#   2. Registers a systemd --user service so the daemon starts on demand.
#
# No root required. The ASR uses the Cloudflare endpoint: https://api.guig.dev/transcribe

set -euo pipefail

PLASMALLM_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/plasmallm"
SERVICE_DIR="$HOME/.config/systemd/user"

action="install"
while [ $# -gt 0 ]; do
    case "$1" in
        --remove) action="remove" ;;
        *) echo "Unknown argument: $1" >&2; exit 1 ;;
    esac
    shift
done

remove_install() {
    echo "Stopping and disabling plasmallm-asr.service..."
    systemctl --user disable --now plasmallm-asr.service 2>/dev/null || true
    rm -f "$SERVICE_DIR/plasmallm-asr.service"
    echo "Removing helper script..."
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
need_cmd python3 "python3"

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

mkdir -p "$PLASMALLM_HOME/bin"

# Install asr_helper.py — the source is in scripts/ next to this file
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HELPER_SRC="$SCRIPT_DIR/asr_helper.py"
HELPER_DST="$PLASMALLM_HOME/bin/asr_helper.py"
if [ -f "$HELPER_SRC" ]; then
    install -m 0755 "$HELPER_SRC" "$HELPER_DST"
else
    echo "asr_helper.py not found at $HELPER_SRC — skipping helper install." >&2
fi

# systemd --user service
cat > "$SERVICE_DIR/plasmallm-asr.service" <<EOF
[Unit]
Description=PlasmaLLM ASR (Cloudflare API)
After=pipewire.service

[Service]
Type=simple
Environment=PLASMALLM_ASR_LANG=fr
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
echo "ASR Endpoint: https://api.guig.dev/transcribe"