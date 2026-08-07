#!/usr/bin/env bash
# install_tts.sh — Install Piper TTS + FR/EN voice models for Desktop Agent.
#
# Downloads Piper binary, the espeak-ng system dependency is left to the distro,
# and two voice models (FR + EN, ~130 MB total) under
# ~/.local/share/plasmallm/{bin,lib,models/piper}.
#
# Usage:
#   ./scripts/install_tts.sh           # install
#   ./scripts/install_tts.sh --update  # refresh binary without re-downloading models
#   ./scripts/install_tts.sh --remove  # remove everything installed by this script
#
# No root required; everything lives in your home directory.

set -euo pipefail

PIPER_VERSION="${PIPER_VERSION:-2023.11.4-2}"
PLASMALLM_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/plasmallm"
PIPER_BIN="$PLASMALLM_HOME/bin/piper"
PIPER_LIB_DIR="$PLASMALLM_HOME/lib"
VOICES_DIR="$PLASMALLM_HOME/models/piper"

# Map (arch uname) → piper's release asset name.
ARCH="$(uname -m)"
case "$ARCH" in
    x86_64) PIPER_ARCH="amd64" ;;
    aarch64|arm64) PIPER_ARCH="arm64" ;;
    armv7l) PIPER_ARCH="armv7" ;;
    *)
        echo "Unsupported architecture: $ARCH" >&2
        echo "Open an issue: https://github.com/rhasspy/piper/releases" >&2
        exit 1
        ;;
esac

# Voices to install by default (one per language). Edit this list and re-run
# the script with --update to add or swap voices.
DEFAULT_VOICES=(
    "fr/fr_FR/upmc/medium/fr_FR-upmc-medium"
    "en/en_US/lessac/medium/en_US-lessac-medium"
)

action="install"
[ "${1:-}" = "--remove" ] && action="remove"
[ "${1:-}" = "--update" ] && action="update"

remove_install() {
    echo "Removing Piper + voice models installed by this script..."
    rm -f "$PIPER_BIN" "$PIPER_LIB_DIR"/libpiper_phonemize*
    rm -rf "$VOICES_DIR"
    echo "Done. Re-run ./scripts/install_tts.sh to reinstall."
}

if [ "$action" = "remove" ]; then
    remove_install
    exit 0
fi

# System deps
if ! command -v espeak-ng >/dev/null 2>&1 && ! ldconfig -p 2>/dev/null | grep -q "libespeak-ng"; then
    echo "libespeak-ng is required. Install it first:"
    echo "  Debian/Ubuntu: sudo apt install libespeak-ng1"
    echo "  Fedora:        sudo dnf install espeak-ng"
    echo "  Arch:          sudo pacman -S espeak-ng"
    exit 2
fi

if ! command -v paplay >/dev/null 2>&1 && ! command -v aplay >/dev/null 2>&1; then
    echo "Neither paplay (PipeWire) nor aplay (ALSA) is installed."
    echo "Install one: sudo apt install pulseaudio-utils alsa-utils (Debian/Ubuntu)"
    echo "On Wayland desktops, paplay from pipewire-pulse is recommended."
    exit 2
fi

mkdir -p "$PLASMALLM_HOME/bin" "$PIPER_LIB_DIR" "$VOICES_DIR"

# Download Piper tarball if missing or out-of-date
if [ "$action" = "install" ] || [ ! -x "$PIPER_BIN" ]; then
    echo "Downloading Piper ${PIPER_VERSION} for linux_${PIPER_ARCH}..."
    TARBALL="$(mktemp --suffix=.tar.gz)"
    URL="https://github.com/rhasspy/piper/releases/download/${PIPER_VERSION}/piper_linux_${PIPER_ARCH}.tar.gz"
    if ! curl -fL --connect-timeout 10 -o "$TARBALL" "$URL"; then
        echo "Download failed: $URL" >&2
        rm -f "$TARBALL"
        exit 3
    fi
    tar -xzf "$TARBALL" -C "$PLASMALLM_HOME/bin" --strip-components=1
    rm -f "$TARBALL"
fi

# Move piper_phonemize shared libs (libpiper_phonemize*.so) next to the binary
PHONEMIZE_SRC="$(find "$PLASMALLM_HOME/bin" -maxdepth 1 -name 'libpiper_phonemize*' 2>/dev/null || true)"
if [ -n "$PHONEMIZE_SRC" ]; then
    mv "$PLASMALLM_HOME/bin"/libpiper_phonemize* "$PIPER_LIB_DIR/" 2>/dev/null || true
fi
# Update rpath so the binary finds its lib in $PLASMALLM_HOME/lib
LD_LIBRARY_PATH="$PIPER_LIB_DIR:${LD_LIBRARY_PATH:-}" \
    "$PIPER_BIN" --version 2>/dev/null || true

# Voices
for rel_path in "${DEFAULT_VOICES[@]}"; do
    IFS='/' read -r lang_loc speaker quality fname <<< "$rel_path"
    target_dir="$VOICES_DIR/$lang_loc"
    mkdir -p "$target_dir"
    base="https://huggingface.co/rhasspy/piper-voices/resolve/main/${lang_loc}/${speaker}/${quality}"
    for ext in onnx onnx.json; do
        out="$target_dir/${fname}.${ext}"
        if [ -f "$out" ]; then
            echo "[skip] $out already present"
            continue
        fi
        echo "Downloading $fname.$ext..."
        if ! curl -fL --connect-timeout 15 -o "$out" "${base}/${fname}.${ext}"; then
            echo "  Failed — check https://huggingface.co/rhasspy/piper-voices/tree/main/${lang_loc}/${speaker} for available voices." >&2
            rm -f "$out"
            continue
        fi
    done
done

# Quick test (FR voice if installed)
FR_VOICE="$VOICES_DIR/fr/fr_FR/upmc/medium/fr_FR-upmc-medium.onnx"
if [ -f "$FR_VOICE" ]; then
    echo ""
    echo "Testing piper…"
    echo "Installation OK. Test with:"
    echo "  echo 'Bonjour, je suis Piper.' | $PIPER_BIN --model $FR_VOICE --output_file /tmp/piper-test.wav && paplay /tmp/piper-test.wav"
else
    echo ""
    echo "No voice found at the default FR path. Try installing one:"
    echo "  ./scripts/install_tts.sh  (edit DEFAULT_VOICES to change)"
fi

echo ""
echo "Done. Enable TTS in Configure Desktop Agent → Appearance → Text-to-Speech."
