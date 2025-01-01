from typing import Dict, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class RiskMetrics:
    position_size: float
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    risk_per_trade: float
    margin_requirement: float

class RiskCalculator:
    def __init__(self, account_size: float, max_risk_per_trade: float = 0.01):
        self.account_size = account_size
        self.max_risk_per_trade = max_risk_per_trade
        
    def calculate_position_size(self, 
                              entry_price: float,
                              stop_loss: float,
                              leverage: float = 1.0) -> RiskMetrics:
        """Calculate appropriate position size based on risk parameters."""
        try:
            # Calculate risk amount
            risk_amount = self.account_size * self.max_risk_per_trade
            
            # Calculate price risk
            price_risk = abs(entry_price - stop_loss)
            
            # Calculate base position size
            position_size = (risk_amount / price_risk) * leverage
            
            # Calculate take profit based on R:R ratio
            risk_reward_ratio = 2.0  # Default 1:2 risk/reward
            take_profit = entry_price + (price_risk * risk_reward_ratio) if entry_price > stop_loss else entry_price - (price_risk * risk_reward_ratio)
            
            # Calculate margin requirement
            margin_requirement = (position_size * entry_price) / leverage
            
            return RiskMetrics(
                position_size=position_size,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_reward_ratio=risk_reward_ratio,
                risk_per_trade=risk_amount,
                margin_requirement=margin_requirement
            )
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            raise
            
    def validate_trade_risk(self, 
                          position_size: float,
                          entry_price: float,
                          stop_loss: float,
                          leverage: float = 1.0) -> Dict:
        """Validate if trade meets risk management criteria."""
        try:
            # Calculate actual risk
            price_risk = abs(entry_price - stop_loss)
            trade_risk = position_size * price_risk
            risk_percentage = trade_risk / self.account_size
            
            # Calculate margin usage
            margin_used = (position_size * entry_price) / leverage
            margin_percentage = margin_used / self.account_size
            
            validation = {
                'risk_acceptable': risk_percentage <= self.max_risk_per_trade,
                'margin_acceptable': margin_percentage <= 0.5,  # Max 50% margin usage
                'risk_percentage': risk_percentage,
                'margin_percentage': margin_percentage,
                'warnings': []
            }
            
            # Add warnings if needed
            if risk_percentage > self.max_risk_per_trade:
                validation['warnings'].append(
                    f"Risk per trade ({risk_percentage:.1%}) exceeds maximum ({self.max_risk_per_trade:.1%})"
                )
                
            if margin_percentage > 0.5:
                validation['warnings'].append(
                    f"Margin usage ({margin_percentage:.1%}) exceeds recommended maximum (50%)"
                )
                
            return validation
            
        except Exception as e:
            logger.error(f"Error validating trade risk: {str(e)}")
            raise
            
    def calculate_portfolio_risk(self, open_positions: List[Dict]) -> Dict:
        """Calculate current portfolio risk metrics."""
        try:
            total_margin_used = 0
            total_exposure = 0
            position_correlations = []
            
            for position in open_positions:
                margin_used = (position['size'] * position['entry_price']) / position.get('leverage', 1.0)
                total_margin_used += margin_used
                total_exposure += position['size'] * position['entry_price']
                
            return {
                'total_margin_used': total_margin_used,
                'margin_usage_percent': total_margin_used / self.account_size,
                'total_exposure': total_exposure,
                'exposure_ratio': total_exposure / self.account_size,
                'free_margin': self.account_size - total_margin_used,
                'position_count': len(open_positions)
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio risk: {str(e)}")
            raise
            
    def adjust_position_sizes(self, positions: List[Dict]) -> List[Dict]:
        """Adjust position sizes to maintain proper risk management."""
        try:
            total_risk = sum(pos['risk_amount'] for pos in positions)
            max_total_risk = self.account_size * 0.05  # Max 5% total risk
            
            if total_risk > max_total_risk:
                # Scale down positions proportionally
                scale_factor = max_total_risk / total_risk
                for position in positions:
                    position['size'] *= scale_factor
                    position['risk_amount'] *= scale_factor
                    
            return positions
            
        except Exception as e:
            logger.error(f"Error adjusting position sizes: {str(e)}")
            raise 