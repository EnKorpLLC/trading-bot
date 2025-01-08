from typing import Dict, Optional, List
import pandas as pd
import logging
from ..core.market_analyzer import MarketCondition
from ..core.tradelocker_client import TradeLockerClient

logger = logging.getLogger(__name__)

class BaseStrategy:
    def __init__(self, name: str):
        self.name = name
        self.parameters = {}
        self.client: Optional[TradeLockerClient] = None
        self.timeframe = "1h"  # Default timeframe
        self.lookback_period = 100  # Default lookback period
        
    def set_client(self, client: TradeLockerClient):
        """Set the TradeLocker client instance."""
        self.client = client
        
    def _get_market_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get market data for analysis."""
        try:
            if not self.client:
                raise ValueError("TradeLocker client not set")
                
            data = self.client.get_historical_data(
                symbol=symbol,
                timeframe=self.timeframe,
                limit=self.lookback_period
            )
            
            if data.empty:
                logger.warning(f"No data received for {symbol}")
                return None
                
            return data
            
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {str(e)}")
            return None
            
    async def execute_trade_signal(self, signal: Dict, risk_manager) -> Dict:
        """Execute a trade signal with position sizing and risk management."""
        try:
            if not self.client:
                raise ValueError("TradeLocker client not set")
                
            if not self._validate_trade_signal(signal):
                return {"error": "Invalid trade signal"}
                
            # Calculate position size based on risk management rules
            position_size = risk_manager.calculate_position_size(
                signal['entry_price'],
                signal['stop_loss']
            )
            
            # Create order with proper risk management
            order = {
                "symbol": signal['symbol'],
                "type": "MARKET",
                "side": signal['side'],
                "size": position_size,
                "stop_loss": signal['stop_loss'],
                "take_profit": signal['take_profit'],
                "metadata": {
                    "strategy": self.name,
                    "reason": signal.get('reason', 'Strategy signal'),
                    "risk_ratio": signal.get('risk_reward_ratio', 2.0)
                }
            }
            
            # Place the order through TradeLocker
            result = await self.client.place_order(order)
            
            if "error" in result:
                logger.error(f"Order placement failed: {result['error']}")
                return result
                
            logger.info(f"Successfully placed order: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing trade signal: {str(e)}")
            return {"error": str(e)}
            
    def _validate_trade_signal(self, signal: Dict) -> bool:
        """Validate trade signal parameters."""
        required_fields = ['symbol', 'side', 'entry_price', 'stop_loss', 'take_profit']
        
        # Check for required fields
        if not all(field in signal for field in required_fields):
            logger.error(f"Missing required fields in trade signal")
            return False
            
        # Validate signal values
        try:
            if signal['side'] not in ['buy', 'sell']:
                logger.error(f"Invalid side in trade signal: {signal['side']}")
                return False
                
            # Convert prices to float and validate
            entry_price = float(signal['entry_price'])
            stop_loss = float(signal['stop_loss'])
            take_profit = float(signal['take_profit'])
            
            # Validate price relationships
            if signal['side'] == 'buy':
                if not (stop_loss < entry_price < take_profit):
                    logger.error("Invalid price levels for buy signal")
                    return False
            else:  # sell
                if not (take_profit < entry_price < stop_loss):
                    logger.error("Invalid price levels for sell signal")
                    return False
                    
            return True
            
        except ValueError as e:
            logger.error(f"Invalid numeric values in trade signal: {str(e)}")
            return False 