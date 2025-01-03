from typing import Optional, Dict, List
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

@dataclass
class Coupon:
    code: str
    discount_percent: int
    max_uses: int
    uses_count: int
    expiry_date: datetime.datetime
    created_at: datetime.datetime

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

    def get_coupon(self, code: str) -> Optional[Coupon]:
        """Get details of a specific coupon."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT code, discount_percent, max_uses, uses_count, 
                           expiry_date, created_at 
                    FROM coupons 
                    WHERE code = ?
                """, (code,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                    
                return Coupon(
                    code=row[0],
                    discount_percent=row[1],
                    max_uses=row[2],
                    uses_count=row[3],
                    expiry_date=datetime.datetime.fromisoformat(row[4]),
                    created_at=datetime.datetime.fromisoformat(row[5])
                )
                
        except Exception as e:
            logger.error(f"Error getting coupon: {str(e)}")
            return None

    def list_coupons(self, include_expired: bool = False) -> List[Coupon]:
        """List all coupons."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT code, discount_percent, max_uses, uses_count, 
                           expiry_date, created_at 
                    FROM coupons
                """
                if not include_expired:
                    query += " WHERE expiry_date > ?"
                    cursor = conn.execute(query, 
                                        (datetime.datetime.utcnow().isoformat(),))
                else:
                    cursor = conn.execute(query)
                
                return [
                    Coupon(
                        code=row[0],
                        discount_percent=row[1],
                        max_uses=row[2],
                        uses_count=row[3],
                        expiry_date=datetime.datetime.fromisoformat(row[4]),
                        created_at=datetime.datetime.fromisoformat(row[5])
                    )
                    for row in cursor.fetchall()
                ]
                
        except Exception as e:
            logger.error(f"Error listing coupons: {str(e)}")
            return []

    def delete_coupon(self, code: str) -> bool:
        """Delete a coupon."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM coupons WHERE code = ?", (code,))
                return True
                
        except Exception as e:
            logger.error(f"Error deleting coupon: {str(e)}")
            return False

    def update_coupon(self, code: str, 
                     discount_percent: Optional[int] = None,
                     max_uses: Optional[int] = None,
                     expiry_date: Optional[datetime.datetime] = None) -> bool:
        """Update coupon details."""
        try:
            updates = []
            params = []
            
            if discount_percent is not None:
                updates.append("discount_percent = ?")
                params.append(discount_percent)
                
            if max_uses is not None:
                updates.append("max_uses = ?")
                params.append(max_uses)
                
            if expiry_date is not None:
                updates.append("expiry_date = ?")
                params.append(expiry_date.isoformat())
                
            if not updates:
                return False
                
            query = f"""
                UPDATE coupons 
                SET {', '.join(updates)}
                WHERE code = ?
            """
            params.append(code)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(query, params)
                return True
                
        except Exception as e:
            logger.error(f"Error updating coupon: {str(e)}")
            return False 