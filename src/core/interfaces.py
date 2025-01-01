from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime

class ITradeExecutor(ABC):
    @abstractmethod
    def execute_trade(self, trade_request: Dict) -> Dict:
        """Execute a trade."""
        pass
        
    @abstractmethod
    def cancel_trade(self, trade_id: str) -> bool:
        """Cancel a trade."""
        pass

class IDataProvider(ABC):
    @abstractmethod
    def get_market_data(self, symbol: str, timeframe: str) -> Dict:
        """Get market data."""
        pass
        
    @abstractmethod
    def subscribe_to_feed(self, symbol: str, callback: callable):
        """Subscribe to market data feed."""
        pass

class IRiskManager(ABC):
    @abstractmethod
    def validate_trade(self, trade_request: Dict) -> bool:
        """Validate trade against risk parameters."""
        pass
        
    @abstractmethod
    def update_exposure(self, position: Dict):
        """Update current exposure."""
        pass

class IStrategyExecutor(ABC):
    @abstractmethod
    def execute_strategy(self, strategy_id: str, market_data: Dict) -> Optional[Dict]:
        """Execute trading strategy."""
        pass
        
    @abstractmethod
    def update_parameters(self, strategy_id: str, parameters: Dict):
        """Update strategy parameters."""
        pass 