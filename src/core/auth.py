from datetime import datetime, timedelta
import jwt
from cryptography.fernet import Fernet
import os
from typing import Optional, Dict
import hashlib
import base64
from .database import Database

class Auth:
    _instance = None
    _key = None
    _fernet = None
    
    def __init__(self):
        if not Auth._key:
            Auth._key = os.getenv('SECRET_KEY') or base64.b64encode(os.urandom(32)).decode()
            Auth._fernet = Fernet(base64.b64encode(hashlib.sha256(Auth._key.encode()).digest()))
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Auth()
        return cls._instance
    
    def encrypt_token(self, token: str) -> str:
        return self._fernet.encrypt(token.encode()).decode()
    
    def decrypt_token(self, encrypted_token: str) -> str:
        return self._fernet.decrypt(encrypted_token.encode()).decode()
    
    async def create_session(self, user_id: int, server: str) -> Dict:
        session_data = {
            'user_id': user_id,
            'server': server,
            'exp': datetime.utcnow() + timedelta(hours=12),
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(session_data, self._key, algorithm='HS256')
        encrypted_token = self.encrypt_token(token)
        
        # Store in database
        await Database.execute(
            """
            INSERT INTO sessions (user_id, token, expires_at, server)
            VALUES ($1, $2, $3, $4)
            """,
            user_id, encrypted_token, session_data['exp'], server
        )
        
        return {
            'session_token': encrypted_token,
            'expires_at': session_data['exp'].timestamp()
        }
    
    async def validate_session(self, encrypted_token: str) -> Optional[Dict]:
        try:
            token = self.decrypt_token(encrypted_token)
            session_data = jwt.decode(token, self._key, algorithms=['HS256'])
            
            # Check if session exists and is valid in database
            session = await Database.fetchrow(
                """
                SELECT * FROM sessions 
                WHERE token = $1 AND expires_at > NOW()
                """,
                encrypted_token
            )
            
            if not session:
                return None
                
            return session_data
            
        except (jwt.InvalidTokenError, Exception):
            return None
    
    async def revoke_session(self, encrypted_token: str):
        await Database.execute(
            "DELETE FROM sessions WHERE token = $1",
            encrypted_token
        )
    
    async def cleanup_expired_sessions(self):
        await Database.execute(
            "DELETE FROM sessions WHERE expires_at < NOW()"
        ) 