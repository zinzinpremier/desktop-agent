#!/usr/bin/env python3
"""
gmail_agent.py - Gmail client with OAuth2 authentication and KDE Wallet integration.

Usage:
    python gmail_agent.py list [query] [max_results]  # List emails
    python gmail_agent.py read <msg_id>               # Read email
    python gmail_agent.py send <to> <subject> <body>  # Send email
    python gmail_agent.py auth                        # Re-authenticate
"""

import sys
import os
import json
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("Error: Google API libraries not installed.", file=sys.stderr)
    print("Install with: pip3 install --user google-api-python-client google-auth-httplib2 google-auth-oauthlib", file=sys.stderr)
    sys.exit(1)

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    print("Warning: keyring not available. Credentials will not be saved securely.", file=sys.stderr)

# Configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
TOKEN_FILE = os.path.expanduser('~/.local/share/plasmallm/gmail_token.json')
CREDENTIALS_FILE = os.path.expanduser('~/.local/share/plasmallm/gmail_credentials.json')
KEYRING_SERVICE = "plasmallm"
KEYRING_KEY = "gmail_oauth"

class GmailAgent:
    def __init__(self):
        self.creds = None
        self.service = None
        self._authenticate()
    
    def _load_credentials_from_keyring(self):
        """Load OAuth credentials from KDE Wallet."""
        if not KEYRING_AVAILABLE:
            return None
        
        try:
            creds_json = keyring.get_password(KEYRING_SERVICE, KEYRING_KEY)
            if creds_json:
                creds_data = json.loads(creds_json)
                return Credentials.from_authorized_user_info(creds_data, SCOPES)
        except Exception as e:
            print(f"Warning: Could not load credentials from keyring: {e}", file=sys.stderr)
        return None
    
    def _save_credentials_to_keyring(self, creds):
        """Save OAuth credentials to KDE Wallet."""
        if not KEYRING_AVAILABLE:
            return False
        
        try:
            creds_json = creds.to_json()
            keyring.set_password(KEYRING_SERVICE, KEYRING_KEY, creds_json)
            return True
        except Exception as e:
            print(f"Warning: Could not save credentials to keyring: {e}", file=sys.stderr)
            return False
    
    def _authenticate(self):
        """Authenticate with Gmail using OAuth2."""
        # Try KDE Wallet first
        self.creds = self._load_credentials_from_keyring()
        
        if self.creds and self.creds.valid:
            self._build_service()
            return
        
        # Check for expired token file
        if os.path.exists(TOKEN_FILE):
            try:
                self.creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                    self._save_credentials_to_keyring(self.creds)
                    self._build_service()
                    return
            except Exception as e:
                print(f"Warning: Token file invalid: {e}", file=sys.stderr)
        
        # Interactive OAuth flow
        if os.path.exists(CREDENTIALS_FILE):
            try:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                self.creds = flow.run_local_server(port=0, open_browser=False)
                self._save_credentials_to_keyring(self.creds)
                
                # Save token file as backup
                os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
                with open(TOKEN_FILE, 'w') as f:
                    f.write(self.creds.to_json())
                
                self._build_service()
                return
            except Exception as e:
                print(f"Error: OAuth flow failed: {e}", file=sys.stderr)
        
        print("Error: No valid credentials found.", file=sys.stderr)
        print("To authenticate:", file=sys.stderr)
        print(f"1. Create OAuth credentials at https://console.cloud.google.com/apis/credentials", file=sys.stderr)
        print(f"2. Save as: {CREDENTIALS_FILE}", file=sys.stderr)
        print(f"3. Run: python gmail_agent.py auth", file=sys.stderr)
        sys.exit(1)
    
    def _build_service(self):
        """Build Gmail API service."""
        try:
            self.service = build('gmail', 'v1', credentials=self.creds)
        except Exception as e:
            print(f"Error: Could not build Gmail service: {e}", file=sys.stderr)
            sys.exit(1)
    
    def list_messages(self, query="", max_results=10):
        """List Gmail messages matching query."""
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            output = []
            
            for msg in messages[:max_results]:
                msg_detail = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'To', 'Subject', 'Date']
                ).execute()
                
                headers = msg_detail.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
                
                output.append({
                    'id': msg['id'],
                    'subject': subject,
                    'from': sender,
                    'date': date,
                    'snippet': msg_detail.get('snippet', '')
                })
            
            return output
        except HttpError as e:
            print(f"Error: Gmail API error: {e}", file=sys.stderr)
            return []
    
    def read_message(self, msg_id):
        """Read full message content."""
        try:
            msg = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()
            
            payload = msg.get('payload', {})
            headers = payload.get('headers', [])
            
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            recipient = next((h['value'] for h in headers if h['name'] == 'To'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Get body content
            body = ""
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                        body_data = part['body']['data']
                        body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                        break
            elif 'body' in payload and 'data' in payload['body']:
                body_data = payload['body']['data']
                body = base64.urlsafe_b64decode(body_data).decode('utf-8')
            
            return {
                'id': msg_id,
                'subject': subject,
                'from': sender,
                'to': recipient,
                'date': date,
                'body': body,
                'threadId': msg.get('threadId')
            }
        except HttpError as e:
            print(f"Error: Gmail API error: {e}", file=sys.stderr)
            return None
    
    def send_message(self, to, subject, body, attachments=None):
        """Send an email message."""
        try:
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            message.attach(MIMEText(body, 'plain'))
            
            # Handle attachments
            if attachments:
                for filepath in attachments.split(','):
                    filepath = filepath.strip()
                    if os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename={os.path.basename(filepath)}'
                            )
                            message.attach(part)
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            sent = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return {'id': sent['id'], 'threadId': sent['threadId']}
        except HttpError as e:
            print(f"Error: Gmail API error: {e}", file=sys.stderr)
            return None
    
    def mark_as_read(self, msg_id):
        """Mark a message as read."""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except HttpError as e:
            print(f"Error: Gmail API error: {e}", file=sys.stderr)
            return False
    
    def delete_message(self, msg_id):
        """Delete a message."""
        try:
            self.service.users().messages().delete(userId='me', id=msg_id).execute()
            return True
        except HttpError as e:
            print(f"Error: Gmail API error: {e}", file=sys.stderr)
            return False


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    agent = GmailAgent()
    
    if command == "list":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        max_results = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        
        messages = agent.list_messages(query, max_results)
        print(json.dumps(messages, indent=2))
    
    elif command == "read":
        if len(sys.argv) < 3:
            print("Usage: gmail_agent.py read <msg_id>", file=sys.stderr)
            sys.exit(1)
        
        msg = agent.read_message(sys.argv[2])
        if msg:
            print(json.dumps(msg, indent=2))
    
    elif command == "send":
        if len(sys.argv) < 5:
            print("Usage: gmail_agent.py send <to> <subject> <body> [attachments]", file=sys.stderr)
            sys.exit(1)
        
        to = sys.argv[2]
        subject = sys.argv[3]
        body = sys.argv[4]
        attachments = sys.argv[5] if len(sys.argv) > 5 else None
        
        result = agent.send_message(to, subject, body, attachments)
        if result:
            print(json.dumps(result, indent=2))
    
    elif command == "auth":
        print("Re-authenticating...")
        agent._authenticate()
        print("Authentication successful!")
    
    elif command == "mark_read":
        if len(sys.argv) < 3:
            print("Usage: gmail_agent.py mark_read <msg_id>", file=sys.stderr)
            sys.exit(1)
        
        success = agent.mark_as_read(sys.argv[2])
        print(json.dumps({"success": success}))
    
    elif command == "delete":
        if len(sys.argv) < 3:
            print("Usage: gmail_agent.py delete <msg_id>", file=sys.stderr)
            sys.exit(1)
        
        success = agent.delete_message(sys.argv[2])
        print(json.dumps({"success": success}))
    
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print(__doc__, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
