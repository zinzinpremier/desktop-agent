#!/usr/bin/env python3
import sys
import os
import subprocess
import tempfile
import requests
import json

# CONFIGURATION CLOUDFLARE / GUIG DEV
ASR_URL = "https://api.guig.dev/v1/audio/transcriptions"
API_KEY = "911a8b92e3b66b8b36f15d9af5a7f49aba87025accdef28140148fb5f5f247d9"
LANG = "fr"  # Français par défaut

def record_audio(duration=5):
    """Enregistre l'audio via pw-record ou arecord"""
    temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    temp_file.close()

 …  # Mode normal : enregistrer
        print("Enregistrement en cours (5s)...")
        audio_file = record_audio(5)
        if not audio_file:
            sys.exit(1)

    print("Transcription...")
    text = transcribe_audio(audio_file)

    if text:
        print(text)
        # Sauvegarde pour le widget
        with open("/tmp/plasmallm-asr-result.txt", "w") as f:
            f.write(text)
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
