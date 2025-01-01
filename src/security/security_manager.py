from typing import Dict, Optional
import logging
from pathlib import Path
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import jwt
import ssl
import secrets

logger = logging.getLogger(__name__)

class SecurityManager:
    def __init__(self):
        self.key_store = {}
        self.key_file = Path("data/security/keys.enc")
        self.key_file.parent.mkdir(parents=True, exist_ok=True)
        self.fernet = self._initialize_encryption()
        self.session_tokens = {}
        
    def encrypt_credentials(self, credentials: Dict) -> Dict:
        """Encrypt sensitive credentials."""
        try:
            encrypted_creds = {}
            for key, value in credentials.items():
                if isinstance(value, str):
                    encrypted_value = self.fernet.encrypt(value.encode())
                    encrypted_creds[key] = encrypted_value.decode()
            return encrypted_creds
            
        except Exception as e:
            logger.error(f"Error encrypting credentials: {str(e)}")
            raise
            
    def decrypt_credentials(self, encrypted_creds: Dict) -> Dict:
        """Decrypt sensitive credentials."""
        try:
            decrypted_creds = {}
            for key, value in encrypted_creds.items():
                if isinstance(value, str):
                    decrypted_value = self.fernet.decrypt(value.encode())
                    decrypted_creds[key] = decrypted_value.decode()
            return decrypted_creds
            
        except Exception as e:
            logger.error(f"Error decrypting credentials: {str(e)}")
            raise
            
    def create_secure_session(self, user_id: str) -> str:
        """Create secure session token."""
        try:
            token = secrets.token_urlsafe(32)
            expiry = {'exp': datetime.utcnow() + timedelta(hours=24)}
            session_data = {'user_id': user_id, **expiry}
            
            encoded_token = jwt.encode(
                session_data,
                self.key_store['session_key'],
                algorithm='HS256'
            )
            
            self.session_tokens[user_id] = encoded_token
            return encoded_token
            
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            raise
            
    def validate_session(self, token: str) -> Optional[str]:
        """Validate session token."""
        try:
            decoded = jwt.decode(
                token,
                self.key_store['session_key'],
                algorithms=['HS256']
            )
            return decoded.get('user_id')
            
        except jwt.ExpiredSignatureError:
            logger.warning("Session token expired")
            return None
        except Exception as e:
            logger.error(f"Error validating session: {str(e)}")
            return None
            
    def secure_connection(self, endpoint: str) -> ssl.SSLContext:
        """Create secure SSL context for connections."""
        try:
            context = ssl.create_default_context()
            context.verify_mode = ssl.CERT_REQUIRED
            context.check_hostname = True
            
            # Load certificates if provided
            cert_path = self.key_store.get('cert_path')
            if cert_path:
                context.load_cert_chain(cert_path)
                
            return context
            
        except Exception as e:
            logger.error(f"Error creating SSL context: {str(e)}")
            raise
            
    def _initialize_encryption(self) -> Fernet:
        """Initialize encryption system."""
        try:
            if self.key_file.exists():
                with open(self.key_file, 'rb') as f:
                    key = f.read()
            else:
                # Generate new encryption key
                salt = secrets.token_bytes(16)
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(b"app_secret"))
                
                # Save key
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                    
            return Fernet(key)
            
        except Exception as e:
            logger.error(f"Error initializing encryption: {str(e)}")
            raise 