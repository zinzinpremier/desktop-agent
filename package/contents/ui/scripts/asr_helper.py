#!/usr/bin/env python3
"""
Cloudflare ASR Helper - Speech-to-Text via Cloudflare Workers AI or OpenAI-compatible endpoint
Supports audio file input and transcription output.
"""

import sys
import os
import json
import subprocess
from pathlib import Path

# Try to import requests; fall back to urllib if not available
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import urllib.request
    import urllib.error


def get_cloudflare_config():
    """Retrieve Cloudflare config from environment or config file."""
    config = {
        "api_token": os.environ.get("CLOUDFLARE_API_TOKEN"),
        "account_id": os.environ.get("CLOUDFLARE_ACCOUNT_ID"),
        "endpoint": os.environ.get("ASR_ENDPOINT"),
        "mode": os.environ.get("ASR_MODE", "cloudflare"),  # cloudflare or openai
    }
    
    # Try reading from config file
    config_dir = os.path.expanduser("~/.config/plasmallm")
    config_file = os.path.join(config_dir, "cloudflare.conf")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("CLOUDFLARE_API_TOKEN="):
                        config["api_token"] = line.split("=", 1)[1]
                    elif line.startswith("CLOUDFLARE_ACCOUNT_ID="):
                        config["account_id"] = line.split("=", 1)[1]
                    elif line.startswith("ASR_ENDPOINT="):
                        config["endpoint"] = line.split("=", 1)[1]
                    elif line.startswith("ASR_MODE="):
                        config["mode"] = line.split("=", 1)[1]
        except Exception as e:
            print(f"Warning: Could not read config file: {e}", file=sys.stderr)
    
    return config


def transcribe_cloudflare(audio_file, language="auto"):
    """
    Transcribe audio using Cloudflare Workers AI.
    
    Args:
        audio_file: Path to audio file
        language: Language code (auto, en, fr, etc.)
    
    Returns:
        str: Transcription text or None on error
    """
    config = get_cloudflare_config()
    
    if not config["api_token"]:
        print("Error: CLOUDFLARE_API_TOKEN not set", file=sys.stderr)
        return None
    
    if not config["account_id"]:
        print("Error: CLOUDFLARE_ACCOUNT_ID not set", file=sys.stderr)
        return None
    
    url = f"https://api.cloudflare.com/client/v4/accounts/{config['account_id']}/ai/run/@cf/whisper"
    
    headers = {
        "Authorization": f"Bearer {config['api_token']}",
    }
    
    try:
        # Read audio file
        if not os.path.exists(audio_file):
            print(f"Error: Audio file not found: {audio_file}", file=sys.stderr)
            return None
        
        with open(audio_file, "rb") as f:
            audio_data = f.read()
        
        # Prepare multipart form data
        if HAS_REQUESTS:
            files = {
                "file": ("audio.wav", audio_data, "audio/wav"),
            }
            data = {}
            if language and language != "auto":
                data["language"] = language
            
            response = requests.post(
                url, files=files, data=data, headers=headers, timeout=60
            )
            if response.status_code == 200:
                result = response.json()
                if "result" in result and "text" in result["result"]:
                    return result["result"]["text"]
                else:
                    print(
                        f"Error: Unexpected response format: {result}",
                        file=sys.stderr,
                    )
                    return None
            else:
                print(
                    f"Error: Cloudflare API returned {response.status_code}",
                    file=sys.stderr,
                )
                print(f"Response: {response.text}", file=sys.stderr)
                return None
        else:
            # urllib fallback (more complex with multipart)
            print(
                "Error: requests library not available, install it for ASR support",
                file=sys.stderr,
            )
            return None
    except Exception as e:
        print(f"Error: Failed to transcribe audio: {e}", file=sys.stderr)
        return None


def transcribe_openai_compatible(audio_file, endpoint, api_key, language="en"):
    """
    Transcribe using OpenAI-compatible endpoint (e.g., api.guig.dev).
    
    Args:
        audio_file: Path to audio file
        endpoint: API endpoint URL
        api_key: API key (optional)
        language: Language code
    
    Returns:
        str: Transcription text or None on error
    """
    try:
        if not os.path.exists(audio_file):
            print(f"Error: Audio file not found: {audio_file}", file=sys.stderr)
            return None
        
        with open(audio_file, "rb") as f:
            audio_data = f.read()
        
        if HAS_REQUESTS:
            files = {
                "file": ("audio.wav", audio_data, "audio/wav"),
            }
            data = {
                "language": language,
            }
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            response = requests.post(
                endpoint, files=files, data=data, headers=headers, timeout=60
            )
            if response.status_code == 200:
                result = response.json()
                if "text" in result:
                    return result["text"]
                else:
                    print(
                        f"Error: Unexpected response format: {result}",
                        file=sys.stderr,
                    )
                    return None
            else:
                print(
                    f"Error: API returned {response.status_code}",
                    file=sys.stderr,
                )
                print(f"Response: {response.text}", file=sys.stderr)
                return None
        else:
            print(
                "Error: requests library not available, install it for ASR support",
                file=sys.stderr,
            )
            return None
    except Exception as e:
        print(f"Error: Failed to transcribe audio: {e}", file=sys.stderr)
        return None


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: asr_helper.py <audio_file> [language] [endpoint] [api_key]", file=sys.stderr)
        print("  audio_file: Path to audio file", file=sys.stderr)
        print("  language: Language code (default: auto)", file=sys.stderr)
        print("  endpoint: Custom endpoint for OpenAI-compatible API", file=sys.stderr)
        print("  api_key: API key for endpoint", file=sys.stderr)
        sys.exit(1)
    
    audio_file = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "auto"
    endpoint = sys.argv[3] if len(sys.argv) > 3 else None
    api_key = sys.argv[4] if len(sys.argv) > 4 else None
    
    config = get_cloudflare_config()
    
    # Determine which API to use
    if endpoint:
        # Use custom endpoint
        print(f"Using OpenAI-compatible endpoint: {endpoint}", file=sys.stderr)
        transcription = transcribe_openai_compatible(audio_file, endpoint, api_key, language)
    elif config["endpoint"]:
        # Use configured endpoint
        print(f"Using configured endpoint: {config['endpoint']}", file=sys.stderr)
        transcription = transcribe_openai_compatible(
            audio_file, config["endpoint"], config.get("api_key"), language
        )
    else:
        # Use Cloudflare
        print("Using Cloudflare Workers AI", file=sys.stderr)
        transcription = transcribe_cloudflare(audio_file, language)
    
    if transcription:
        print(transcription)
        sys.exit(0)
    else:
        print("Error: Failed to transcribe audio", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
