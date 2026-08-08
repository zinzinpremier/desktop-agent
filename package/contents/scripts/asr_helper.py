#!/usr/bin/env python3
# asr_helper.py — D-Bus daemon that captures microphone audio via PipeWire
# and transcribes it using the Cloudflare ASR API or local Whisper.
#
# Activated by PlasmaLLM via a session D-Bus signal
# (org.plasmallm.ASR / StartRecording, StopRecording).
#
# Configuration is read from environment variables so the systemd unit
# can override them:
#   PLASMALLM_ASR_MAX_DURATION — auto-stop recording after N seconds (default: 60)
#   PLASMALLM_ASR_LANG         — language code (default: fr)
#   PLASMALLM_ASR_MODE         — "cloud" or "local" (default: cloud)
#   PLASMALLM_ASR_API_URL      — Cloudflare API endpoint (default: https://api.guig.dev/transcribe)
#   PLASMALLM_ASR_OPENAI_COMPATIBLE — use OpenAI-compatible endpoint (default: false)

import os
import sys
import json
import signal
import subprocess
import tempfile
import threading
import time
import urllib.request
import urllib.error
from pathlib import Path

import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib

PLASMALLM_HOME = Path(os.environ.get(
    "XDG_DATA_HOME",
    str(Path.home() / ".local" / "share")
)) / "plasmallm"

MODELS_DIR = PLASMALLM_HOME / "models" / "whisper"
LANG = os.environ.get("PLASMALLM_ASR_LANG", "fr")
MAX_DURATION = int(os.environ.get("PLASMALLM_ASR_MAX_DURATION", "60"))
ASR_MODE = os.environ.get("PLASMALLM_ASR_MODE", "cloud").lower()
USE_OPENAI_COMPATIBLE = os.environ.get("PLASMALLM_ASR_OPENAI_COMPATIBLE", "false").lower() == "true"

# Cloudflare ASR API endpoints
ASR_API_URL = os.environ.get("PLASMALLM_ASR_API_URL", "https://api.guig.dev/transcribe")
OPENAI_COMPATIBLE_URL = "https://api.guig.dev/v1/audio/transcriptions"

BUS_NAME = "org.plasmallm.ASR"
OBJECT_PATH = "/org/plasmallm/ASR"


def log(msg: str) -> None:
    print(f"[asr] {msg}", flush=True)


def which(cmd: str) -> str | None:
    for p in os.environ.get("PATH", "").split(":"):
        candidate = Path(p) / cmd
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


