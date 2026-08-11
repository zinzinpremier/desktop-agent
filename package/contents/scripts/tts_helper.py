#!/usr/bin/env python3
# tts_helper.py — Text-to-Speech daemon supporting both local Piper and Cloudflare TTS API.
#
# Activated by PlasmaLLM via D-Bus or direct command execution.
#
# Configuration is read from environment variables:
#   PLASMALLM_TTS_MODE          — "cloud" or "local" (default: cloud)
#   PLASMALLM_TTS_API_URL       — Cloudflare TTS API endpoint (default: https://api.guig.dev/v1/audio/speech)
#   PLASMALLM_TTS_VOICE         — Voice name for cloud (default: "athena")
#   PLASMALLM_TTS_SPEED         — Speed multiplier (default: 1.0)
#   PLASMALLM_TTS_LANG          — Language code (default: fr)
#   PLASMALLM_TTS_MODEL         — Model name (default: aura-2)

import os
import sys
import json
import time
import subprocess
import tempfile
import urllib.request
import urllib.error
from pathlib import Path

PLASMALLM_HOME = Path(os.environ.get(
    "XDG_DATA_HOME",
    str(Path.home() / ".local" / "share")
)) / "plasmallm"

PIPER_BIN = PLASMALLM_HOME / "bin" / "piper"
PIPER_LIB_DIR = PLASMALLM_HOME / "lib"
VOICES_DIR = PLASMALLM_HOME / "models" / "piper"

TTS_MODE = os.environ.get("PLASMALLM_TTS_MODE", "cloud").lower()
TTS_API_URL = os.environ.get("PLASMALLM_TTS_API_URL", "https://api.guig.dev/v1/audio/speech")
TTS_VOICE = os.environ.get("PLASMALLM_TTS_VOICE", "athena")
TTS_SPEED = float(os.environ.get("PLASMALLM_TTS_SPEED", "1.0"))
TTS_LANG = os.environ.get("PLASMALLM_TTS_LANG", "fr")
TTS_MODEL = os.environ.get("PLASMALLM_TTS_MODEL", "aura-2")


def log(msg: str) -> None:
    print(f"[tts] {msg}", flush=True)


def which(cmd: str) -> str | None:
    for p in os.environ.get("PATH", "").split(":"):
        candidate = Path(p) / cmd
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def speak_cloud(text: str, output_wav: Path) -> bool:
    """Synthesize speech using Cloudflare TTS API (OpenAI-compatible endpoint)."""
    log(f"Using Cloudflare TTS API (model={TTS_MODEL}, voice={TTS_VOICE}, lang={TTS_LANG}, speed={TTS_SPEED})")
    
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            # OpenAI-compatible format: POST /v1/audio/speech
            payload = json.dumps({
                "model": TTS_MODEL,
                "input": text,
                "voice": TTS_VOICE,
                "speed": TTS_SPEED,
            }).encode("utf-8")
            
            req = urllib.request.Request(
                TTS_API_URL,
                data=payload,
                method="POST",
            )
            req.add_header("Content-Type", "application/json")
            req.add_header("User-Agent", "Mozilla/5.0 (X11; Linux x86_64) PlasmaLLM/1.0")
            req.add_header("Accept", "*/*")
            
            log(f"Sending TTS request to {TTS_API_URL} (attempt {attempt + 1}/{max_retries + 1})")
            
            with urllib.request.urlopen(req, timeout=60) as response:
                audio_data = response.read()
                
            if len(audio_data) < 100:  # WAV header is 44 bytes, minimal audio should be larger
                log("Received audio too small, likely an error")
                return False
                
            with open(output_wav, "wb") as f:
                f.write(audio_data)
                
            log(f"Audio saved to {output_wav} ({len(audio_data)} bytes)")
            return True
            
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8', errors='ignore')
            log(f"TTS API HTTP error (attempt {attempt + 1}): {e.code} - {error_body}")
            if attempt < max_retries and e.code >= 500:
                time.sleep(1 * (attempt + 1))
                continue
            return False
        except urllib.error.URLError as e:
            log(f"TTS API URL error (attempt {attempt + 1}): {e.reason}")
            if attempt < max_retries:
                time.sleep(1 * (attempt + 1))
                continue
            return False
        except Exception as e:
            log(f"TTS API error (attempt {attempt + 1}): {type(e).__name__}: {e}")
            if attempt < max_retries:
                time.sleep(1 * (attempt + 1))
                continue
            return False
    
    return False


