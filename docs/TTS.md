# TTS (Text-to-Speech) - Cloudflare Aura-2

## Configuration par défaut

Le système TTS utilise **Cloudflare Workers AI (Aura-2)** par défaut avec les paramètres optimisés suivants :

- **Mode** : Cloud (API Cloudflare)
- **Modèle** : `aura-2`
- **Vitesse** : `1.1x` (10% plus rapide pour une réponse plus réactive)
- **Langue par défaut** : Français (`fr`)
- **Voix française** : `apollo` (voix masculine, claire et naturelle)

## Voix disponibles par langue

Le système sélectionne **automatiquement** la meilleure voix selon la langue configurée :

| Langue | Code | Voix | Genre | Description |
|--------|------|------|-------|-------------|
| 🇫🇷 Français | `fr-FR` | `apollo` | Homme | Claire, naturelle (défaut) |
| 🇫🇷 Français | `fr-FR` | `demeter` | Femme | Alternative disponible |
| 🇺🇸 Anglais US | `en-US` | `athena` | Femme | Défaut anglais |
| 🇺🇸 Anglais US | `en-US` | `zeus` | Homme | Alternative |
| 🇬🇧 Anglais UK | `en-GB` | `hera` | Femme | Accent britannique |
| 🇬🇧 Anglais UK | `en-GB` | `perseus` | Homme | Alternative UK |
| 🇪🇸 Espagnol | `es-ES` | `artemis` | Femme | Naturel |
| 🇪🇸 Espagnol | `es-ES` | `ares` | Homme | Alternative |
| 🇩🇪 Allemand | `de-DE` | `hebe` | Femme | Claire |
| 🇩🇪 Allemand | `de-DE` | `poseidon` | Homme | Alternative |
| 🇮🇹 Italien | `it-IT` | `medusa` | Femme | Expressive |
| 🇮🇹 Italien | `it-IT` | `hades` | Homme | Alternative |
| 🇧🇷 Portugais BR | `pt-BR` | `iris` | Femme | Naturel BR |
| 🇧🇷 Portugais BR | `pt-BR` | `eros` | Homme | Alternative |
| 🇯🇵 Japonais | `ja-JP` | `maia` | Femme | Claire |
| 🇯🇵 Japonais | `ja-JP` | `atlas` | Homme | Alternative |

## Auto-sélection intelligente

Si aucune voix n'est explicitement configurée, le système choisit automatiquement :

```javascript
// Exemple dans SpeakText.js
if (!cloudVoice || cloudVoice === "athena") {
    if (lang.startsWith("fr")) {
        cloudVoice = "apollo";       // Français -> apollo
    } else if (lang.startsWith("es")) {
        cloudVoice = "artemis";      // Espagnol -> artemis
    } else if (lang.startsWith("de")) {
        cloudVoice = "hebe";         // Allemand -> hebe
    }
    // ... etc
}
```

## Variables d'environnement

```bash
PLASMALLM_TTS_MODE="cloud"           # cloud ou local
PLASMALLM_TTS_MODEL="aura-2"         # Modèle Cloudflare
PLASMALLM_TTS_VOICE="apollo"         # Voix (auto-sélectionnée si non définie)
PLASMALLM_TTS_LANG="fr"              # Code langue (fr, en, es, de, it, pt, ja)
PLASMALLM_TTS_SPEED="1.1"            # Vitesse (1.0 = normal, 1.1 = 10% plus fast)
PLASMALLM_TTS_STREAMING="true"       # Activer le streaming pour latence réduite
PLASMALLM_TTS_API_URL="https://api.guig.dev/v1/audio/speech"
```

## Optimisations de performance

### 1. Vitesse augmentée (1.1x)
- Réduit le temps de synthèse de ~10%
- Reste naturel et clair
- Configurable via `PLASMALLM_TTS_SPEED`

### 2. Streaming audio
- Lecture progressive pendant la génération
- Réduit la latence perçue
- Activé par défaut (`PLASMALLM_TTS_STREAMING="true"`)

### 3. Sélection automatique de voix
- Plus besoin de configurer manuellement chaque langue
- Utilise toujours la voix optimale pour la langue demandée

## Utilisation avec l'API Cloudflare

```python
import urllib.request
import json

payload = json.dumps({
    "model": "aura-2",
    "input": "Bonjour, ceci est un test.",
    "voice": "apollo",
    "speed": 1.1,
}).encode("utf-8")

req = urllib.request.Request(
    "https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/workers-ai/models/@cf/meta/aura-2-aurorasky",
    data=payload,
    method="POST",
)
req.add_header("Authorization", "Bearer {API_TOKEN}")
req.add_header("Content-Type", "application/json")

with urllib.request.urlopen(req) as response:
    audio_data = response.read()
    # Sauvegarder ou jouer audio_data (format WAV)
```

## Dépannage

### Problème : Voix incorrecte pour la langue
**Solution** : Vérifier que `PLASMALLM_TTS_LANG` est correctement défini (ex: `fr`, `en`, `es`)

### Problème : Latence élevée
**Solutions** :
1. Augmenter `PLASMALLM_TTS_SPEED` (ex: `1.2` ou `1.3`)
2. Vérifier que `PLASMALLM_TTS_STREAMING="true"`
3. Réduire la longueur du texte (max 1000 caractères par défaut)

### Problème : Audio non joué
**Solution** : Le script teste plusieurs lecteurs dans l'ordre :
1. `paplay` (PipeWire/PulseAudio)
2. `ffplay` (FFmpeg - fallback universel)
3. `pw-play` (PipeWire natif)
4. `aplay` (ALSA - dernier recours)

Installer `ffmpeg` pour garantir `ffplay` : `sudo apt install ffmpeg`

## Fichiers clés

- `/workspace/package/contents/scripts/tts_helper.py` - Script Python principal
- `/workspace/package/contents/ui/tools/SpeakText.js` - Intégration PlasmaLLM
- `/workspace/docs/TTS.md` - Cette documentation

## Références

- [Cloudflare Workers AI - Aura](https://developers.cloudflare.com/workers-ai/models/aura/)
- [API Documentation](https://developers.cloudflare.com/api/operations/text-to-speech-create-aura)