class ASRDaemon(dbus.service.Object):
    def __init__(self, bus):
        super().__init__(bus, OBJECT_PATH)
        self.recording_proc: subprocess.Popen | None = None
        self.audio_file: Path | None = None
        self.transcribe_thread: threading.Thread | None = None
        self._stop_timer: threading.Timer | None = None
        self._lock = threading.Lock()

    @dbus.service.method(BUS_NAME, in_signature="ss", out_signature="b")
    def StartRecording(self, target="", model=""):
        """Begin capturing microphone audio. `target` optionally selects the
        PipeWire source. The `model` parameter is ignored (kept for API compatibility)."""
        with self._lock:
            if self.recording_proc is not None:
                log("Already recording — ignoring StartRecording")
                return False

            # Prefer pw-record (PipeWire); fall back to pw-cat if needed
            pw_record = which("pw-record")
            if pw_record is None:
                pw_record = which("pw-cat")

            if pw_record is None:
                log("pw-record / pw-cat not found — is pipewire-audio-client-libraries installed?")
                return False

            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False, prefix="plasmallm-asr-")
            tmp.close()
            self.audio_file = Path(tmp.name)

            cmd = [pw_record]
            # Optional PipeWire source target from widget config; empty = session default.
            if target:
                cmd += ["--target", str(target)]
            cmd += [
                "--format", "s16",
                "--rate", "16000",
                "--channels", "1",
                self.audio_file.name,
            ]
            log(f"Starting recorder: {' '.join(cmd)}")
            try:
                self.recording_proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                )
            except OSError as e:
                log(f"Failed to start recorder: {e}")
                self.audio_file.unlink(missing_ok=True)
                self.audio_file = None
                return False

            # Auto-stop after MAX_DURATION
            self._stop_timer = threading.Timer(MAX_DURATION, self._auto_stop)
            self._stop_timer.start()
            return True

    def _auto_stop(self):
        log(f"Auto-stop after {MAX_DURATION}s")
        self.StopRecording()

    @dbus.service.method(BUS_NAME, in_signature="", out_signature="b")
    def StopRecording(self):
        """Stop capturing and transcribe the captured audio."""
        with self._lock:
            proc = self.recording_proc
            audio = self.audio_file
            self.recording_proc = None
            self.audio_file = None
            if self._stop_timer is not None:
                self._stop_timer.cancel()
                self._stop_timer = None

        if proc is None:
            log("Not recording — nothing to stop")
            return False

        try:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=1)
        except OSError as e:
            log(f"Error stopping recorder: {e}")

        if audio is None or not audio.exists():
            log("No audio file captured")
            return False

        # Normalize mic level — quiet mics (e.g. wireless headsets) otherwise
        # fall below whisper's no-speech threshold and yield empty transcripts.
        sox = which("sox")
        if sox:
            norm = audio.with_suffix(".norm.wav")
            try:
                r = subprocess.run([sox, str(audio), str(norm), "gain", "-n", "-3"],
                                   capture_output=True, timeout=30)
                if r.returncode == 0 and norm.exists() and norm.stat().st_size > 100:
                    audio = norm
                else:
                    norm.unlink(missing_ok=True)
            except (OSError, subprocess.TimeoutExpired):
                norm.unlink(missing_ok=True)

        # Spawn transcription on a worker thread so the D-Bus reply is fast
        self.transcribe_thread = threading.Thread(
            target=self._transcribe_and_type,
            args=(audio,),
            daemon=True,
        )
        self.transcribe_thread.start()
        return True

    def _transcribe_and_type(self, audio: Path):
        try:
            text = self._transcribe(audio)
        finally:
            try:
                audio.unlink(missing_ok=True)
            except OSError:
                pass

        if text:
            # Always publish the transcript to a known file — the widget polls
            # it after StopRecording and inserts the text into its input field.
            try:
                Path("/tmp/plasmallm-asr-last.txt").write_text(text)
            except OSError:
                pass
            self._type_text(text)
        else:
            log("Transcription produced empty result")

    def _transcribe(self, audio: Path) -> str:
        """Transcribe audio using Cloudflare ASR API or local Whisper."""
        if ASR_MODE == "local":
            return self._transcribe_local(audio)
        else:
            return self._transcribe_cloud(audio)

    def _transcribe_cloud(self, audio: Path) -> str:
        """Transcribe audio using the Cloudflare ASR API."""
        api_url = OPENAI_COMPATIBLE_URL if USE_OPENAI_COMPATIBLE else ASR_API_URL
        log(f"Transcribing with Cloudflare ASR API (mode={'openai' if USE_OPENAI_COMPATIBLE else 'native'}, lang={LANG}, url={api_url})")
        
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                if USE_OPENAI_COMPATIBLE:
                    # OpenAI-compatible endpoint
                    boundary = "----PlasmaLLMASRBoundary" + str(time.time()).replace(".", "")
                    
                    with open(audio, "rb") as f:
                        audio_data = f.read()
                    
                    body = (
                        f"--{boundary}\r\n"
                        f'Content-Disposition: form-data; name="file"; filename="recording.wav"\r\n'
                        f"Content-Type: audio/wav\r\n\r\n"
                    ).encode("utf-8") + audio_data + (
                        f"\r\n--{boundary}\r\n"
                        f'Content-Disposition: form-data; name="model"\r\n\r\n'
                        f"whisper-1\r\n"
                        f"\r\n--{boundary}\r\n"
                        f'Content-Disposition: form-data; name="language"\r\n\r\n'
                        f"{LANG}\r\n"
                        f"--{boundary}--\r\n"
                    ).encode("utf-8")
                    
                    req = urllib.request.Request(api_url, data=body, method="POST")
                    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
                else:
                    # Native Cloudflare endpoint
                    boundary = "----PlasmaLLMASRBoundary" + str(time.time()).replace(".", "")
                    
                    with open(audio, "rb") as f:
                        audio_data = f.read()
                    
                    body = (
                        f"--{boundary}\r\n"
                        f'Content-Disposition: form-data; name="audio"; filename="recording.wav"\r\n'
                        f"Content-Type: audio/wav\r\n\r\n"
                    ).encode("utf-8") + audio_data + (
                        f"\r\n--{boundary}\r\n"
                        f'Content-Disposition: form-data; name="language"\r\n\r\n'
                        f"{LANG}\r\n"
                        f"--{boundary}--\r\n"
                    ).encode("utf-8")
                    
                    req = urllib.request.Request(ASR_API_URL, data=body, method="POST")
                    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
                
                log(f"Sending audio to {api_url} (attempt {attempt + 1}/{max_retries + 1})")
                
                with urllib.request.urlopen(req, timeout=MAX_DURATION) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    
                if USE_OPENAI_COMPATIBLE:
                    text = result.get("text", "").strip()
                else:
                    text = result.get("text", "").strip()
                    detected_lang = result.get("language", LANG)
                    log(f"Detected language: {detected_lang}")
                    
                log(f"Transcribed: {text!r}")
                return text
                
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8', errors='ignore')
                log(f"ASR API HTTP error (attempt {attempt + 1}): {e.code} - {error_body}")
                if attempt < max_retries and e.code >= 500:
                    time.sleep(1 * (attempt + 1))
                    continue
                return ""
            except urllib.error.URLError as e:
                log(f"ASR API URL error (attempt {attempt + 1}): {e.reason}")
                if attempt < max_retries:
                    time.sleep(1 * (attempt + 1))
                    continue
                return ""
            except Exception as e:
                log(f"ASR API error (attempt {attempt + 1}): {type(e).__name__}: {e}")
                if attempt < max_retries:
                    time.sleep(1 * (attempt + 1))
                    continue
                return ""
        
        return ""

    def _transcribe_local(self, audio: Path) -> str:
        """Transcribe audio using local Whisper.cpp installation."""
        whisper_cpp = MODELS_DIR / "main"
        model_path = MODELS_DIR / "ggml-base.bin"
        
        if not whisper_cpp.exists():
            log("Whisper.cpp not found. Run scripts/install_asr.sh to install.")
            return ""
        
        if not model_path.exists():
            log(f"Model not found at {model_path}. Run scripts/install_asr.sh to download.")
            return ""
        
        log(f"Transcribing locally with Whisper.cpp (lang={LANG})")
        
        try:
            cmd = [
                str(whisper_cpp),
                "-m", str(model_path),
                "-f", str(audio),
                "-l", LANG,
                "--no-timestamps",
                "-otxt",
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=MAX_DURATION)
            
            if result.returncode != 0:
                log(f"Whisper.cpp failed: {result.stderr}")
                return ""
            
            txt_file = Path(str(audio) + ".txt")
            if txt_file.exists():
                text = txt_file.read_text().strip()
                txt_file.unlink()
                log(f"Transcribed: {text!r}")
                return text
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            log("Whisper.cpp timed out")
            return ""
        except Exception as e:
            log(f"Local transcription error: {type(e).__name__}: {e}")
            return ""

    def _type_text(self, text: str) -> None:
        # Prefer clipboard injection then Ctrl+V simulation — that survives
        # most focus constraints. wtype/xdotool type are direct fallbacks.
        session_type = os.environ.get("XDG_SESSION_TYPE", "x11").lower()
        if session_type == "wayland":
            wl_copy = which("wl-copy")
            wtype = which("wtype")
            if wl_copy:
                try:
                    subprocess.run([wl_copy], input=text, text=True, check=True)
                    # Trigger paste via the keyboard
                    if wtype:
                        subprocess.run([wtype, "-M", "ctrl", "v"], check=False)
                    return
                except (OSError, subprocess.CalledProcessError) as e:
                    log(f"wl-copy failed: {e}")
            if wtype:
                try:
                    subprocess.run([wtype, text], check=True)
                    return
                except (OSError, subprocess.CalledProcessError) as e:
                    log(f"wtype failed: {e}")
        else:
            xdotool = which("xdotool")
            if xdotool:
                try:
                    subprocess.run([xdotool, "type", "--clearmodifiers", text], check=True)
                    return
                except (OSError, subprocess.CalledProcessError) as e:
                    log(f"xdotool failed: {e}")
        log("No working text-injection tool found; transcript printed only")


def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    bus_name = dbus.service.BusName(BUS_NAME, bus=bus, allow_replacement=True, do_not_queue=True)
    ASRDaemon(bus)
    log(f"Listening on {BUS_NAME} (mode={ASR_MODE}, max {MAX_DURATION}s, lang={LANG})")
    if ASR_MODE == "cloud":
        log(f"API: {OPENAI_COMPATIBLE_URL if USE_OPENAI_COMPATIBLE else ASR_API_URL}")
    else:
        log(f"Local model: {MODELS_DIR / 'ggml-base.bin'}")

    loop = GLib.MainLoop()

    def shutdown(*_args):
        log("Shutting down")
        loop.quit()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    loop.run()


if __name__ == "__main__":
    main()