def speak_local(text: str, output_wav: Path) -> bool:
    """Synthesize speech using local Piper installation."""
    if not PIPER_BIN.exists():
        log(f"Piper binary not found at {PIPER_BIN}. Run scripts/install_tts.sh")
        return False
    
    # Find voice model
    voice_name = TTS_VOICE.replace("/", "_").replace("-", "_")
    voice_model = VOICES_DIR / f"{voice_name}.onnx"
    
    if not voice_model.exists():
        # Try to find any French voice as fallback
        voice_model = next(VOICES_DIR.glob("**/fr_*.onnx"), None)
        if not voice_model:
            log(f"Voice model not found. Install voices with scripts/install_tts.sh")
            return False
        log(f"Using fallback voice: {voice_model.name}")
    
    length_scale = 1.0 / TTS_SPEED
    
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = str(PIPER_LIB_DIR) + ":" + env.get("LD_LIBRARY_PATH", "")
    
    cmd = [
        str(PIPER_BIN),
        "--model", str(voice_model),
        "--length_scale", f"{length_scale:.3f}",
        "--output_file", str(output_wav),
    ]
    
    log(f"Running Piper: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            input=text,
            text=True,
            capture_output=True,
            env=env,
            timeout=60,
        )
        
        if result.returncode != 0:
            log(f"Piper failed: {result.stderr.decode('utf-8', errors='ignore')}")
            return False
        
        if not output_wav.exists() or output_wav.stat().st_size < 100:
            log("Piper produced no or invalid output")
            return False
        
        log(f"Audio saved to {output_wav} ({output_wav.stat().st_size} bytes)")
        return True
        
    except subprocess.TimeoutExpired:
        log("Piper timed out")
        return False
    except Exception as e:
        log(f"Piper error: {type(e).__name__}: {e}")
        return False


def play_audio(wav_path: Path) -> bool:
    """Play audio file using paplay (PipeWire), ffplay (FFmpeg), pw-play (PipeWire), or aplay (ALSA)."""
    # Try paplay first (PipeWire/PulseAudio)
    paplay = which("paplay")
    if paplay:
        try:
            result = subprocess.run([paplay, str(wav_path)], timeout=60)
            if result.returncode == 0:
                return True
        except Exception as e:
            log(f"paplay failed: {e}")
    
    # Try ffplay (FFmpeg - most reliable fallback)
    ffplay = which("ffplay")
    if ffplay:
        try:
            # Use -nodisp to disable video window, -autoexit to exit after playback
            result = subprocess.run([ffplay, "-nodisp", "-autoexit", str(wav_path)], 
                                  timeout=60, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if result.returncode == 0:
                return True
        except Exception as e:
            log(f"ffplay failed: {e}")
    
    # Try pw-play (PipeWire native)
    pw_play = which("pw-play")
    if pw_play:
        try:
            result = subprocess.run([pw_play, str(wav_path)], timeout=60)
            if result.returncode == 0:
                return True
        except Exception as e:
            log(f"pw-play failed: {e}")
    
    # Try aplay (ALSA - last resort, may not work in containers)
    aplay = which("aplay")
    if aplay:
        try:
            result = subprocess.run([aplay, "-q", str(wav_path)], timeout=60)
            if result.returncode == 0:
                return True
        except Exception as e:
            log(f"aplay failed: {e}")
    
    log("No working audio player found (tried: paplay, ffplay, pw-play, aplay)")
    log(f"Audio file saved but not played: {wav_path}")
    return True  # Return True since TTS synthesis succeeded even if playback failed


def speak(text: str) -> bool:
    """Main entry point: synthesize and play speech."""
    if not text.strip():
        log("Empty text, nothing to speak")
        return False
    
    # Truncate very long texts
    max_chars = int(os.environ.get("PLASMALLM_TTS_MAX_CHARS", "1000"))
    if len(text) > max_chars:
        text = text[:max_chars]
        log(f"Text truncated to {max_chars} characters")
    
    # Create temp file for output
    tmp_wav = Path(tempfile.mktemp(suffix=".wav", prefix="plasmallm-tts-"))
    
    try:
        # Choose synthesis method
        if TTS_MODE == "local":
            success = speak_local(text, tmp_wav)
        else:
            success = speak_cloud(text, tmp_wav)
        
        if not success:
            return False
        
        # Play the audio
        return play_audio(tmp_wav)
        
    finally:
        # Cleanup
        try:
            tmp_wav.unlink(missing_ok=True)
        except OSError:
            pass


def main():
    import time
    
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <text>")
        print(f"Mode: {TTS_MODE}")
        if TTS_MODE == "cloud":
            print(f"API: {TTS_API_URL}")
            print(f"Model: {TTS_MODEL}, Voice: {TTS_VOICE}, Lang: {TTS_LANG}, Speed: {TTS_SPEED}")
        else:
            print(f"Piper: {PIPER_BIN}")
            print(f"Voices dir: {VOICES_DIR}")
        sys.exit(1)
    
    text = " ".join(sys.argv[1:])
    log(f"Starting TTS (mode={TTS_MODE})")
    
    if speak(text):
        log("TTS completed successfully")
        sys.exit(0)
    else:
        log("TTS failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
