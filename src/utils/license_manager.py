from typing import Optional, Dict
import hashlib
import jwt
import datetime
from dataclasses import dataclass
import sqlite3
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class License:
    license_key: str
    user_email: str
    expiry_date: datetime.datetime
    is_active: bool
    features: Dict[str, bool]

class LicenseManager:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path("data/licenses.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        
    def _init_db(self):
        """Initialize the license database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS licenses (
                    license_key TEXT PRIMARY KEY,
                    user_email TEXT NOT NULL,
                    expiry_date TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL,
                    features TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS coupons (
                    code TEXT PRIMARY KEY,
                    discount_percent INTEGER NOT NULL,
                    max_uses INTEGER NOT NULL,
                    uses_count INTEGER NOT NULL DEFAULT 0,
                    expiry_date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            
    def generate_license(self, user_email: str, 
                        duration_days: int = 365) -> str:
        """Generate a new license key."""
        # Create unique license key
        timestamp = datetime.datetime.utcnow().isoformat()
        key_base = f"{user_email}:{timestamp}"
        license_key = hashlib.sha256(key_base.encode()).hexdigest()[:32]
        
        # Set expiry date
        expiry_date = (datetime.datetime.utcnow() + 
                      datetime.timedelta(days=duration_days))
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO licenses 
                (license_key, user_email, expiry_date, is_active, 
                 features, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                license_key,
                user_email,
                expiry_date.isoformat(),
                True,
                '{"basic": true, "premium": false}',
                timestamp
            ))
            
        return license_key
        
    def validate_license(self, license_key: str) -> Optional[License]:
        """Validate a license key."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM licenses 
                    WHERE license_key = ? AND is_active = 1
                """, (license_key,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                    
                expiry_date = datetime.datetime.fromisoformat(row[2])
                if expiry_date < datetime.datetime.utcnow():
                    return None
                    
                return License(
                    license_key=row[0],
                    user_email=row[1],
                    expiry_date=expiry_date,
                    is_active=bool(row[3]),
                    features=eval(row[4])  # Safe as we control the data
                )
                
        except Exception as e:
            logger.error(f"Error validating license: {str(e)}")
            return None
            
    def add_coupon(self, code: str, discount_percent: int,
                   max_uses: int, duration_days: int = 30):
        """Add a new coupon code."""
        expiry_date = (datetime.datetime.utcnow() + 
                      datetime.timedelta(days=duration_days))
                      
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO coupons 
                (code, discount_percent, max_uses, expiry_date, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                code,
                discount_percent,
                max_uses,
                expiry_date.isoformat(),
                datetime.datetime.utcnow().isoformat()
            ))
            
    def validate_coupon(self, code: str) -> Optional[int]:
        """Validate a coupon code and return discount percentage."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT discount_percent, max_uses, uses_count, expiry_date 
                    FROM coupons WHERE code = ?
                """, (code,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                    
                discount, max_uses, uses, expiry = row
                expiry_date = datetime.datetime.fromisoformat(expiry)
                
                if (expiry_date < datetime.datetime.utcnow() or 
                    uses >= max_uses):
                    return None
                    
                # Increment usage count
                conn.execute("""
                    UPDATE coupons 
                    SET uses_count = uses_count + 1 
                    WHERE code = ?
                """, (code,))
                
                return discount
                
        except Exception as e:
            logger.error(f"Error validating coupon: {str(e)}")
            return None 