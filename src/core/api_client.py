from typing import Optional, Dict, List
import logging
from tradelocker import TradeLocker
import pandas as pd

logger = logging.getLogger(__name__)

class TradingAPIClient:
    def __init__(self, api_key: str, api_secret: str, use_demo: bool = True):
        """Initialize the TradeLocker API client.
        
        Args:
            api_key: The API key from TradeLocker
            api_secret: The API secret from TradeLocker
            use_demo: Whether to use the demo environment (default: True)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.use_demo = use_demo
        self.client = None
        self._connect()
    
    def _connect(self):
        """Connect to the TradeLocker API."""
        try:
            self.client = TradeLocker(
                api_key=self.api_key,
                api_secret=self.api_secret,
                demo=self.use_demo
            )
            logger.info("Connected to TradeLocker API successfully")
        except Exception as e:
            logger.error(f"Failed to connect to TradeLocker API: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """Test the API connection."""
        try:
            # Get account info to test connection
            self.client.get_account()
            return True
        except Exception as e:
            logger.error(f"API connection test failed: {str(e)}")
            return False
    
    def get_account_info(self) -> Dict:
        """Get account information."""
        try:
            return self.client.get_account()
        except Exception as e:
            logger.error(f"Failed to get account info: {str(e)}")
            return {}
    
    def get_positions(self) -> List[Dict]:
        """Get current positions."""
        try:
            return self.client.get_positions()
        except Exception as e:
            logger.error(f"Failed to get positions: {str(e)}")
            return []
    
    def place_order(self, symbol: str, side: str, quantity: float, order_type: str = "MARKET",
                   price: Optional[float] = None, stop_price: Optional[float] = None) -> Dict:
        """Place a trading order.
        
        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            side: Order side ("BUY" or "SELL")
            quantity: Order quantity
            order_type: Order type ("MARKET" or "LIMIT")
            price: Limit price (required for LIMIT orders)
            stop_price: Stop price (for stop orders)
        """
        try:
            params = {
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "type": order_type
            }
            
            if price is not None:
                params["price"] = price
            if stop_price is not None:
                params["stopPrice"] = stop_price
            
            return self.client.create_order(**params)
        except Exception as e:
            logger.error(f"Failed to place order: {str(e)}")
            return {}
    
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order."""
        try:
            self.client.cancel_order(order_id=order_id, symbol=symbol)
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order: {str(e)}")
            return False
    
    def get_order_status(self, order_id: str, symbol: str) -> Dict:
        """Get the status of an order."""
        try:
            return self.client.get_order(order_id=order_id, symbol=symbol)
        except Exception as e:
            logger.error(f"Failed to get order status: {str(e)}")
            return {}
    
    def get_market_data(self, symbol: str, interval: str = "1m", limit: int = 100) -> pd.DataFrame:
        """Get market data (klines/candlesticks)."""
        try:
            data = self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Failed to get market data: {str(e)}")
            return pd.DataFrame() 