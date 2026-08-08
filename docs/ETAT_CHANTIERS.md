# État des Chantiers - PlasmaLLM / Desktop Agent

## 📊 Vue d'ensemble

Ce document présente l'état actuel du développement, les fonctionnalités incomplètes, et les pistes d'amélioration pour transformer PlasmaLLM en un système AGI autonome capable de gérer les communications multi-protocoles.

---

## 🔴 Chantiers Incomplets / Fonctions à Risque

### 1. **ASR (Speech-to-Text) - Endpoint Cloudflare**
**Statut**: ⚠️ Partiellement opérationnel  
**Fichier**: `package/contents/scripts/asr_helper.py`

**Problèmes identifiés**:
- ✅ Code implémenté pour `https://api.guig.dev/transcribe` (natif) et `/v1/audio/transcriptions` (OpenAI-compatible)
- ❌ Erreurs 403 (Forbidden) lors des tests API → DNS propagation ou authentification requise
- ❌ Aucun fallback automatique si l'API cloud échoue (bien que le mode local Whisper soit présent)
- ⚠️ Gestion des erreurs réseau basique (retry simple sans backoff exponentiel)

**À faire**:
- [ ] Tester à nouveau quand DNS sera propagé
- [ ] Ajouter un health check automatique au démarrage du daemon
- [ ] Implémenter un fallback cloud→local transparent
- [ ] Ajouter journalisation des échecs dans un fichier log dédié

---

### 2. **TTS (Text-to-Speech) - Endpoint Cloudflare**
**Statut**: ⚠️ Partiellement opérationnel  
**Fichier**: `package/contents/scripts/tts_helper.py`

**Problèmes identifiés**:
- ✅ Code implémenté pour `https://api.guig.dev/v1/audio/speech` (OpenAI-compatible)
- ❌ Erreurs 403 lors des tests → même problème que ASR
- ❌ Mode local Piper fonctionnel mais voix limitées (fr/en seulement par défaut)
- ⚠️ Pas de cache des synthèses (régénère toujours le même texte)
- ⚠️ Pas de streaming audio (attend la fin du WAV pour jouer)

**À faire**:
- [ ] Tester à nouveau quand DNS sera propagé
- [ ] Ajouter endpoint TTS natif Cloudflare (si différent de OpenAI-compatible)
- [ ] Implémenter un cache disque des synthèses (hash du texte → fichier WAV)
- [ ] Support du streaming pour lecture pendant la synthèse
- [ ] Catalogue de voix dynamique (récupéré via API)

---

### 3. **SMS via KDE Connect**
**Statut**: ✅ Fonctionnel (D-Bus direct)  
**Fichiers**: `package/contents/ui/tools/GetSMS.js`, `SendSMS.js`, `package/contents/scripts/sms/kdeconnect_sms.py`

**Problèmes résolus**:
- ✅ Scripts shell externes remplacés par module Python D-Bus direct
- ✅ Plus de dépendance à `~/plasmallm-tools/` (inexistant)
- ✅ Utilisation native de l'API D-Bus KDE Connect
- ✅ Support des conversations (thread_id) et nouveaux SMS

**Reste à faire**:
- [ ] Tester avec un téléphone Android appairé
- [ ] Ajouter outil de test de connexion KDE Connect
- [ ] Documenter l'appairage dans README

---

### 4. **Gestion Email (SMTP/IMAP)**
**Statut**: ❌ Inexistant

**Problèmes identifiés**:
- ❌ Aucun outil pour envoyer/recevoir des emails
- ❌ Pas d'intégration avec KMail, Thunderbird, ou APIs Gmail/Outlook
- ⚠️ Le tool `HttpRequest.js` pourrait être utilisé mais nécessite une config complexe

**À faire**:
- [ ] Créer un module Python `email_agent.py` avec:
  - IMAP pour la réception (ou API Gmail)
  - SMTP pour l'envoi (ou API Gmail)
  - OAuth2 pour l'authentification sécurisée
