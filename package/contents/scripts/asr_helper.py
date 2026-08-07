#!/usr/bin/env python3
# asr_helper.py — D-Bus daemon that captures microphone audio via PipeWire
# and transcribes it with whisper.cpp, then types the result at the cursor.
#
# Activated by PlasmaLLM via a session D-Bus signal
# (org.plasmallm.ASR / StartRecording, StopRecording).
#
# Configuration is read from environment variables so the systemd unit
# can override them:
#   PLASMALLM_ASR_MODEL  — ggml model basename without .bin (default: base)
#   PLASMALLM_ASR_LANG   — language code, or "auto" (default: auto)
#   PLASMALLM_ASR_MAX_DURATION — auto-stop recording after N seconds (default: 60)

import os
import sys
import json
import signal
import subprocess
import tempfile
import threading
import time
from pathlib import Path

import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib

PLASMALLM_HOME = Path(os.environ.get(
    "XDG_DATA_HOME",
    str(Path.home() / ".local" / "share")
)) / "plasmallm"

WHISPER_BIN = PLASMALLM_HOME / "bin" / "whisper-cli"
MODELS_DIR = PLASMALLM_HOME / "models" / "whisper"
MODEL_NAME = os.environ.get("PLASMALLM_ASR_MODEL", "base")
LANG = os.environ.get("PLASMALLM_ASR_LANG", "fr")
MAX_DURATION = int(os.environ.get("PLASMALLM_ASR_MAX_DURATION", "60"))

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

    @dbus.service.method(BUS_NAME, in_signature="s", out_signature="b")
    def StartRecording(self, target=""):
        """Begin capturing microphone audio. `target` optionally selects the PipeWire source."""
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
        if not WHISPER_BIN.is_file():
            log(f"whisper-cli not found at {WHISPER_BIN}")
            return ""
        model = MODELS_DIR / f"ggml-{MODEL_NAME}.bin"
        if not model.is_file():
            log(f"Model not found: {model}")
            return ""

        cmd = [
            str(WHISPER_BIN),
            "--model", str(model),
            "--language", LANG if LANG != "auto" else "auto",
            "--no-timestamps",
            "--threads", str(max(1, os.cpu_count() or 1)),
            "--file", str(audio),
        ]
        log(f"Transcribing with model={MODEL_NAME} lang={LANG}")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=MAX_DURATION,
            )
        except subprocess.TimeoutExpired:
            log("Transcription timed out")
            return ""

        if result.returncode != 0:
            log(f"whisper-cli exited {result.returncode}: {result.stderr.strip()}")
            return ""

        # whisper-cli output looks like:
        # [00:00:00.000 --> 00:00:01.234]  Hello world.
        # We strip the timestamps and join.
        lines = []
        for raw in result.stdout.splitlines():
            stripped = raw.strip()
            if not stripped:
                continue
            # Strip "[hh:mm:ss.mmm --> hh:mm:ss.mmm]  " prefix if present
            if stripped.startswith("[") and "]" in stripped:
                stripped = stripped.split("]", 1)[1].strip()
            lines.append(stripped)
        text = " ".join(lines).strip()
        log(f"Transcribed: {text!r}")
        return text

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
    log(f"Listening on {BUS_NAME} (max {MAX_DURATION}s, model={MODEL_NAME}, lang={LANG})")

    loop = GLib.MainLoop()

    def shutdown(*_args):
        log("Shutting down")
        loop.quit()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    loop.run()


if __name__ == "__main__":
    main()