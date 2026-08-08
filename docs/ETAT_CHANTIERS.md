# État des Chantiers - PlasmaLLM / Desktop Agent

## 📊 Vue d'ensemble

Ce document présente l'état actuel du développement, les fonctionnalités **complètes** et incomplètes, et les pistes d'amélioration pour transformer PlasmaLLM en un système AGI autonome capable de gérer les communications multi-protocoles.

**Dernière mise à jour**: Août 2025
**Statut global**: 70% complet

---

## ✅ Chantiers Complétés

### 1. **ASR (Speech-to-Text) - Endpoint Cloudflare** ✅
**Statut**: ✅ **Opérationnel**  
**Fichier**: `package/contents/scripts/asr_helper.py`

**Implémentation**:
- ✅ Endpoint natif: `https://api.guig.dev/transcribe`
- ✅ Endpoint OpenAI-compatible: `https://api.guig.dev/v1/audio/transcriptions`
- ✅ Fallback local Whisper.cpp disponible
- ✅ Gestion des erreurs avec retry
- ✅ Support Wayland/X11 pour injection texte
- ✅ Variables d'environnement configurables:
  - `PLASMALLM_ASR_MODE` (cloud/local)
  - `PLASMALLM_ASR_LANG` (code langue)
  - `PLASMALLM_ASR_API_URL` (URL personnalisable)

**Test manuel**:
```bash
curl -X POST https://api.guig.dev/transcribe \
  -F 'audio=@recording.wav' \
  -F 'language=fr'
```

---

### 2. **TTS (Text-to-Speech) - Endpoint Cloudflare** ✅
**Statut**: ✅ **Opérationnel**  
**Fichier**: `package/contents/scripts/tts_helper.py`

**Implémentation**:
- ✅ Endpoint: `https://api.guig.dev/v1/audio/speech`
- ✅ Modèle: `aura-2` (Deepgram via Cloudflare)
- ✅ 40+ voix disponibles (athena, aries, arcas, etc.)
- ✅ Mode local Piper disponible
- ✅ Variables configurables:
  - `PLASMALLM_TTS_MODE` (cloud/local)
  - `PLASMALLM_TTS_VOICE` (nom de la voix)
  - `PLASMALLM_TTS_MODEL` (modèle)
  - `PLASMALLM_TTS_SPEED` (vitesse 0.5-2.0)

**Test**:
```bash
python3 package/contents/scripts/tts_helper.py "Bonjour ceci est un test"
```

---

### 3. **SMS via KDE Connect** ✅
**Statut**: ✅ **Opérationnel**  
**Fichiers**: 
- `package/contents/ui/tools/GetSMS.js`
- `package/contents/ui/tools/SendSMS.js`
- `package/contents/scripts/sms/kdeconnect_sms.py`

**Implémentation**:
- ✅ API D-Bus KDE Connect directe
- ✅ Plus de dépendance aux scripts shell externes
- ✅ Support des conversations (thread_id)
- ✅ Récupération SMS reçus/envoyés
- ✅ Envoi de nouveaux SMS

**Prérequis**: Téléphone Android appairé avec KDE Connect

---

### 4. **Gestion Email Gmail** ✅
**Statut**: ✅ **Implémenté**  
**Fichiers**:
- `package/contents/scripts/protocols/gmail_agent.py`
- `package/contents/ui/tools/email/ReadEmail.js`
- `package/contents/ui/tools/email/SendEmail.js`

**Implémentation**:
- ✅ SDK officiel Google Gmail API
- ✅ Authentification OAuth2 sécurisée
- ✅ Intégration KDE Wallet (KWallet) pour stockage credentials
- ✅ Fonctions: list, read, send, mark_read, delete
- ✅ Support des pièces jointes
- ✅ Recherche Gmail (query syntax)

**Configuration requise**:
```bash
pip3 install --user google-api-python-client google-auth-oauthlib keyring
```

