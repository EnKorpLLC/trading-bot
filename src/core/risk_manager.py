from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self, max_risk_per_trade: float = 0.02):
        self.max_risk_per_trade = max_risk_per_trade
        self.open_positions: Dict = {}
        self.total_exposure: float = 0.0
        
    def calculate_position_size(self, 
                              account_balance: float,
                              entry_price: float,
                              stop_loss: float) -> float:
        """Calculate safe position size based on risk parameters."""
        risk_amount = account_balance * self.max_risk_per_trade
        stop_distance = abs(entry_price - stop_loss)
        
        if stop_distance == 0:
            logger.error("Invalid stop loss distance")
            return 0
            
        position_size = risk_amount / stop_distance
        return position_size
        
    def validate_trade(self, 
                      trade_details: Dict) -> bool:
        """Validate if trade meets risk management criteria."""
        # Check if we're within risk limits
        if self.total_exposure >= 0.06:  # Max 6% total exposure
            logger.warning("Maximum exposure limit reached")
            return False
            
        # Validate stop loss
        if 'stop_loss' not in trade_details:
            logger.error("No stop loss specified")
            return False
            
        return True
        
    def update_exposure(self, 
                       trade_id: str, 
                       position_size: float, 
                       risk_percentage: float) -> None:
        """Update total exposure with new trade."""
        self.open_positions[trade_id] = {
            'size': position_size,
            'risk': risk_percentage
        }
        self.total_exposure += risk_percentage
        logger.info(f"Updated exposure: {self.total_exposure:.2%}") 