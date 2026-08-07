# Text-to-Speech (Piper)

PlasmaLLM uses [Piper](https://github.com/rhasspy/piper) for local, on-device text-to-speech. Voices are downloaded individually (10–100 MB each) and run on CPU in real time.

## Install

The widget bundles `scripts/install_tts.sh`. Run it once:

```bash
./scripts/install_tts.sh
```

This downloads:

| File | Destination | Size |
|---|---|---|
| `piper` binary (Linux x86_64) | `~/.local/share/plasmallm/bin/piper` | ~6 MB |
| `piper_phonemize` shared lib | `~/.local/share/plasmallm/lib/` | ~2 MB |
| `libespeak-ng` (system) | distro package | — |
| `fr_FR-upmc-medium.onnx` + `.json` | `~/.local/share/plasmallm/models/piper/fr/` | ~60 MB |
| `en_US-lessac-medium.onnx` + `.json` | `~/.local/share/plasmallm/models/piper/en/` | ~60 MB |

Total: ~130 MB.

## Usage

Once installed:

1. `Configure Desktop Agent → Appearance → Text-to-Speech → Enable`
2. Pick a voice in `Default voice`
3. Either:
   - **Manual**: click the 🔊 button on any assistant message to read it aloud
   - **Auto-read**: enable `Auto-read assistant responses` in the same tab

The `speak_text` tool is also exposed to the LLM, so the model can request speech when relevant ("let me explain that verbally…").

## Voice catalog

Browse [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices) for available voices. To install another voice:

```bash
mkdir -p ~/.local/share/plasmallm/models/piper/de
cd ~/.local/share/plasmallm/models/piper/de
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/high/de_DE-thorsten-high.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/high/de_DE-thorsten-high.onnx.json
```

Then select the voice in the widget config (it auto-discovers `.onnx` files under `models/piper/`).

## Configuration

`Plasmoid.configuration` keys:

| Key | Default | Description |
|---|---|---|
| `ttsEnabled` | `false` | Master toggle |
| `ttsDefaultVoice` | `fr_FR-upmc-medium` | Voice filename without extension |
| `ttsSpeed` | `1.0` | Speech rate multiplier (0.5–2.0) |
| `ttsAutoRead` | `false` | Auto-read assistant responses |
| `ttsMaxChars` | `1000` | Truncate long messages before TTS |

## How it works

`SpeakText.js` (tool) → `context.exec("piper … --output_file /tmp/plasma-tts-XXXXX.wav")` → `paplay` (PipeWire) or `aplay` (ALSA) for playback.

If `paplay` is not available, the widget falls back to `aplay`, then to writing a `.wav` to disk and notifying the user. PipeWire users get the best experience (no blocking, latency-free mixing).

## Troubleshooting

| Symptom | Fix |
|---|---|
| "piper: command not found" | Run `scripts/install_tts.sh` |
| "model file not found" | Check the voice name in config matches the `.onnx` filename |
| No audio | Check `paplay --version` works, or test with `speaker-test` |
| Robotic / choppy output | Try a `medium` or `high` quality voice (slower but smoother) |
| espeak-ng errors | `sudo apt install libespeak-ng1` |

## Performance

Piper runs at **>1× real-time** on a modern x86_64 CPU even for `high` quality voices. Raspberry Pi 5 handles `medium` voices comfortably. No GPU is used.

The widget streams text to Piper incrementally: as soon as the LLM finishes a sentence, the audio starts playing while the next sentence is being synthesized — no wait for the full response.

## Uninstall

```bash
rm -rf ~/.local/share/plasmallm/{bin/piper,lib/libpiper_phonemize*,models/piper}
```

Disable in widget config or remove `speak_text` from the tool list in `tools/index.js`.