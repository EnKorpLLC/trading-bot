import MetaTrader5 as mt5
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MT5Connector:
    def __init__(self):
        self.connected = False
        self.available_symbols = []
    
    def connect(self, path: str = None) -> bool:
        """Connect to MetaTrader 5 terminal"""
        try:
            if not mt5.initialize(path=path):
                logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return False
            
            logger.info("MT5 connection established successfully")
            self.connected = True
            
            # Get available symbols
            self.available_symbols = [symbol.name for symbol in mt5.symbols_get()]
            logger.info(f"Available symbols: {len(self.available_symbols)}")
            
            return True
        except Exception as e:
            logger.error(f"Error connecting to MT5: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MetaTrader 5 terminal"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("MT5 connection closed")
    
    def get_symbols(self) -> List[str]:
        """Get list of available symbols"""
        return self.available_symbols
    
    def get_ohlcv(self, 
                  symbol: str, 
                  timeframe: str,
                  num_candles: int = 1000) -> Optional[pd.DataFrame]:
        """Get OHLCV data for a symbol"""
        if not self.connected:
            logger.error("MT5 not connected")
            return None
        
        # Convert timeframe string to MT5 timeframe
        tf_map = {
            '1m': mt5.TIMEFRAME_M1,
            '5m': mt5.TIMEFRAME_M5,
            '15m': mt5.TIMEFRAME_M15,
            '30m': mt5.TIMEFRAME_M30,
            '1h': mt5.TIMEFRAME_H1,
            '4h': mt5.TIMEFRAME_H4,
            '1d': mt5.TIMEFRAME_D1,
        }
        
        mt5_tf = tf_map.get(timeframe)
        if mt5_tf is None:
            logger.error(f"Invalid timeframe: {timeframe}")
            return None
        
        try:
            # Get historical data
            rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, num_candles)
            if rates is None:
                logger.error(f"Failed to get data for {symbol}: {mt5.last_error()}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Rename columns to match our format
            df = df.rename(columns={
                'time': 'timestamp',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'tick_volume': 'volume'
            })
            
            return df
        except Exception as e:
            logger.error(f"Error getting data for {symbol}: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[Dict[str, float]]:
        """Get current bid/ask price for a symbol"""
        if not self.connected:
            logger.error("MT5 not connected")
            return None
        
        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                logger.error(f"Failed to get price for {symbol}: {mt5.last_error()}")
                return None
            
            return {
                'bid': tick.bid,
                'ask': tick.ask,
                'spread': tick.ask - tick.bid
            }
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return None
    
    def get_account_info(self) -> Optional[Dict]:
        """Get account information"""
        if not self.connected:
            logger.error("MT5 not connected")
            return None
        
        try:
            account_info = mt5.account_info()
            if account_info is None:
                logger.error(f"Failed to get account info: {mt5.last_error()}")
                return None
            
            return {
                'balance': account_info.balance,
                'equity': account_info.equity,
                'margin': account_info.margin,
                'free_margin': account_info.margin_free,
                'leverage': account_info.leverage,
                'currency': account_info.currency
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None 