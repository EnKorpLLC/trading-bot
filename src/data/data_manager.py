from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from pathlib import Path
import sqlite3
from ..core.interfaces import IDataProvider
from ..utils.cache_manager import CacheManager

logger = logging.getLogger(__name__)

class DataManager(IDataProvider):
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.db_path = Path("data/market_data.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = self._init_database()
        self.subscriptions = {}
        
    def get_market_data(self, 
                       symbol: str, 
                       timeframe: str,
                       start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None) -> Dict:
        """Get market data from cache or database."""
        try:
            # Check cache first
            cache_key = f"{symbol}_{timeframe}"
            if cached_data := self.cache.get_market_data(cache_key):
                return cached_data
                
            # Query database
            query = """
                SELECT timestamp, open, high, low, close, volume
                FROM market_data
                WHERE symbol = ? AND timeframe = ?
                AND timestamp BETWEEN ? AND ?
            """
            
            start_time = start_time or datetime.now() - timedelta(days=30)
            end_time = end_time or datetime.now()
            
            df = pd.read_sql_query(
                query,
                self.connection,
                params=(symbol, timeframe, start_time, end_time),
                parse_dates=['timestamp']
            )
            
            # Cache the data
            market_data = df.to_dict('records')
            self.cache.cache_market_data(cache_key, market_data)
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")
            return {}
            
    def subscribe_to_feed(self, symbol: str, callback: callable):
        """Subscribe to real-time market data feed."""
        try:
            if symbol not in self.subscriptions:
                self.subscriptions[symbol] = set()
            self.subscriptions[symbol].add(callback)
            
        except Exception as e:
            logger.error(f"Error subscribing to feed: {str(e)}")
            
    def save_market_data(self, data: Dict):
        """Save market data to database."""
        try:
            query = """
                INSERT INTO market_data (
                    symbol, timeframe, timestamp, open, high, low, close, volume
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            with self.connection:
                self.connection.execute(query, (
                    data['symbol'],
                    data['timeframe'],
                    data['timestamp'],
                    data['open'],
                    data['high'],
                    data['low'],
                    data['close'],
                    data['volume']
                ))
                
        except Exception as e:
            logger.error(f"Error saving market data: {str(e)}")
            
    def _init_database(self) -> sqlite3.Connection:
        """Initialize SQLite database."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Create tables if they don't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    timeframe TEXT,
                    timestamp DATETIME,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    UNIQUE(symbol, timeframe, timestamp)
                )
            """)
            
            # Create indices
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_market_data_symbol 
                ON market_data(symbol)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_market_data_timestamp 
                ON market_data(timestamp)
            """)
            
            return conn
            
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise 