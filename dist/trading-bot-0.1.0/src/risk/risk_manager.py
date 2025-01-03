from typing import Dict, List, Optional
from decimal import Decimal
import logging
from dataclasses import dataclass
from ..core.interfaces import IRiskManager
from ..utils.config_manager import ConfigManager

logger = logging.getLogger(__name__)

@dataclass
class RiskLimits:
    max_position_size: Decimal
    max_daily_loss: Decimal
    max_drawdown: Decimal
    max_leverage: Decimal
    position_limit: int
    max_correlation: float

class RiskManager(IRiskManager):
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.risk_limits = self._load_risk_limits()
        self.current_exposure = {}
        self.daily_pnl = Decimal('0')
        self.peak_balance = Decimal('0')
        self.positions = {}
        self.correlation_matrix = {}
        
    def validate_trade(self, trade_request: Dict) -> bool:
        """Validate trade against risk parameters."""
        try:
            # Check position size
            if not self._validate_position_size(trade_request):
                return False
                
            # Check leverage
            if not self._validate_leverage(trade_request):
                return False
                
            # Check correlation
            if not self._validate_correlation(trade_request):
                return False
                
            # Check position limits
            if not self._validate_position_limits(trade_request):
                return False
                
            # Check drawdown
            if not self._validate_drawdown():
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating trade: {str(e)}")
            return False
            
    def update_exposure(self, position: Dict):
        """Update current exposure and risk metrics."""
        try:
            symbol = position['symbol']
            size = Decimal(str(position['size']))
            
            # Update position tracking
            if size == 0:
                self.positions.pop(symbol, None)
            else:
                self.positions[symbol] = position
                
            # Update exposure
            self.current_exposure[symbol] = size
            
            # Update daily P&L
            self.daily_pnl += Decimal(str(position.get('realized_pnl', 0)))
            
            # Update peak balance
            current_balance = Decimal(str(position.get('account_balance', 0)))
            self.peak_balance = max(self.peak_balance, current_balance)
            
            # Update correlation matrix
            self._update_correlation_matrix()
            
        except Exception as e:
            logger.error(f"Error updating exposure: {str(e)}")
            
    def _validate_position_size(self, trade_request: Dict) -> bool:
        """Validate position size against limits."""
        size = Decimal(str(trade_request['size']))
        symbol = trade_request['symbol']
        
        # Check absolute size
        if size > self.risk_limits.max_position_size:
            logger.warning(f"Position size {size} exceeds limit {self.risk_limits.max_position_size}")
            return False
            
        # Check relative to account size
        account_size = self._get_account_size()
        if size / account_size > Decimal('0.1'):  # 10% max per position
            logger.warning("Position size exceeds 10% of account size")
            return False
            
        return True
        
    def _validate_leverage(self, trade_request: Dict) -> bool:
        """Validate leverage against limits."""
        leverage = self._calculate_leverage(trade_request)
        if leverage > self.risk_limits.max_leverage:
            logger.warning(f"Leverage {leverage} exceeds limit {self.risk_limits.max_leverage}")
            return False
        return True
        
    def _validate_correlation(self, trade_request: Dict) -> bool:
        """Validate position correlation."""
        symbol = trade_request['symbol']
        
        for existing_symbol, correlation in self.correlation_matrix.get(symbol, {}).items():
            if (existing_symbol in self.positions and 
                abs(correlation) > self.risk_limits.max_correlation):
                logger.warning(f"High correlation between {symbol} and {existing_symbol}")
                return False
                
        return True
        
    def _validate_position_limits(self, trade_request: Dict) -> bool:
        """Validate number of open positions."""
        if len(self.positions) >= self.risk_limits.position_limit:
            logger.warning("Maximum number of positions reached")
            return False
        return True
        
    def _validate_drawdown(self) -> bool:
        """Validate current drawdown."""
        if self.peak_balance == 0:
            return True
            
        current_balance = self._get_account_size()
        drawdown = (self.peak_balance - current_balance) / self.peak_balance
        
        if drawdown > self.risk_limits.max_drawdown:
            logger.warning(f"Drawdown {drawdown} exceeds limit {self.risk_limits.max_drawdown}")
            return False
            
        return True
        
    def _load_risk_limits(self) -> RiskLimits:
        """Load risk limits from configuration."""
        risk_config = self.config.get_setting('risk_management', {})
        
        return RiskLimits(
            max_position_size=Decimal(str(risk_config.get('max_position_size', 0))),
            max_daily_loss=Decimal(str(risk_config.get('max_daily_loss', 0))),
            max_drawdown=Decimal(str(risk_config.get('max_drawdown', 0.1))),
            max_leverage=Decimal(str(risk_config.get('max_leverage', 3))),
            position_limit=int(risk_config.get('position_limit', 5)),
            max_correlation=float(risk_config.get('max_correlation', 0.7))
        ) 