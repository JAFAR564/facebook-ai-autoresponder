# config/security.py
from cryptography.fernet import Fernet
import os
import base64
from dotenv import load_dotenv

class CredentialManager:
    def __init__(self):
        load_dotenv()
        self._initialize_key()
        
    def _initialize_key(self):
        """Initialize or load the encryption key."""
        key_file = os.path.join(os.path.dirname(__file__), '.key')
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                self.key = f.read()
        else:
            # Generate a new key and save it
            self.key = Fernet.generate_key()
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(self.key)
            print("New encryption key generated.")
            
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data):
        """Encrypt sensitive data."""
        if not data:
            return None
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data):
        """Decrypt sensitive data."""
        if not encrypted_data:
            return None
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def get_credentials(self):
        """Get decrypted credentials from environment variables."""
        username = os.getenv("FB_USERNAME")
        password = os.getenv("FB_PASSWORD")
        secret_key = os.getenv("FB_2FA_SECRET")
        
        # Check if credentials are encrypted
        if username and username.startswith('gAAAAA'):
            username = self.decrypt(username)
            
        if password and password.startswith('gAAAAA'):
            password = self.decrypt(password)
            
        if secret_key and secret_key.startswith('gAAAAA'):
            secret_key = self.decrypt(secret_key)
            
        return {
            'username': username,
            'password': password,
            'secret_key': secret_key
        }
    
    def encrypt_credentials(self):
        """Encrypt credentials in .env file."""
        try:
            # Load the current .env file
            with open('.env', 'r') as f:
                lines = f.readlines()
            
            encrypted = False
            new_lines = []
            for line in lines:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    if key in ['FB_USERNAME', 'FB_PASSWORD', 'FB_2FA_SECRET'] and value and not value.startswith('gAAAAA'):
                        encrypted_value = self.encrypt(value)
                        new_lines.append(f"{key}={encrypted_value}\n")
                        encrypted = True
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            
            if encrypted:
                # Write the updated .env file
                with open('.env', 'w') as f:
                    f.writelines(new_lines)
                print("Credentials encrypted successfully.")
            else:
                print("No credentials needed encryption.")
                
        except Exception as e:
            print(f"Error encrypting credentials: {e}")
