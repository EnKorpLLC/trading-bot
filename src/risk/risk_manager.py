from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from ..config.market_config import get_pair_settings
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class RiskParameters:
    max_account_risk: float = 0.02  # Maximum risk per trade (2% of account)
    max_daily_loss: float = 0.05    # Maximum daily loss (5% of account)
    max_weekly_loss: float = 0.10   # Maximum weekly loss (10% of account)
    max_drawdown: float = 0.20      # Maximum drawdown allowed (20% of account)
    max_position_size: float = 0.10  # Maximum position size (10% of account)
    max_correlated_pairs: int = 3    # Maximum number of correlated pairs to trade
    min_risk_reward: float = 2.0     # Minimum risk/reward ratio
    position_scaling: bool = True    # Whether to scale positions based on volatility
    max_open_positions: int = 5      # Maximum number of open positions
    max_daily_trades: int = 10       # Maximum number of trades per day

class PortfolioStats:
    def __init__(self):
        self.open_positions: Dict[str, Dict] = {}
        self.daily_trades: List[Dict] = []
        self.weekly_trades: List[Dict] = []
        self.peak_balance: float = 0
        self.current_balance: float = 0
        self.daily_pnl: float = 0
        self.weekly_pnl: float = 0
        self.max_drawdown: float = 0
        self.last_updated = datetime.now()

