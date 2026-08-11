# ASR Cloudflare - Configuration et Utilisation

## Vue d'ensemble

Le module ASR (Automatic Speech Recognition) de PlasmaLLM utilise **Cloudflare Workers AI** avec le modèle `@cf/openai/whisper` pour la transcription audio en temps réel.

## Architecture

```
Microphone → PipeWire (pw-record) → WAV → Cloudflare Workers AI → Texte → Injection clavier
```

## Configuration Requise

### 1. Variables d'environnement

Pour utiliser Cloudflare Workers AI, définissez les variables suivantes dans votre systemd service ou environnement :

```bash
# Mode ASR
PLASMALLM_ASR_MODE="cloud"  # ou "local" pour Whisper.cpp

# Configuration Cloudflare Workers AI
PLASMALLM_ASR_CLOUDFLARE_ACCOUNT_ID="votre_account_id"
PLASMALLM_ASR_CLOUDFLARE_API_TOKEN="votre_api_token"

# Langue par défaut (code ISO 639-1)
PLASMALLM_ASR_LANG="fr"  # français par défaut

# Durée maximale d'enregistrement (secondes)
PLASMALLM_ASR_MAX_DURATION="60"
```

### 2. Endpoint personnalisé (optionnel)

Si vous préférez utiliser un endpoint compatible OpenAI au lieu de Cloudflare Workers AI :

```bash
PLASMALLM_ASR_API_URL="https://votre-endpoint.com/v1/audio/transcriptions"
```

## Obtention des Identifiants Cloudflare

1. Connectez-vous à [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Allez dans **Workers & Pages** → **AI** → **Models**
3. Notez votre **Account ID** (dans l'URL ou via API)
4. Créez un **API Token** avec les permissions :
   - `Account.AI:Read`
   - `Account.AI:Edit`

### Récupérer l'Account ID via API

```bash
curl -X GET "https://api.cloudflare.com/client/v4/accounts" \
  -H "Authorization: Bearer VOTRE_API_TOKEN"
```

## Installation du Service

```bash
# Installer le service systemd
./scripts/install_asr.sh

# Vérifier le statut
systemctl --user status plasmallm-asr.service

# Redémarrer avec les nouvelles variables
systemctl --user daemon-reload
systemctl --user restart plasmallm-asr.service
```

## Format Audio Supporté

Le système enregistre automatiquement au format requis par Cloudflare Whisper :
- **Format**: WAV
- **Sample Rate**: 16000 Hz
- **Channels**: 1 (mono)
- **Bit Depth**: 16-bit PCM

## Endpoints API

### Cloudflare Workers AI (Recommandé)

```
POST https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/openai/whisper
Headers:
  Authorization: Bearer {api_token}
  Content-Type: multipart/form-data

Body:
  audio: fichier WAV
  language: fr (optionnel)
```

### Réponse Attendue

```json
{
  "success": true,
  "errors": [],
  "messages": [],
  "result": {
    "text": "Bonjour, ceci est un test de transcription.",
    "language": "fr",
    "duration": 3.5
  }
}
```

## Dépannage

### Logs du Service

```bash
journalctl --user -u plasmallm-asr.service -f
```

### Erreurs Courantes

| Erreur | Solution |
|--------|----------|
| `No ASR endpoint configured` | Définir `PLASMALLM_ASR_CLOUDFLARE_ACCOUNT_ID` et `PLASMALLM_ASR_CLOUDFLARE_API_TOKEN` |
| `HTTP 401 Unauthorized` | Vérifier l'API Token |
| `HTTP 404 Not Found` | Vérifier l'Account ID |
| `pw-record not found` | Installer `pipewire` et `pipewire-audio-client-libraries` |
| `No microphone detected` | Vérifier que PipeWire voit le micro: `pw-cli list-objects \| grep Source` |

### Test Manuel

```bash
# Tester l'API Cloudflare directement
curl -X POST "https://api.cloudflare.com/client/v4/accounts/VOTRE_ACCOUNT_ID/ai/run/@cf/openai/whisper" \
  -H "Authorization: Bearer VOTRE_API_TOKEN" \
  -F "audio=@recording.wav" \
  -F "language=fr"
```

## Comparaison des Options

| Option | Avantages | Inconvénients |
|--------|-----------|---------------|
| **Cloudflare Workers AI** | - Qualité excellente<br>- Pas d'installation locale<br>- Mise à jour automatique | - Nécessite compte Cloudflare<br>- Latence réseau (~1-2s) |
| **Whisper.cpp Local** | - Hors ligne<br>- Vie privée totale<br>- Pas de latence réseau | - Installation complexe<br>- Utilise CPU/GPU<br>- Modèles à télécharger |

## Performance

- **Latence typique**: 1-3 secondes (incluant upload + traitement)
- **Précision**: ~95%+ pour le français clair
- **Taille max audio**: 25 MB (limitation Cloudflare)

## Sécurité

- L'audio est envoyé via HTTPS chiffré
- Aucun stockage permanent chez Cloudflare
- Le token API doit être protégé (mode 600)

## Exemple de Configuration Complète

Fichier: `~/.config/systemd/user/plasmallm-asr.service`

```ini
[Unit]
Description=PlasmaLLM ASR Daemon
After=pipewire.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/user/.local/share/plasmallm/bin/asr_helper.py
Environment="PLASMALLM_ASR_MODE=cloud"
Environment="PLASMALLM_ASR_CLOUDFLARE_ACCOUNT_ID=abc123..."
Environment="PLASMALLM_ASR_CLOUDFLARE_API_TOKEN=xyz789..."
Environment="PLASMALLM_ASR_LANG=fr"
Environment="PLASMALLM_ASR_MAX_DURATION=60"

[Install]
WantedBy=default.target
```

---

**Dernière mise à jour**: 2025
**Version**: 2.0 (Cloudflare Workers AI)
