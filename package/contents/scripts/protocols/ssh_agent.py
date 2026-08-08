#!/usr/bin/env python3
"""
ssh_agent.py - SSH/SFTP client with key management and session persistence.

Usage:
    python ssh_agent.py connect <host> [user]              # Test connection
    python ssh_agent.py exec <host> <command> [user]       # Execute command
    python ssh_agent.py upload <host> <local> <remote> [user]  # Upload file
    python ssh_agent.py download <host> <remote> <local> [user]  # Download file
    python ssh_agent.py list <host> <path> [user]          # List remote directory
"""

import sys
import os

try:
    import paramiko
except ImportError:
    print("Error: paramiko not installed.", file=sys.stderr)
    print("Install with: pip3 install --user paramiko", file=sys.stderr)
    sys.exit(1)

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    print("Warning: keyring not available. Passwords will not be saved securely.", file=sys.stderr)

KEYRING_SERVICE = "plasmallm"

class SSHAgent:
    def __init__(self):
        self.client = None
        self.sftp = None
    
    def connect(self, host, username=None, password=None, key_file=None, port=22):
        """Establish SSH connection."""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Try key-based authentication first
            if key_file and os.path.exists(key_file):
                self.client.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    key_filename=key_file,
                    timeout=10,
                    allow_agent=True,
                    look_for_keys=True
                )
            elif password:
                self.client.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    password=password,
                    timeout=10
                )
            else:
                # Try from keyring
                if KEYRING_AVAILABLE:
                    stored_password = keyring.get_password(KEYRING_SERVICE, f"ssh_{username}@{host}")
                    if stored_password:
                        self.client.connect(
                            hostname=host,
                            port=port,
                            username=username,
                            password=stored_password,
                            timeout=10
                        )
                    else:
                        # Try SSH agent
                        self.client.connect(
                            hostname=host,
                            port=port,
                            username=username,
                            timeout=10,
                            allow_agent=True,
                            look_for_keys=True
                        )
                else:
                    # Try SSH agent
                    self.client.connect(
                        hostname=host,
                        port=port,
                        username=username,
                        timeout=10,
                        allow_agent=True,
                        look_for_keys=True
                    )
            
            self.sftp = self.client.open_sftp()
            return True
        except Exception as e:
            print(f"Error: Connection failed: {e}", file=sys.stderr)
            return False
    
    def execute_command(self, command):
        """Execute a command on the remote server."""
        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            return {
                'exit_code': exit_status,
                'stdout': output,
                'stderr': error,
                'success': exit_status == 0
            }
        except Exception as e:
            return {'error': str(e), 'success': False}
    
    def upload_file(self, local_path, remote_path):
        """Upload a file to the remote server."""
        try:
            self.sftp.put(local_path, remote_path)
            return {'success': True, 'remote_path': remote_path}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def download_file(self, remote_path, local_path):
        """Download a file from the remote server."""
        try:
            self.sftp.get(remote_path, local_path)
            return {'success': True, 'local_path': local_path}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def list_directory(self, path='.'):
        """List contents of a remote directory."""
        try:
            entries = []
            for entry in self.sftp.listdir_attr(path):
                entries.append({
                    'filename': entry.filename,
                    'size': entry.st_size,
                    'mode': entry.st_mode,
                    'is_dir': entry.st_mode & 0o40000 != 0
                })
            return {'success': True, 'entries': entries}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def close(self):
        """Close the SSH connection."""
        try:
            if self.sftp:
                self.sftp.close()
            if self.client:
                self.client.close()
        except:
            pass


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    agent = SSHAgent()
    
    if command == "connect":
        if len(sys.argv) < 3:
            print("Usage: ssh_agent.py connect <host> [user]", file=sys.stderr)
            sys.exit(1)
        
        host = sys.argv[2]
        user = sys.argv[3] if len(sys.argv) > 3 else None
        
        success = agent.connect(host, username=user)
        if success:
            print(f"Connected to {host} successfully!")
            agent.close()
        else:
            sys.exit(1)
    
    elif command == "exec":
        if len(sys.argv) < 4:
            print("Usage: ssh_agent.py exec <host> <command> [user]", file=sys.stderr)
            sys.exit(1)
        
        host = sys.argv[2]
        cmd = sys.argv[3]
        user = sys.argv[4] if len(sys.argv) > 4 else None
        
        if agent.connect(host, username=user):
            result = agent.execute_command(cmd)
            import json
            print(json.dumps(result, indent=2))
            agent.close()
        else:
            sys.exit(1)
    
    elif command == "upload":
        if len(sys.argv) < 5:
            print("Usage: ssh_agent.py upload <host> <local> <remote> [user]", file=sys.stderr)
            sys.exit(1)
        
        host = sys.argv[2]
        local = sys.argv[3]
        remote = sys.argv[4]
        user = sys.argv[5] if len(sys.argv) > 5 else None
        
        if agent.connect(host, username=user):
            result = agent.upload_file(local, remote)
            import json
            print(json.dumps(result, indent=2))
            agent.close()
        else:
            sys.exit(1)
    
    elif command == "download":
        if len(sys.argv) < 5:
            print("Usage: ssh_agent.py download <host> <remote> <local> [user]", file=sys.stderr)
            sys.exit(1)
        
        host = sys.argv[2]
        remote = sys.argv[3]
        local = sys.argv[4]
        user = sys.argv[5] if len(sys.argv) > 5 else None
        
        if agent.connect(host, username=user):
            result = agent.download_file(remote, local)
            import json
            print(json.dumps(result, indent=2))
            agent.close()
        else:
            sys.exit(1)
    
    elif command == "list":
        if len(sys.argv) < 4:
            print("Usage: ssh_agent.py list <host> <path> [user]", file=sys.stderr)
            sys.exit(1)
        
        host = sys.argv[2]
        path = sys.argv[3]
        user = sys.argv[4] if len(sys.argv) > 4 else None
        
        if agent.connect(host, username=user):
            result = agent.list_directory(path)
            import json
            print(json.dumps(result, indent=2))
            agent.close()
        else:
            sys.exit(1)
    
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print(__doc__, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
