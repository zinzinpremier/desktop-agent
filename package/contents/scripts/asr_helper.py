#!/usr/bin/env python3
import sys
import os
import subprocess
import tempfile
import json
import time
import urllib.request
import urllib.error
import threading
import signal
from pathlib import Path

# Try to import dbus
try:
    import dbus
    import dbus.service
    import dbus.mainloop.glib
    from gi.repository import GLib
    DBUS_AVAILABLE = True
except ImportError:
    DBUS_AVAILABLE = False
    print("Warning: dbus-python or PyGObject not installed. D-Bus daemon will not run.")

# CONFIGURATION CLOUDFLARE / GUIG DEV
ASR_API_URL = os.environ.get("PLASMALLM_ASR_API_URL", "https://api.guig.dev/v1/audio/transcriptions")
ASR_API_KEY = os.environ.get("PLASMALLM_ASR_API_KEY", "911a8b92e3b66b8b36f15d9af5a7f49aba87025accdef28140148fb5f5f247d9")
LANG = os.environ.get("PLASMALLM_ASR_LANG", "fr")
MAX_DURATION = int(os.environ.get("PLASMALLM_ASR_MAX_DURATION", "60"))
ASR_MODE = os.environ.get("PLASMALLM_ASR_MODE", "local").lower()
PLASMALLM_HOME = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))) / "plasmallm"
WHISPER_BIN = PLASMALLM_HOME / "bin" / "whisper-cli"
MODELS_DIR = PLASMALLM_HOME / "models" / "whisper"
MODEL_NAME = os.environ.get("PLASMALLM_ASR_MODEL", "small")

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


if DBUS_AVAILABLE:
    class ASRDaemon(dbus.service.Object):
        def __init__(self, bus):
            super().__init__(bus, OBJECT_PATH)
            self.recording_proc = None
            self.audio_file = None
            self.transcribe_thread = None
            self._stop_timer = None
            self._lock = threading.Lock()

        @dbus.service.method(BUS_NAME, in_signature="ssssss", out_signature="b")
        def StartRecording(self, device="", model="", lang="", api_key="", api_url="", mode="local"):
            """Begin capturing microphone audio."""
            
            # Store runtime configuration for this session
            self.current_lang = lang or LANG
            self.current_api_key = api_key or ASR_API_KEY
            self.current_api_url = api_url or ASR_API_URL
            self.current_mode = mode or ASR_MODE
            self.current_model = model or MODEL_NAME
            
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

                cmd = [
                    pw_record,
                    "--target", "0" if not device else device,
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
                self._save_result(text)
                self._type_text(text)
            else:
                log("Transcription produced empty result")

        def _save_result(self, text: str):
            """Save the result to /tmp/ for QML polling."""
            with open("/tmp/plasmallm-asr-last.txt", "w") as f:
                f.write(text)

        def _transcribe(self, audio: Path) -> str:
            if self.current_mode == "cloud":
                return self._transcribe_cloud(audio)
            else:
                return self._transcribe_local(audio)

        def _transcribe_local(self, audio: Path) -> str:
            """Transcribe using local whisper.cpp."""
            if not WHISPER_BIN.is_file():
                log(f"whisper-cli not found at {WHISPER_BIN}")
                return ""
            model_file = MODELS_DIR / f"ggml-{self.current_model}.bin"
            if not model_file.is_file():
                log(f"Model not found: {model_file}")
                return ""

            cmd = [
                str(WHISPER_BIN),
                "--model", str(model_file),
                "--language", self.current_lang if self.current_lang != "auto" else "auto",
                "--no-timestamps",
                "--threads", str(max(1, os.cpu_count() or 1)),
                "--file", str(audio),
            ]
            log(f"Transcribing with model={self.current_model} lang={self.current_lang}")
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=MAX_DURATION)
            except subprocess.TimeoutExpired:
                log("Transcription timed out")
                return ""

            if result.returncode != 0:
                log(f"whisper-cli exited {result.returncode}: {result.stderr.strip()}")
                return ""

            lines = []
            for raw in result.stdout.splitlines():
                stripped = raw.strip()
                if not stripped: continue
                if stripped.startswith("[") and "]" in stripped:
                    stripped = stripped.split("]", 1)[1].strip()
                lines.append(stripped)
            text = " ".join(lines).strip()
            log(f"Transcribed (local): {text!r}")
            return text

        def _transcribe_cloud(self, audio: Path) -> str:
            """Transcribe using Cloudflare/OpenAI multipart API."""
            log(f"Transcribing audio ({audio.stat().st_size} bytes) via {self.current_api_url} (lang={self.current_lang})")
            
            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    boundary = "----PlasmaLLMAsrBoundary" + str(time.time()).replace(".", "")
                    
                    with open(audio, "rb") as f:
                        audio_data = f.read()
                    
                    body = (
                        f"--{boundary}\r\n"
                        f'Content-Disposition: form-data; name="file"; filename="{audio.name}"\r\n'
                        f"Content-Type: audio/wav\r\n\r\n"
                    ).encode("utf-8") + audio_data
                    
                    body += (
                        f"\r\n--{boundary}\r\n"
                        f'Content-Disposition: form-data; name="language"\r\n\r\n'
                        f"{self.current_lang}\r\n"
                        f"--{boundary}--\r\n"
                    ).encode("utf-8")
                    
                    req = urllib.request.Request(self.current_api_url, data=body, method="POST")
                    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
                    req.add_header("Authorization", f"Bearer {self.current_api_key}")
                    
                    with urllib.request.urlopen(req, timeout=60) as response:
                        result = json.loads(response.read().decode("utf-8"))
                    
                    text = ""
                    if "text" in result:
                        text = result["text"].strip()
                    elif "result" in result and isinstance(result["result"], dict):
                        text = result["result"].get("text", "").strip()
                        
                    if text:
                        log(f"Transcribed: {text!r}")
                        return text
                        
                except Exception as e:
                    log(f"Transcription error (attempt {attempt+1}): {e}")
                    if attempt < max_retries:
                        time.sleep(1)
            
            return ""

        def _type_text(self, text: str) -> None:
            # Prefer clipboard injection then Ctrl+V simulation
            session_type = os.environ.get("XDG_SESSION_TYPE", "x11").lower()
            if session_type == "wayland":
                wl_copy = which("wl-copy")
                wtype = which("wtype")
                if wl_copy:
                    try:
                        subprocess.run([wl_copy], input=text, text=True, check=True)
                        if wtype:
                            subprocess.run([wtype, "-M", "ctrl", "v"], check=False)
                        return
                    except Exception as e:
                        log(f"wl-copy failed: {e}")
                if wtype:
                    try:
                        subprocess.run([wtype, text], check=True)
                        return
                    except Exception:
                        pass
            else:
                xdotool = which("xdotool")
                if xdotool:
                    try:
                        subprocess.run([xdotool, "type", "--clearmodifiers", text], check=True)
                        return
                    except Exception as e:
                        log(f"xdotool failed: {e}")
            log("No working text-injection tool found; transcript saved to /tmp only")


def main():
    if not DBUS_AVAILABLE:
        print("D-Bus not available. Cannot start daemon.", file=sys.stderr)
        sys.exit(1)
        
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    bus_name = dbus.service.BusName(BUS_NAME, bus=bus, allow_replacement=True, do_not_queue=True)
    ASRDaemon(bus)
    log(f"Listening on {BUS_NAME} (max {MAX_DURATION}s, lang={LANG})")

    loop = GLib.MainLoop()

    def shutdown(*_args):
        log("Shutting down")
        loop.quit()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    loop.run()


if __name__ == "__main__":
    main()
