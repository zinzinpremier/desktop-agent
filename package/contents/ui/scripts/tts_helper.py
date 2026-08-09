#!/usr/bin/env python3
"""
Cloudflare TTS Helper - Text-to-Speech via Cloudflare Workers AI (Aura-2)
Supports direct streaming to audio players or file output.
"""

import sys
import os
import json
import subprocess
import tempfile
from pathlib import Path

# Try to import requests; fall back to urllib if not available
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import urllib.request
    import urllib.error


def get_cloudflare_api_key():
    """Retrieve Cloudflare API token from environment or config."""
    # Try environment variable first
    api_key = os.environ.get("CLOUDFLARE_API_TOKEN")
    if api_key:
        return api_key
    
    # Try reading from config file
    config_dir = os.path.expanduser("~/.config/plasmallm")
    config_file = os.path.join(config_dir, "cloudflare.conf")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                for line in f:
                    if line.startswith("CLOUDFLARE_API_TOKEN="):
                        return line.split("=", 1)[1].strip()
        except Exception as e:
            print(f"Warning: Could not read config file: {e}", file=sys.stderr)
    
    return None


def synthesize_cloudflare(text, voice="athena", language="en"):
    """
    Synthesize text using Cloudflare Workers AI Aura-2 API.
    
    Args:
        text: Text to synthesize
        voice: Voice name (athena, apollo, etc.)
        language: Language code (default: en)
    
    Returns:
        bytes: Audio data (MP3) or None on error
    """
    api_key = get_cloudflare_api_key()
    if not api_key:
        print("Error: CLOUDFLARE_API_TOKEN not set", file=sys.stderr)
        return None
    
    # Cloudflare Workers AI endpoint
    url = "https://api.cloudflare.com/client/v4/accounts/me/ai/run/@cf/tts"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "text": text,
        "voice": voice,
    }
    
    try:
        if HAS_REQUESTS:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.content
            else:
                print(
                    f"Error: Cloudflare API returned {response.status_code}",
                    file=sys.stderr,
                )
                print(f"Response: {response.text}", file=sys.stderr)
                return None
        else:
            req = urllib.request.Request(
                url, data=json.dumps(payload).encode("utf-8"), headers=headers
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    return response.read()
            except urllib.error.HTTPError as e:
                print(f"Error: Cloudflare API returned {e.code}", file=sys.stderr)
                print(f"Response: {e.read().decode()}", file=sys.stderr)
                return None
    except Exception as e:
        print(f"Error: Failed to connect to Cloudflare API: {e}", file=sys.stderr)
        return None


def play_audio(audio_data):
    """Play audio using available system player."""
    if not audio_data:
        return False
    
    # Try to write to temp file and play
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name
        
        # Try different audio players
        players = ["paplay", "aplay", "mpv", "ffplay"]
        for player in players:
            try:
                if player == "mpv":
                    subprocess.run(
                        [player, "--no-terminal", "--no-video", tmp_path],
                        timeout=60,
                        check=True,
                    )
                elif player == "aplay":
                    subprocess.run([player, "-q", tmp_path], timeout=60, check=True)
                else:
                    subprocess.run([player, tmp_path], timeout=60, check=True)
                
                # Clean up
                try:
                    os.unlink(tmp_path)
                except:
                    pass
                return True
            except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
                continue
        
        print("Error: No audio player found (tried: paplay, aplay, mpv, ffplay)", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error: Failed to play audio: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: tts_helper.py <text> [voice] [output_file]", file=sys.stderr)
        print("  text: Text to synthesize", file=sys.stderr)
        print("  voice: Voice name (default: athena)", file=sys.stderr)
        print("  output_file: Save to file instead of playing", file=sys.stderr)
        sys.exit(1)
    
    text = sys.argv[1]
    voice = sys.argv[2] if len(sys.argv) > 2 else "athena"
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Limit text length
    max_chars = 5000
    if len(text) > max_chars:
        text = text[:max_chars]
        print(
            f"Warning: Text truncated to {max_chars} characters",
            file=sys.stderr,
        )
    
    # Synthesize
    print(f"Synthesizing {len(text)} characters with voice '{voice}'...", file=sys.stderr)
    audio_data = synthesize_cloudflare(text, voice)
    
    if not audio_data:
        print("Error: Failed to synthesize speech", file=sys.stderr)
        sys.exit(1)
    
    print(f"Synthesized {len(audio_data)} bytes of audio", file=sys.stderr)
    
    # Output or play
    if output_file:
        try:
            with open(output_file, "wb") as f:
                f.write(audio_data)
            print(f"Saved to: {output_file}", file=sys.stderr)
        except Exception as e:
            print(f"Error: Failed to write output file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        if not play_audio(audio_data):
            sys.exit(1)
    
    print("Done", file=sys.stderr)


if __name__ == "__main__":
    main()
