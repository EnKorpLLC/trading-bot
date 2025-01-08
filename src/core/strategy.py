from typing import Dict, Optional
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class Strategy:
    """Base class for trading strategies."""
    
    def __init__(self, name: str, default_parameters: Dict):
        """Initialize strategy with name and default parameters."""
        self.name = name
        self.parameters = default_parameters.copy()
        self.current_position = None
        
    def set_parameters(self, parameters: Dict):
        """Update strategy parameters."""
        self.parameters.update(parameters)
        if not self.validate_parameters():
            logger.error("Invalid parameters provided")
            return False
        return True
        
    def validate_parameters(self) -> bool:
        """Validate strategy parameters. Override in subclass."""
        return True
        
    def analyze(self, market_data: Dict, market_state: Dict) -> Optional[Dict]:
        """Analyze market data and generate trading signals. Override in subclass."""
        raise NotImplementedError("Subclass must implement analyze method")
        
    def _calculate_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate common technical indicators."""
        try:
            # Calculate moving averages
            sma_20 = data['close'].rolling(window=20).mean().iloc[-1]
            sma_50 = data['close'].rolling(window=50).mean().iloc[-1]
            
            # Calculate Bollinger Bands
            bb_period = self.parameters.get('bb_period', 20)
            bb_std = self.parameters.get('bb_std', 2.0)
            
            bb_sma = data['close'].rolling(window=bb_period).mean()
            bb_std = data['close'].rolling(window=bb_period).std()
            bb_upper = bb_sma + (bb_std * bb_std)
            bb_lower = bb_sma - (bb_std * bb_std)
            
            # Calculate RSI
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return {
                'sma_20': sma_20,
                'sma_50': sma_50,
                'bb_upper': bb_upper.iloc[-1],
                'bb_lower': bb_lower.iloc[-1],
                'rsi': rsi.iloc[-1]
            }
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            return {}
            
    def _generate_signal(self, signal_type: str, price: float,
                        indicators: Dict, market_state: Dict) -> Dict:
        """Generate a trading signal with common attributes."""
        return {
            'type': signal_type,
            'price': price,
            'timestamp': pd.Timestamp.now(),
            'indicators': indicators,
            'market_state': market_state
        }
        
    def calculate_position_size(self, account_balance: float,
                              risk_percentage: float,
                              entry_price: float,
                              stop_loss: float) -> float:
        """Calculate position size based on risk parameters."""
        try:
            risk_amount = account_balance * (risk_percentage / 100)
            price_risk = abs(entry_price - stop_loss)
            
            if price_risk <= 0:
                return 0
                
            position_size = risk_amount / price_risk
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return 0 