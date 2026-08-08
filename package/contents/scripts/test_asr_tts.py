#!/usr/bin/env python3
"""Test script for ASR and TTS Cloudflare endpoints."""

import urllib.request
import json
import sys

def test_health():
    """Test API health endpoint."""
    try:
        req = urllib.request.Request('https://api.guig.dev/health', method='GET')
        req.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) PlasmaLLM/1.0')
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            print("✓ Health Check:", data)
            return True
    except Exception as e:
        print(f"✗ Health Check Failed: {e}")
        return False

def test_asr_transcribe():
    """Test ASR transcribe endpoint (requires actual audio file)."""
    print("\n--- ASR Transcribe Test ---")
    print("Endpoint: https://api.guig.dev/transcribe")
    print("Method: POST multipart/form-data")
    print("Fields: audio (file), language (optional)")
    print("Response: {\"text\": \"...\", \"language\": \"fr\"}")
    print("\nTo test manually:")
    print("  curl -X POST https://api.guig.dev/transcribe \\")
    print("    -F 'audio=@recording.wav' \\")
    print("    -F 'language=fr'")
    return True

def test_tts_speech():
    """Test TTS speech synthesis endpoint."""
    print("\n--- TTS Speech Test ---")
    try:
        payload = json.dumps({
            'model': 'aura-2',
            'input': 'Bonjour, ceci est un test de synthèse vocale.',
            'voice': 'athena'
        }).encode('utf-8')
        
        req = urllib.request.Request('https://api.guig.dev/v1/audio/speech', data=payload, method='POST')
        req.add_header('Content-Type', 'application/json')
        req.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) PlasmaLLM/1.0')
        req.add_header('Accept', '*/*')
        
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            if len(data) > 1000:
                print(f"✓ TTS Success: Received {len(data)} bytes of audio")
                return True
            else:
                print(f"✗ TTS Warning: Received only {len(data)} bytes")
                return False
    except Exception as e:
        print(f"✗ TTS Failed: {e}")
        return False

def test_openai_compatible_asr():
    """Test OpenAI-compatible ASR endpoint."""
    print("\n--- OpenAI-Compatible ASR Test ---")
    print("Endpoint: https://api.guig.dev/v1/audio/transcriptions")
    print("Method: POST multipart/form-data")
    print("Fields: file (audio), model (whisper-1), language (optional)")
    print("Response: {\"text\": \"...\"}")
    return True

def show_config():
    """Show configuration summary."""
    print("\n" + "="*60)
    print("PLASMALLM CONFIGURATION SUMMARY")
    print("="*60)
    
    print("\n📡 ASR (Speech-to-Text):")
    print("   Mode: cloud (default) or local")
    print("   Native Endpoint: https://api.guig.dev/transcribe")
    print("   OpenAI-Compatible: https://api.guig.dev/v1/audio/transcriptions")
    print("   Env vars: PLASMALLM_ASR_MODE, PLASMALLM_ASR_LANG, PLASMALLM_ASR_API_URL")
    
    print("\n🔊 TTS (Text-to-Speech):")
    print("   Mode: cloud (default) or local")
    print("   Endpoint: https://api.guig.dev/v1/audio/speech")
    print("   Model: aura-2")
    print("   Voices: amalthea, andromeda, apollo, arcas, aries, asteria, athena, atlas, etc.")
    print("   Env vars: PLASMALLM_TTS_MODE, PLASMALLM_TTS_VOICE, PLASMALLM_TTS_MODEL")
    
    print("\n📋 Available Endpoints:")
    print("   GET  https://api.guig.dev/health           - Service health")
    print("   GET  https://api.guig.dev/models           - Available models")
    print("   POST https://api.guig.dev/transcribe        - ASR (native)")
    print("   POST https://api.guig.dev/v1/audio/transcriptions - ASR (OpenAI-compatible)")
    print("   POST https://api.guig.dev/v1/audio/speech   - TTS (OpenAI-compatible)")
    print("   GET  https://api.guig.dev/v1/models         - Models (OpenAI-compatible)")
    print("="*60)

if __name__ == "__main__":
    print("PlasmaLLM ASR/TTS Cloudflare Integration Test")
    print("-" * 50)
    
    results = []
    results.append(("Health Check", test_health()))
    results.append(("TTS Speech", test_tts_speech()))
    test_asr_transcribe()
    test_openai_compatible_asr()
    show_config()
    
    print("\n" + "="*60)
    print("TEST RESULTS:")
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"  Passed: {passed}/{total}")
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    print("="*60)
    
    sys.exit(0 if passed == total else 1)
