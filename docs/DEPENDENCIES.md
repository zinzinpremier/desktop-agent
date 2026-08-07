# Dependencies

PlasmaLLM is designed to lean on **what's already installed** on a KDE Plasma 6 system. Most external programs invoked by tools are common Linux utilities. This document lists everything by category so you know what to install if something misbehaves.

## Required (built-in)

| Component | Version | Source |
|---|---|---|
| **KDE Plasma** | 6.0+ | `plasma-desktop` package |
| **Qt** | 6 | pulled by Plasma 6 |
| **KDE Frameworks 6** | 6.0+ | `kf6` (KConfig, KWallet, Kirigami) |
| **KWallet** | 5/6 | secret storage for API keys |

## Build-time (translations, packaging)

Required only if you regenerate `.mo` files or rebuild the `.plasmoid`:

| Tool | Purpose |
|---|---|
| `gettext` (`xgettext`, `msgmerge`, `msgfmt`, `msgattrib`) | Translation extraction, merging, compilation, validation |
| `zip` | Package creation (`make package`) |
| `make` | Obviously |

Install (Debian/Ubuntu): `sudo apt install gettext zip make`

## Tool runtime dependencies

Tools call external binaries via `context.exec()`. Most are coreutils, but a few are optional and surfaced in the UI when missing.

### Filesystem tools

| Tool | Binary | Status |
|---|---|---|
| `read_file` | `head` | coreutils |
| `write_file` | `tee`, `mkdir` | coreutils |
| `list_dir` | `ls` | coreutils |
| `search_files` | `grep`, `timeout` (coreutils ≥ 8.32) | coreutils |

### Network tools

| Tool | Binary | Status |
|---|---|---|
| `web_search` (DuckDuckGo) | `curl` | install `curl` |
| `web_search` (SearXNG) | `curl` + SearXNG instance | depends on config |
| `web_search` (Ollama) | `curl` + local Ollama | depends on config |
| `http_get`, `http_request` | `curl` | install `curl` |

### Desktop integration

| Tool | Binary | Status |
|---|---|---|
| `run_command` | user shell + everything | depends on user intent |
| `get_clipboard` / `set_clipboard` | `wl-paste` / `wl-copy` (Wayland) **or** `xclip` / `xsel` (X11) | install per session |
| `notify` | `notify-send` | `libnotify-bin` |
| `open_url` | `xdg-open` | `xdg-utils` |
| Terminal multiplexing | `tmux` **or** `screen` | optional, per session |

### Desktop automation (driver)

The driver stack is **opt-in** (`Plasmoid.configuration.enableDesktopAutomation`). It needs:

| Component | Notes |
|---|---|
| `com.joshuaroman.plasmallm.DesktopDriver` D-Bus service | from the `plasmallm-driver` package (separate repo) |
| Active Wayland session | remote-desktop portal access required |

### TTS — Piper (optional)

Enabled by `Plasmoid.configuration.ttsEnabled`. Without it, `speak_text` tool returns an error message.

| Component | Source |
|---|---|
| `piper` binary | `~/.local/share/plasmallm/bin/piper` (downloaded by `scripts/install_tts.sh`) |
| Voice `.onnx` + `.onnx.json` | `~/.local/share/plasmallm/models/piper/` (downloaded by script) |
| `libespeak-ng` (system) | `libespeak-ng1` |

Default voices (downloaded by default):
- French: `fr_FR-upmc-medium` (~60 MB)
- English: `en_US-lessac-medium` (~60 MB)

### ASR — whisper.cpp (optional)

Enabled by `Plasmoid.configuration.asrEnabled`. Without the helper daemon, the mic button in the widget is hidden.

| Component | Source |
|---|---|
| `whisper.cpp` binary | `~/.local/share/plasmallm/bin/whisper-cli` (built by `scripts/install_asr.sh`) |
| Whisper model | `~/.local/share/plasmallm/models/whisper/` |
| `wl-copy` + `wtype` (Wayland) or `xdotool` (X11) | text injection |
| `systemd --user` | daemon management |

Default model: `ggml-base.bin` (~140 MB). Alternatives: `tiny` (75 MB, faster), `small` (460 MB, better accuracy).

### LLM providers

No SDK installs — adapters speak HTTP directly.

| Provider | Needs |
|---|---|
| Ollama | running daemon, `ollama pull <model>` |
| LM Studio | local server enabled |
| OpenAI / OpenAI-compatible | API key (stored in KWallet) |
| Anthropic | API key |
| Gemini | API key |

## Recommended packages (Debian/Ubuntu one-liner)

```bash
sudo apt install \
    curl xdg-utils libnotify-bin wl-clipboard wtype \
    libespeak-ng1 gettext zip make
```

## Recommended packages (Fedora)

```bash
sudo dnf install \
    curl xdg-utils libnotify wl-clipboard wtype \
    espeak-ng gettext zip make
```

## Verifying dependencies

From a terminal:

```bash
for cmd in curl xdg-open notify-send wl-copy wtype espeak-ng; do
    command -v $cmd >/dev/null && echo "✓ $cmd" || echo "✗ $cmd MISSING"
done
```

If any line shows `MISSING`, install it from the list above. TTS / ASR tools are checked separately by the install scripts (`scripts/install_tts.sh`, `scripts/install_asr.sh`).