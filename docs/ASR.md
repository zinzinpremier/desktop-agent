# Speech-to-Text (whisper.cpp)

PlasmaLLM uses [whisper.cpp](https://github.com/ggerganov/whisper.cpp) for local, on-device speech recognition. Models run on CPU with optional Vulkan/CUDA GPU acceleration.

## Architecture

Two pieces:

1. **`asr_helper.py`** — a small D-Bus daemon that listens for activation, captures mic audio via PipeWire, runs whisper.cpp, and types the result wherever the cursor is.
2. **Widget integration** — the widget exposes a mic button and auto-starts the daemon on demand.

The daemon is **session-scoped** (your user only) and runs as `systemd --user` service `plasmallm-asr.service`.

## Install

Run once:

```bash
./scripts/install_asr.sh
```

This:

| Step | Notes |
|---|---|
| Clones whisper.cpp (shallow) | `~/.local/share/build/whisper.cpp` |
| Builds `whisper-cli` | CPU + Vulkan (if `vulkan-sdk` present) |
| Downloads `ggml-base.bin` (~140 MB) | `~/.local/share/plasmallm/models/whisper/` |
| Installs `asr_helper.py` | `~/.local/share/plasmallm/bin/` |
| Registers `plasmallm-asr.service` | `~/.config/systemd/user/` |

Total: ~150 MB + ~80 MB build dir.

## Global hotkey

Default: **`Meta+Shift+Space`** (press-and-hold to record, release to transcribe).

Customize via `Configure Desktop Agent → General → ASR → Global hotkey`. Plasma's `KGlobalAccel` framework is used so the shortcut works whether the widget is focused or not.

## How it works

```
User presses Meta+Shift+Space
  ↓
asr_helper.py starts recording (pw-record)
  ↓
User releases the shortcut
  ↓
Recording stops → WAV saved to /tmp
  ↓
whisper-cli runs on the WAV → text
  ↓
Text injected via:
  • Wayland: wtype (typed), or wl-copy + Ctrl+V simulation
  • X11: xdotool type
  ↓
Audio + text discarded
```

If the global shortcut can't be grabbed (e.g., another app holds it), the widget logs the failure and disables the shortcut. Use the widget's mic button as fallback.

## Widget integration

The widget exposes:

- **🎤 button in the input bar** — same behaviour as the global hotkey but anchored to the widget
- **Live transcript overlay** — appears while recording, dismissible
- **Auto-punctuation** — whisper.cpp's built-in punctuation
- **Language detection** — auto, but lockable via config (`asrLanguage = "fr"`)

Configuration keys (`Plasmoid.configuration`):

| Key | Default | Description |
|---|---|---|
| `asrEnabled` | `false` | Master toggle |
| `asrModel` | `base` | `tiny`, `base`, `small`, `medium` |
| `asrLanguage` | `auto` | `auto`, `fr`, `en`, … |
| `asrGlobalHotkey` | `Meta+Shift+Space` | KDE global shortcut |
| `asrMaxDurationSec` | `60` | Stop recording after N seconds |

## Models

Whisper models trade accuracy for size:

| Model | Size | Speed (CPU) | WER (EN) |
|---|---|---|---|
| `tiny` | 75 MB | <1× real-time on Pi 5 | ~7% |
| `base` | 140 MB | ~1× on modern laptop | ~5% |
| `small` | 460 MB | ~2× on modern laptop | ~4% |
| `medium` | 1.5 GB | ~5× on modern laptop | ~3% |

French recognition quality roughly matches English at the same model size.

To upgrade the model:

```bash
./scripts/install_asr.sh --model small
```

## Privacy

Everything runs on-device:

- Audio is captured from PipeWire in your session
- whisper.cpp runs locally, no network
- Transcribed text is typed into the focused window — same as if you typed it
- No audio or transcript is uploaded, logged, or persisted (unless you save the chat)

## Troubleshooting

| Symptom | Fix |
|---|---|
| "Failed to start ASR daemon" | Check `journalctl --user -u plasmallm-asr.service` |
| "No microphone detected" | `pw-cli list-objects \| grep Source` to verify PipeWire sees it |
| "Permission denied" | Make sure your user is in the `audio` group or has PipeWire access |
| Global hotkey doesn't work | Check `KGlobalAccel` in System Settings; some DEs reserve Meta+Shift combos |
| Daemon eats CPU | Use a smaller model (`tiny` or `base`) |

## Uninstall

```bash
systemctl --user disable --now plasmallm-asr.service
rm ~/.config/systemd/user/plasmallm-asr.service
rm -rf ~/.local/share/{build/whisper.cpp,share/plasmallm/{bin/asr_helper.py,models/whisper}}
```