class RiskManager:
    def __init__(self, risk_params: Optional[RiskParameters] = None):
        self.params = risk_params or RiskParameters()
        self.portfolio = PortfolioStats()
        self.correlation_matrix: Optional[pd.DataFrame] = None
        self.volatility_data: Dict[str, float] = {}
        
    def calculate_position_size(self, account_balance: float, entry_price: float,
                              stop_loss: float, symbol: str) -> float:
        """Calculate safe position size based on risk parameters."""
        try:
            # Get market settings for the symbol
            market_settings = get_pair_settings(symbol)
            
            # Calculate risk amount in account currency
            risk_amount = account_balance * self.params.max_account_risk
            
            # Calculate pip value and risk in pips
            pip_value = market_settings['pip_value']
            risk_pips = abs(entry_price - stop_loss) / pip_value
            
            if risk_pips == 0:
                logger.error("Invalid risk pips calculation")
                return 0
                
            # Calculate base position size
            position_size = risk_amount / (risk_pips * pip_value)
            
            # Apply volatility scaling if enabled
            if self.params.position_scaling and symbol in self.volatility_data:
                volatility_factor = self._calculate_volatility_factor(symbol)
                position_size *= volatility_factor
            
            # Apply position limits
            max_size = account_balance * self.params.max_position_size
            position_size = min(position_size, max_size)
            
            # Round to market's minimum lot size
            min_lot = market_settings['min_lot_size']
            position_size = round(position_size / min_lot) * min_lot
            
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return 0
            
    def validate_trade(self, trade: Dict, account_balance: float) -> Dict:
        """Validate trade against risk parameters."""
        try:
            symbol = trade['symbol']
            entry = trade['entry_price']
            stop_loss = trade['stop_loss']
            take_profit = trade['take_profit']
            
            validation = {
                'valid': True,
                'messages': [],
                'adjusted_trade': trade.copy()
            }
            
            # Check daily loss limit
            if self.portfolio.daily_pnl <= -(account_balance * self.params.max_daily_loss):
                validation['valid'] = False
                validation['messages'].append("Daily loss limit reached")
                return validation
            
            # Check weekly loss limit
            if self.portfolio.weekly_pnl <= -(account_balance * self.params.max_weekly_loss):
                validation['valid'] = False
                validation['messages'].append("Weekly loss limit reached")
                return validation
            
            # Check drawdown limit
            current_drawdown = (self.portfolio.peak_balance - account_balance) / self.portfolio.peak_balance
            if current_drawdown >= self.params.max_drawdown:
                validation['valid'] = False
                validation['messages'].append("Maximum drawdown reached")
                return validation
            
            # Check risk/reward ratio
            risk = abs(entry - stop_loss)
            reward = abs(entry - take_profit)
            if (reward / risk) < self.params.min_risk_reward:
                validation['valid'] = False
                validation['messages'].append("Insufficient risk/reward ratio")
                return validation
            
            # Check correlation limits
            if not self._validate_correlation(symbol):
                validation['valid'] = False
                validation['messages'].append("Correlation limit reached for this pair")
                return validation
            
            # Check maximum open positions
            if len(self.portfolio.open_positions) >= self.params.max_open_positions:
                validation['valid'] = False
                validation['messages'].append("Maximum open positions reached")
                return validation
            
            # Check daily trade limit
            today_trades = len([t for t in self.portfolio.daily_trades 
                              if t['timestamp'].date() == datetime.now().date()])
            if today_trades >= self.params.max_daily_trades:
                validation['valid'] = False
                validation['messages'].append("Daily trade limit reached")
                return validation
            
            return validation
            
        except Exception as e:
            logger.error(f"Error validating trade: {str(e)}")
            return {'valid': False, 'messages': [str(e)], 'adjusted_trade': trade}
            
    def update_portfolio(self, trade_update: Dict):
        """Update portfolio statistics with new trade information."""
        try:
            symbol = trade_update['symbol']
            
            if trade_update['status'] == 'OPENED':
                self.portfolio.open_positions[symbol] = trade_update
                self.portfolio.daily_trades.append(trade_update)
                self.portfolio.weekly_trades.append(trade_update)
                
            elif trade_update['status'] == 'CLOSED':
                if symbol in self.portfolio.open_positions:
                    del self.portfolio.open_positions[symbol]
                
                # Update P&L
                pnl = trade_update.get('realized_pnl', 0)
                self.portfolio.daily_pnl += pnl
                self.portfolio.weekly_pnl += pnl
                self.portfolio.current_balance += pnl
                
                # Update peak balance
                if self.portfolio.current_balance > self.portfolio.peak_balance:
                    self.portfolio.peak_balance = self.portfolio.current_balance
                
                # Update drawdown
                current_drawdown = (self.portfolio.peak_balance - self.portfolio.current_balance) / self.portfolio.peak_balance
                self.portfolio.max_drawdown = max(self.portfolio.max_drawdown, current_drawdown)
            
            self._cleanup_historical_data()
            
        except Exception as e:
            logger.error(f"Error updating portfolio: {str(e)}")
            
    def _validate_correlation(self, new_symbol: str) -> bool:
        """Check if adding a new symbol would exceed correlation limits."""
        if self.correlation_matrix is None or new_symbol not in self.correlation_matrix.index:
            return True
            
        correlated_count = 0
        for symbol in self.portfolio.open_positions:
            if symbol in self.correlation_matrix.index:
                correlation = abs(self.correlation_matrix.loc[new_symbol, symbol])
                if correlation > 0.7:  # High correlation threshold
                    correlated_count += 1
                    
        return correlated_count < self.params.max_correlated_pairs
        
    def _calculate_volatility_factor(self, symbol: str) -> float:
        """Calculate position scaling factor based on volatility."""
        try:
            current_volatility = self.volatility_data.get(symbol, 1.0)
            avg_volatility = np.mean(list(self.volatility_data.values()))
            
            if avg_volatility == 0:
                return 1.0
                
            # Scale between 0.5 and 1.5 based on relative volatility
            factor = (current_volatility / avg_volatility)
            return max(0.5, min(1.5, factor))
            
        except Exception as e:
            logger.error(f"Error calculating volatility factor: {str(e)}")
            return 1.0
            
    def _cleanup_historical_data(self):
        """Clean up historical trade data."""
        now = datetime.now()
        
        # Clean up daily trades older than 1 day
        self.portfolio.daily_trades = [
            trade for trade in self.portfolio.daily_trades
            if trade['timestamp'] > now - timedelta(days=1)
        ]
        
        # Clean up weekly trades older than 7 days
        self.portfolio.weekly_trades = [
            trade for trade in self.portfolio.weekly_trades
            if trade['timestamp'] > now - timedelta(days=7)
        ]
        
        # Reset daily P&L if it's a new day
        if self.portfolio.last_updated.date() != now.date():
            self.portfolio.daily_pnl = 0
            
        # Reset weekly P&L if it's a new week
        if self.portfolio.last_updated.isocalendar()[1] != now.isocalendar()[1]:
            self.portfolio.weekly_pnl = 0
            
        self.portfolio.last_updated = now
        
    def update_market_data(self, correlation_matrix: pd.DataFrame,
                          volatility_data: Dict[str, float]):
        """Update market data used for risk calculations."""
        self.correlation_matrix = correlation_matrix
        self.volatility_data = volatility_data 