- [ ] Intégration avec le portefeuille KDE (KWallet) pour stocker les credentials
- [ ] Outils QML: `ReadEmail`, `SendEmail`, `ListConversations`
- [ ] Support des pièces jointes

---

### 5. **SSH/SFTP**
**Statut**: ❌ Inexistant

**Problèmes identifiés**:
- ❌ Aucun outil pour se connecter à des serveurs distants
- ⚠️ `KioFile.js` supporte théoriquement `sftp://` mais non testé
- ❌ Pas de gestion des clés SSH ou authentication

**À faire**:
- [ ] Créer un module Python `ssh_agent.py` utilisant `paramiko`
- [ ] Outils QML: `SSHConnect`, `SSHCommand`, `SFTPUpload`, `SFTPDownload`
- [ ] Intégration avec `~/.ssh/config` et les clés existantes
- [ ] Support des sessions persistantes

---

### 6. **FTP/FTPS**
**Statut**: ❌ Inexistant

**À faire**:
- [ ] Utiliser `KioFile.js` (déjà supporte `ftp://`)
- [ ] Ou créer un module Python avec `ftplib`
- [ ] Stockage sécurisé des credentials dans KWallet

---

### 7. **WebDAV**
**Statut**: ⚠️ Théoriquement supporté via KIO

**À faire**:
- [ ] Tester `kioclient5` avec URLs WebDAV
- [ ] Documenter la configuration

---

### 8. **Mémoire à Long Terme (RAG)**
**Statut**: ⚠️ Basique  
**Fichiers**: `memory.js`, `MemoryRead.js`, `MemoryWrite.js`, etc.

**Problèmes identifiés**:
- ✅ Système de mémoire persistante présent
- ❌ Pas d'embeddings vectoriels (recherche sémantique limitée)
- ❌ Pas de consolidation automatique des souvenirs
- ⚠️ La recherche est textuelle simple (substring match)

**À faire**:
- [ ] Intégrer un modèle d'embeddings local (nomic-embed-text via Ollama)
- [ ] Base de données vectorielle (ChromaDB ou FAISS)
- [ ] Consolidation automatique périodique (sleep mode)
- [ ] Oubli sélectif (mémoire à capacité limitée)

---

### 9. **Orchestration Multi-Outils**
**Statut**: ⚠️ Basique

**Problèmes identifiés**:
- ✅ Les outils sont indépendants et modulaires
- ❌ Pas de coordination entre outils (ex: lire email → répondre par SMS)
- ❌ Pas de planification de tâches complexes (goal decomposition)
- ⚠️ Le LLM doit tout orchestrer lui-même → lent et coûteux

**À faire**:
- [ ] Créer un module `orchestrator.js` qui:
  - Décompose les goals en sous-tâches
  - Exécute les outils en parallèle quand possible
  - Gère les dépendances entre tâches
- [ ] Ajouter un système de "workflows" pré-définis
- [ ] Implementer un mode "autonomie" avec supervision humaine

---

### 10. **Sécurité & Autorisations**
**Statut**: ⚠️ Partiel

**Problèmes identifiés**:
- ✅ Système d'approbation manuel pour les outils sensibles
- ✅ Sandbox pour les opérations fichiers
- ❌ Pas de niveaux de confiance (trust levels)
- ❌ Pas de journalisation des actions critiques
- ❌ Pas de limite de taux (rate limiting) pour les appels API

**À faire**:
- [ ] Implémenter un système de trust levels:
  - Niveau 1: Outils sans risque (lecture fichier, clipboard)
  - Niveau 2: Outils modérés (écriture fichier, HTTP GET)
  - Niveau 3: Outils sensibles (SSH, email, SMS)
  - Niveau 4: Outils critiques (sudo, suppression)
- [ ] Journalisation audit dans `~/.local/share/plasmallm/audit.log`
- [ ] Rate limiting configurable par outil
- [ ] Système de "safe mode" pour les nouvelles installations

---

## 🟡 Améliorations UX/UI Identifiées

### 1. **Accessibilité**
- ❌ Pas de support screen reader (Orca)
- ❌ Contraste des couleurs non vérifié WCAG
- ⚠️ Navigation clavier limitée

