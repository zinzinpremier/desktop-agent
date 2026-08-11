# TTS Cloudflare - Configuration et Utilisation

## Vue d'ensemble

Le module TTS (Text-to-Speech) de PlasmaLLM utilise **Cloudflare Workers AI** avec le modèle `aura-2` de Deepgram pour la synthèse vocale haute qualité.

## Architecture

```
Texte → Cloudflare Workers AI (aura-2) → Audio WAV → Lecture système
```

## Configuration Requise

### Variables d'environnement

```bash
# Mode TTS
PLASMALLM_TTS_MODE="cloud"  # ou "local" pour Piper

# Configuration Cloudflare
PLASMALLM_TTS_CLOUDFLARE_ACCOUNT_ID="votre_account_id"
PLASMALLM_TTS_CLOUDFLARE_API_TOKEN="votre_api_token"

# Voix (parmi 40+ disponibles)
PLASMALLM_TTS_VOICE="apollo"  # voix masculine française recommandée

# Langue
PLASMALLM_TTS_LANG="fr"  # français par défaut

# Modèle
PLASMALLM_TTS_MODEL="aura-2"

# Vitesse (0.5 - 2.0)
PLASMALLM_TTS_SPEED="1.1"  # légèrement plus rapide par défaut

# Streaming (pour lecture progressive)
PLASMALLM_TTS_STREAMING="true"
```

## Voix Disponibles par Langue

### 🇫🇷 Français (Recommandé: `apollo`)
| Voix | Genre | Style |
|------|-------|-------|
| `apollo` | Homme | Clair, professionnel |
| `athena` | Femme | Doux, naturel |
| `celeste` | Femme | Chaleureux |
| `danu` | Femme | Expressif |

### 🇺🇸 Anglais US (Recommandé: `athena`)
| Voix | Genre | Style |
|------|-------|-------|
| `athena` | Femme | Professionnel |
| `echo` | Homme | Profond |
| `emma` | Femme | Amical |

### Autres Langues
- 🇪🇸 Espagnol: `artemis`, `shango`
- 🇩🇪 Allemand: `hebe`, `jupiter`
- 🇮🇹 Italien: `medusa`, `percy`
- 🇧🇷 Portugais: `iris`, `orion`
- 🇯🇵 Japonais: `maia`, `talon`

## Endpoint API

### Cloudflare Workers AI

```
POST https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/deepgram/aura-2
Headers:
  Authorization: Bearer {api_token}
  Content-Type: application/json

Body:
{
  "text": "Bonjour, ceci est un test.",
  "voice": "apollo",
  "lang": "fr",
  "speed": 1.1
}
```

### Réponse

L'API retourne un flux audio binaire (WAV/MP3) directement lisible.

## Test Rapide

```bash
python3 package/contents/scripts/tts_helper.py "Bonjour, ceci est un test de synthèse vocale."
```

## Comparaison des Options

| Option | Avantages | Inconvénients |
|--------|-----------|---------------|
| **Cloudflare aura-2** | - Qualité exceptionnelle<br>- 40+ voix<br>- Multi-langue<br>- Pas d'installation | - Nécessite compte Cloudflare<br>- Latence réseau |
| **Piper Local** | - Hors ligne<br>- Vie privée<br>- Rapide | - Installation complexe<br>- Moins de voix<br>- Qualité variable |

## Performance

- **Latence**: 500ms - 2s selon longueur texte
- **Qualité**: MOS > 4.0 (quasi-humain)
- **Formats**: WAV, MP3 (selon configuration)

---

**Dernière mise à jour**: 2025
**Version**: 2.0 (Cloudflare Workers AI)