**OAuth Setup**:
1. Créer credentials sur https://console.cloud.google.com/apis/credentials
2. Sauvegarder sous `~/.local/share/plasmallm/gmail_credentials.json`
3. Exécuter: `python gmail_agent.py auth`

---

### 5. **SSH/SFTP** ✅
**Statut**: ✅ **Implémenté**  
**Fichier**: `package/contents/scripts/protocols/ssh_agent.py`

**Implémentation**:
- ✅ Bibliothèque paramiko
- ✅ Authentification par clé SSH
- ✅ Support SSH agent system
- ✅ Intégration KWallet pour mots de passe
- ✅ Commandes: connect, exec, upload, download, list
- ✅ Sessions SFTP complètes

**Configuration requise**:
```bash
pip3 install --user paramiko keyring
```

---

## 🔴 Chantiers Incomplets / Fonctions à Risque

### 6. **FTP/FTPS** ⚠️
**Statut**: ⚠️ **Théoriquement supporté via KIO**

**À faire**:
- [ ] Tester `kioclient5` avec URLs `ftp://`
- [ ] Ou créer module Python avec `ftplib`
- [ ] Stockage sécurisé credentials dans KWallet

---

### 7. **WebDAV** ⚠️
**Statut**: ⚠️ **Théoriquement supporté via KIO**

**À faire**:
- [ ] Tester `kioclient` avec URLs WebDAV
- [ ] Documenter configuration

---

### 8. **Mémoire à Long Terme (RAG)** ⚠️
**Statut**: ⚠️ **Basique**  
**Fichiers**: `memory.js`, `MemoryRead.js`, `MemoryWrite.js`

**Problèmes identifiés**:
- ✅ Système de mémoire persistante présent
- ❌ Pas d'embeddings vectoriels (recherche sémantique limitée)
- ❌ Pas de consolidation automatique des souvenirs
- ⚠️ Recherche textuelle simple (substring match)

**À faire**:
- [ ] Intégrer modèle embeddings local (nomic-embed-text via Ollama)
- [ ] Base de données vectorielle (ChromaDB ou FAISS)
- [ ] Consolidation automatique périodique
- [ ] Oubli sélectif (mémoire à capacité limitée)

---

### 9. **Orchestration Multi-Outils** ⚠️
**Statut**: ⚠️ **Basique**

**Problèmes identifiés**:
- ✅ Outils indépendants et modulaires
- ❌ Pas de coordination entre outils (ex: lire email → répondre par SMS)
- ❌ Pas de planification de tâches complexes (goal decomposition)
- ⚠️ Le LLM doit tout orchestrer lui-même → lent et coûteux

**À faire**:
- [ ] Créer module `orchestrator.js`:
  - Décompose les goals en sous-tâches
  - Exécute outils en parallèle quand possible
  - Gère dépendances entre tâches
- [ ] Ajouter système de "workflows" pré-définis
- [ ] Implémenter mode "autonomie" avec supervision humaine

---

### 10. **Sécurité & Autorisations** ⚠️
**Statut**: ⚠️ **Partiel**

**Problèmes identifiés**:
- ✅ Approbation manuelle pour outils sensibles
- ✅ Sandbox pour opérations fichiers
- ❌ Pas de niveaux de confiance (trust levels)
- ❌ Pas de journalisation actions critiques
- ❌ Pas de rate limiting pour appels API

**À faire**:
- [ ] Implémenter trust levels:
  - Niveau 1: Lecture fichier, clipboard
  - Niveau 2: Écriture fichier, HTTP GET
  - Niveau 3: SSH, email, SMS
  - Niveau 4: sudo, suppression
- [ ] Journalisation audit dans `~/.local/share/plasmallm/audit.log`
- [ ] Rate limiting configurable par outil
- [ ] Système "safe mode" nouvelles installations

---

## 🟡 Améliorations UX/UI Identifiées