**À faire**:
- [ ] Ajouter des labels ARIA aux éléments QML
- [ ] Vérifier les contrastes de couleurs
- [ ] Support complet de la navigation clavier
- [ ] Raccourcis clavier personnalisables

### 2. **Feedback Utilisateur**
- ⚠️ Pas d'indications de progression pour les tâches longues
- ❌ Pas d'estimation du temps restant
- ⚠️ Messages d'erreur trop techniques

**À faire**:
- [ ] Barres de progression pour les opérations >2s
- [ ] Messages d'erreur humanisés avec suggestions
- [ ] Notifications discrètes pour les tâches en arrière-plan

### 3. **Personnalisation**
- ✅ Thèmes de couleurs personnalisables
- ✅ Polices personnalisables
- ❌ Pas de layouts prédéfinis
- ❌ Pas de profils utilisateur (multi-personnes)

**À faire**:
- [ ] Profils utilisateur avec préférences isolées
- [ ] Layouts prédéfinis (compact, large, minimal)
- [ ] Export/import des configurations

---

## 📋 Plan d'Intégration des Protocoles de Communication

### Architecture Proposée

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
│  - IMAP/SMTP  │   │  - D-Bus        │   │  - Keys mgmt    │
│  - OAuth2     │   │  - Fallback API │   │  - Sessions     │
└───────────────┘   └─────────────────┘   └─────────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  FTP Module   │   │  WebDAV Module  │   │  Matrix/ XMPP   │
│  - ftplib     │   │  - KIO          │   │  - maubot       │
│  - KIO        │   │  - davlib       │   │  - D-Bus        │
└───────────────┘   └─────────────────┘   └─────────────────┘
```

### Intégration Gmail

**Option A: SDK Officiel Google** (Recommandé)
```python
# google_email_agent.py
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import keyring  # KDE Wallet integration

class GmailAgent:
    def __init__(self):
        self.creds = self._load_credentials()
        self.service = build('gmail', 'v1', credentials=self.creds)
    
    def _load_credentials(self):
        # Try KDE Wallet first
        creds_json = keyring.get_password("plasmallm", "gmail_oauth")
        if creds_json:
            return Credentials.from_authorized_user_info(json.loads(creds_json))
        
        # Fallback to OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', 
            ['https://www.googleapis.com/auth/gmail.modify']
        )
        creds = flow.run_local_server(port=0)
        
        # Save to KDE Wallet
        keyring.set_password("plasmallm", "gmail_oauth", creds.to_json())
        return creds
    
    def list_messages(self, query="", max_results=10):
        results = self.service.users().messages().list(
            userId='me', q=query, maxResults=max_results
        ).execute()
        return results.get('messages', [])
    
    def read_message(self, msg_id):
        msg = self.service.users().messages().get(
            userId='me', id=msg_id, format='full'
        ).execute()
        return self._parse_message(msg)
    
    def send_message(self, to, subject, body, attachments=None):
        message = self._create_message(to, subject, body, attachments)
        sent = self.service.users().messages().send(
            userId='me', body=message
        ).execute()
        return sent['id']
```

**Option B: IMAP/SMTP Standard**
```python
# standard_email_agent.py
import imaplib
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import keyring

class IMAPEmailAgent:
    def __init__(self, server, port, username):
        self.server = server
        self.username = username
        self.password = keyring.get_password("plasmallm", f"imap_{username}")
        
    def connect_imap(self):
        mail = imaplib.IMAP4_SSL(self.server)
        mail.login(self.username, self.password)
        return mail
    
    def connect_smtp(self):
        smtp = smtplib.SMTP_SSL(self.server, 465)
        smtp.login(self.username, self.password)
        return smtp
