import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MT5Handler:
    def __init__(self):
        self.connected = False
        self.initialize()

    def initialize(self):
        """Initialize connection to MT5 terminal"""
        try:
            if not mt5.initialize():
                logger.error(f"MT5 initialization failed. Error: {mt5.last_error()}")
                return False
            
            logger.info("MT5 connection established successfully")
            self.connected = True
            return True
        except Exception as e:
            logger.error(f"Error initializing MT5: {str(e)}")
            return False

    def get_available_symbols(self):
        """Get list of available trading symbols"""
        if not self.connected:
            if not self.initialize():
                return []
        
        try:
            symbols = mt5.symbols_get()
            return [symbol.name for symbol in symbols]
        except Exception as e:
            logger.error(f"Error getting symbols: {str(e)}")
            return []

    def get_symbol_info(self, symbol):
        """Get detailed information about a symbol"""
        if not self.connected:
            if not self.initialize():
                return None
        
        try:
            info = mt5.symbol_info(symbol)
            if info is None:
                logger.error(f"Failed to get symbol info for {symbol}")
                return None
            
            return {
                'symbol': info.name,
                'bid': info.bid,
                'ask': info.ask,
                'spread': info.spread,
                'digits': info.digits,
                'volume_min': info.volume_min,
                'volume_max': info.volume_max
            }
        except Exception as e:
            logger.error(f"Error getting symbol info: {str(e)}")
            return None

    def get_historical_data(self, symbol, timeframe=mt5.TIMEFRAME_M1, start_pos=0, count=1000):
        """Get historical price data for a symbol"""
        if not self.connected:
            if not self.initialize():
                return None
        
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, start_pos, count)
            if rates is None:
                logger.error(f"Failed to get historical data for {symbol}")
                return None
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            return df
        except Exception as e:
            logger.error(f"Error getting historical data: {str(e)}")
            return None

    def place_market_order(self, symbol, order_type, volume, stop_loss=None, take_profit=None):
        """Place a market order"""
        if not self.connected:
            if not self.initialize():
                return False

        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                logger.error(f"Failed to get symbol info for {symbol}")
                return False

            point = symbol_info.point
            price = symbol_info.ask if order_type == mt5.ORDER_TYPE_BUY else symbol_info.bid

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": float(volume),
                "type": order_type,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": "python script order",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            if stop_loss:
                request["sl"] = stop_loss
            if take_profit:
                request["tp"] = take_profit

            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed: {result.comment}")
                return False
            
            logger.info(f"Order placed successfully: {result.comment}")
            return True
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return False

    def close_position(self, position_id):
        """Close an open position"""
        if not self.connected:
            if not self.initialize():
                return False

        try:
            position = mt5.positions_get(ticket=position_id)
            if position is None:
                logger.error(f"Position {position_id} not found")
                return False

            position = position[0]
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": mt5.ORDER_TYPE_SELL if position.type == 0 else mt5.ORDER_TYPE_BUY,
                "position": position_id,
                "price": mt5.symbol_info_tick(position.symbol).bid if position.type == 0 else mt5.symbol_info_tick(position.symbol).ask,
                "deviation": 20,
                "magic": 234000,
                "comment": "python script close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Failed to close position: {result.comment}")
                return False
            
            logger.info(f"Position closed successfully")
            return True
        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
            return False

    def __del__(self):
        """Cleanup when object is destroyed"""
        if self.connected:
            mt5.shutdown() 