### 1. **Accessibilité**
- ❌ Pas de support screen reader (Orca)
- ❌ Contraste couleurs non vérifié WCAG
- ⚠️ Navigation clavier limitée

**À faire**:
- [ ] Labels ARIA éléments QML
- [ ] Vérifier contrastes couleurs
- [ ] Navigation clavier complète
- [ ] Raccourcis clavier personnalisables

### 2. **Feedback Utilisateur**
- ⚠️ Pas d'indications progression tâches longues
- ❌ Pas d'estimation temps restant
- ⚠️ Messages d'erreur trop techniques

**À faire**:
- [ ] Barres progression opérations >2s
- [ ] Messages d'erreur humanisés avec suggestions
- [ ] Notifications discrètes tâches arrière-plan

### 3. **Personnalisation**
- ✅ Thèmes couleurs personnalisables
- ✅ Polices personnalisables
- ❌ Pas de layouts prédéfinis
- ❌ Pas de profils utilisateur (multi-personnes)

**À faire**:
- [ ] Profils utilisateur avec préférences isolées
- [ ] Layouts prédéfinis (compact, large, minimal)
- [ ] Export/import configurations

---

## 📋 Architecture Multi-Protocoles

```
┌─────────────────────────────────────────────────────────────┐
│                    Communication Agent                       │
│  (module central orchestrant tous les protocoles)            │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  Email Module │   │   SMS Module    │   │  SSH/SFTP Module│
│  - Gmail API  │   │  - KDE Connect  │   │  - Paramiko     │
│  - OAuth2     │   │  - D-Bus        │   │  - Keys mgmt    │
│  - KWallet    │   │                 │   │  - Sessions     │
└───────────────┘   └─────────────────┘   └─────────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  FTP Module   │   │  WebDAV Module  │   │  ASR/TTS Module │
│  - ftplib     │   │  - KIO          │   │  - Cloudflare   │
│  - KIO        │   │  - davlib       │   │  - Whisper/Piper│
└───────────────┘   └─────────────────┘   └─────────────────┘
```

---

## 📚 Ressources Documentation

### Cloudflare AI Gateway
- **Documentation**: https://developers.cloudflare.com/workers-ai/
- **Endpoints**:
  - `GET  /health` - Santé service
  - `GET  /models` - Modèles disponibles
  - `POST /transcribe` - ASR natif
  - `POST /v1/audio/transcriptions` - ASR OpenAI-compatible
  - `POST /v1/audio/speech` - TTS OpenAI-compatible
  - `GET  /v1/models` - Modèles OpenAI-compatible

### KDE D-Bus APIs
- **KDE Connect**: https://community.kde.org/KDEConnect
- **KWallet**: `org.kde.kwalletd5`
- **KIO**: `org.kde.KIO`

### Bibliothèques Python Requises
```bash
# ASR/TTS (déjà installé)
pip3 install --user requests

# Gmail
pip3 install --user google-api-python-client google-auth-oauthlib keyring

# SSH
pip3 install --user paramiko keyring

# Optionnel: RAG
pip3 install --user chromadb sentence-transformers
```

---

## ✅ Checklist Finale

### Communications Multi-Protocoles
- [x] ASR Cloudflare + Local
- [x] TTS Cloudflare + Local
- [x] SMS KDE Connect
- [x] Email Gmail (OAuth2 + KWallet)
- [x] SSH/SFTP (paramiko + KWallet)
- [ ] FTP/FTPS
- [ ] WebDAV

### Sécurité
- [ ] Trust levels
- [ ] Audit logging
- [ ] Rate limiting
- [ ] Safe mode

### AGI Readiness
- [ ] Mémoire vectorielle (RAG)
- [ ] Orchestrateur multi-outils
- [ ] Workflows autonomes
- [ ] Supervision humaine

---

*Prochaine revue: Après tests complets Gmail et SSH*
