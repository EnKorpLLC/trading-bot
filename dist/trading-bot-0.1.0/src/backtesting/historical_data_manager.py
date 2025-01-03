from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import yfinance as yf  # For demo data
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class HistoricalDataManager:
    def __init__(self):
        self.data: Dict[str, Dict[str, pd.DataFrame]] = {}
        self.timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
        self.cache_dir = Path("cache/historical_data")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def load_data(self, 
                 symbol: str, 
                 timeframe: str, 
                 start_date: datetime, 
                 end_date: datetime) -> bool:
        """Load historical price data for a specific symbol and timeframe."""
        try:
            # Check cache first
            cached_data = self._load_from_cache(symbol, timeframe, start_date, end_date)
            if cached_data is not None:
                self._store_data(symbol, timeframe, cached_data)
                return True
                
            # Fetch new data if not in cache
            data = self._fetch_data(symbol, timeframe, start_date, end_date)
            if data is None:
                return False
                
            # Store and cache data
            self._store_data(symbol, timeframe, data)
            self._save_to_cache(symbol, timeframe, data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading data for {symbol} {timeframe}: {str(e)}")
            return False
            
    def get_data(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Get stored data for a symbol and timeframe."""
        return self.data.get(symbol, {}).get(timeframe)
        
    def get_timestamps(self) -> List[datetime]:
        """Get list of all timestamps in the data."""
        all_timestamps = set()
        for symbol_data in self.data.values():
            for df in symbol_data.values():
                all_timestamps.update(df.index)
        return sorted(list(all_timestamps))
        
    def get_data_at(self, timestamp: datetime) -> Dict[str, Dict]:
        """Get market data for all symbols at a specific timestamp."""
        result = {}
        for symbol, timeframes in self.data.items():
            for timeframe, df in timeframes.items():
                if timestamp in df.index:
                    if symbol not in result:
                        result[symbol] = {}
                    result[symbol].update({
                        'open': df.loc[timestamp, 'open'],
                        'high': df.loc[timestamp, 'high'],
                        'low': df.loc[timestamp, 'low'],
                        'close': df.loc[timestamp, 'close'],
                        'volume': df.loc[timestamp, 'volume'],
                        'timeframe': timeframe
                    })
        return result
        
    def validate_data(self) -> bool:
        """Verify data integrity and completeness."""
        if not self.data:
            return False
            
        try:
            for symbol, timeframes in self.data.items():
                for timeframe, df in timeframes.items():
                    # Check for required columns
                    required_columns = ['open', 'high', 'low', 'close', 'volume']
                    if not all(col in df.columns for col in required_columns):
                        logger.error(f"Missing required columns in {symbol} {timeframe}")
                        return False
                        
                    # Check for missing values
                    if df[required_columns].isna().any().any():
                        logger.error(f"Found missing values in {symbol} {timeframe}")
                        return False
                        
                    # Check data consistency
                    if not self._check_data_consistency(df):
                        logger.error(f"Data consistency check failed for {symbol} {timeframe}")
                        return False
                        
            return True
            
        except Exception as e:
            logger.error(f"Data validation error: {str(e)}")
            return False
            
    def resample_data(self, timeframe: str):
        """Convert data to different timeframes."""
        for symbol in self.data:
            base_data = self._get_base_timeframe_data(symbol)
            if base_data is None:
                continue
                
            resampled = self._resample_ohlcv(base_data, timeframe)
            if resampled is not None:
                self._store_data(symbol, timeframe, resampled)
                
    def _store_data(self, symbol: str, timeframe: str, data: pd.DataFrame):
        """Store data in memory."""
        if symbol not in self.data:
            self.data[symbol] = {}
        self.data[symbol][timeframe] = data
        
    def _fetch_data(self, symbol: str, timeframe: str, 
                   start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """Fetch historical data from data provider."""
        try:
            # Using yfinance for demo purposes
            # Replace with your actual data source
            ticker = yf.Ticker(symbol)
            interval = self._convert_timeframe(timeframe)
            data = ticker.history(start=start_date, end=end_date, interval=interval)
            
            # Standardize column names
            data.columns = [col.lower() for col in data.columns]
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}")
            return None
            
    def _convert_timeframe(self, timeframe: str) -> str:
        """Convert internal timeframe format to provider format."""
        # Convert timeframe format for yfinance
        # Customize based on your data provider
        conversion = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '1h': '60m',
            '4h': '4h',
            '1d': '1d'
        }
        return conversion.get(timeframe, '1d')
        
    def _check_data_consistency(self, df: pd.DataFrame) -> bool:
        """Check data for basic consistency rules."""
        # Check if high is highest
        if not all(df['high'] >= df[['open', 'close']].max(axis=1)):
            return False
            
        # Check if low is lowest
        if not all(df['low'] <= df[['open', 'close']].min(axis=1)):
            return False
            
        # Check if volume is non-negative
        if not all(df['volume'] >= 0):
            return False
            
        return True
        
    def _get_base_timeframe_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get the smallest timeframe data available for a symbol."""
        if symbol not in self.data:
            return None
            
        timeframes_available = list(self.data[symbol].keys())
        if not timeframes_available:
            return None
            
        smallest_timeframe = min(timeframes_available, 
                               key=lambda x: self._timeframe_to_minutes(x))
        return self.data[symbol][smallest_timeframe]
        
    def _timeframe_to_minutes(self, timeframe: str) -> int:
        """Convert timeframe string to minutes."""
        multiplier = int(timeframe[:-1])
        unit = timeframe[-1]
        
        if unit == 'm':
            return multiplier
        elif unit == 'h':
            return multiplier * 60
        elif unit == 'd':
            return multiplier * 1440
        return 0
        
    def _resample_ohlcv(self, df: pd.DataFrame, timeframe: str) -> Optional[pd.DataFrame]:
        """Resample OHLCV data to a new timeframe."""
        try:
            # Convert timeframe to pandas offset string
            offset = self._timeframe_to_offset(timeframe)
            
            # Resample OHLCV data
            resampled = df.resample(offset).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            })
            
            return resampled
            
        except Exception as e:
            logger.error(f"Error resampling data: {str(e)}")
            return None
            
    def _timeframe_to_offset(self, timeframe: str) -> str:
        """Convert timeframe to pandas offset string."""
        # Convert timeframe format for pandas resampling
        conversion = {
            '1m': '1T',
            '5m': '5T',
            '15m': '15T',
            '1h': '1H',
            '4h': '4H',
            '1d': '1D'
        }
        return conversion.get(timeframe, '1D')
        
    def _load_from_cache(self, symbol: str, timeframe: str,
                        start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """Load data from cache if available."""
        cache_file = self.cache_dir / f"{symbol}_{timeframe}.csv"
        if not cache_file.exists():
            return None
            
        try:
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            mask = (df.index >= start_date) & (df.index <= end_date)
            return df[mask]
        except Exception as e:
            logger.error(f"Error loading from cache: {str(e)}")
            return None
            
    def _save_to_cache(self, symbol: str, timeframe: str, data: pd.DataFrame):
        """Save data to cache."""
        try:
            cache_file = self.cache_dir / f"{symbol}_{timeframe}.csv"
            data.to_csv(cache_file)
        except Exception as e:
            logger.error(f"Error saving to cache: {str(e)}") 