```

### Projet KDE Existants à Greffer

1. **KDE Connect** (déjà partiellement intégré)
   - SMS: `org.kde.kdeconnect.daemon` → `/modules/sms`
   - Notifications: `org.kde.kdeconnect.daemon` → `/modules/notification`
   - Clipboard: `org.kde.kdeconnect.daemon` → `/modules/clipboard`
   
   ```bash
   # Tester D-Bus KDE Connect
   qdbus org.kde.kdeconnect.daemon /modules/sms org.kde.kdeconnect.module.sms.receivedMessages
   ```

2. **KMail/Kontact**
   - D-Bus: `org.kde.kmail`
   - Akonadi pour l'accès aux emails
   - Complexe mais puissant

3. **Telepathy/KAccounts**
   - Framework unifié pour communications
   - Supporte Gmail, Facebook, etc.
   - Projet en maintenance mais fonctionnel

4. **Plasma Browser Integration**
   - Pourrait être étendu pour Gmail
   - D-Bus: `org.kde.plasma.browser_integration`

### Recommandation Stratégique

**Phase 1 (Immédiat)**:
1. ✅ Finaliser ASR/TTS Cloudflare (attendre DNS)
2. 🔧 Créer scripts SMS manquants ou utiliser D-Bus KDE Connect directement
3. 📧 Implémenter module Gmail avec OAuth2 + KWallet

**Phase 2 (Court terme)**:
4. 🔐 Module SSH avec paramiko
5. 📁 Support SFTP/FTP via KIO (tester et documenter)
6. 🔒 Système de trust levels pour autorisations

**Phase 3 (Moyen terme)**:
7. 🧠 Mémoire vectorielle (RAG avec embeddings)
8. 🎼 Orchestrateur multi-outils
9. 📊 Audit logging et rate limiting

**Phase 4 (Long terme - AGI)**:
10. 🤖 Workflows autonomes avec supervision
11. 🌐 Support Matrix/XMPP pour messagerie décentralisée
12. 🔄 Apprentissage continu (reflex learning amélioré)

---

## 📚 Ressources Documentation

### Wayland (Dernière version)
- **Protocole**: [wayland-protocols](https://gitlab.freedesktop.org/wayland/wayland-protocols)
- **Remote Desktop**: `ext-session-lock-v1`, `wlr-screencopy-unstable-v1`
- **Input Methods**: `input-method-unstable-v2`
- **Outils**: `wl-copy`, `wl-paste`, `wtype` (wlroots)

### Cloudflare AI Gateway
- **Documentation**: https://developers.cloudflare.com/workers-ai/
- **Endpoints testés**:
  - `POST /transcribe` (ASR natif)
  - `POST /v1/audio/transcriptions` (ASR OpenAI-compatible)
  - `POST /v1/audio/speech` (TTS OpenAI-compatible)
- **Modèles**: `@cf/openai/whisper`, `@cf/deepgram/aura-2`

### KDE D-Bus APIs
- **KDE Connect**: https://community.kde.org/KDEConnect
- **KWallet**: `org.kde.kwalletd5`
- **KIO**: `org.kde.KIO`

### Bibliothèques Python Recommandées
```
google-api-python-client  # Gmail
google-auth-oauthlib      # OAuth2 Gmail
paramiko                  # SSH/SFTP
keyring                   # KDE Wallet integration
chromadb                  # Vector database (RAG)
maubot                    # Matrix bot framework
```

---

## ✅ Checklist Finale

### ASR/TTS Cloudflare
- [ ] DNS propagé → tester endpoints
- [ ] Health check automatique
- [ ] Fallback cloud→local
- [ ] Logging dédié

### Communications
- [ ] Scripts SMS (KDE Connect D-Bus)
- [ ] Module Gmail (OAuth2 + KWallet)
- [ ] Module SSH (paramiko)
- [ ] Test SFTP/FTP via KIO

### Sécurité
- [ ] Trust levels
- [ ] Audit logging
- [ ] Rate limiting
- [ ] Safe mode

### AGI Readiness
- [ ] Mémoire vectorielle
- [ ] Orchestrateur
- [ ] Workflows autonomes
- [ ] Supervision humaine

---

*Dernière mise à jour: $(date)*
*Prochaine revue: après propagation DNS Cloudflare*
