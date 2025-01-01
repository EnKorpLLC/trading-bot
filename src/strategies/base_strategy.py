from abc import ABC, abstractmethod
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class BaseStrategy(ABC):
    def __init__(self, name: str):
        self.name = name
        self.parameters: Dict = {}
        self.is_active: bool = False
        
    @abstractmethod
    def analyze_market(self, data: Dict) -> Dict:
        """Analyze market conditions and return analysis results."""
        pass
        
    @abstractmethod
    def generate_signals(self, analysis: Dict) -> Optional[Dict]:
        """Generate trading signals based on analysis."""
        pass
        
    @abstractmethod
    def validate_setup(self, signal: Dict) -> bool:
        """Validate if the trading setup meets all criteria."""
        pass
        
    def update_parameters(self, new_params: Dict) -> None:
        """Update strategy parameters."""
        self.parameters.update(new_params)
        logger.info(f"Updated parameters for {self.name} strategy")
        
    def activate(self) -> None:
        """Activate the strategy."""
        self.is_active = True
        logger.info(f"Activated {self.name} strategy")
        
    def deactivate(self) -> None:
        """Deactivate the strategy."""
        self.is_active = False
        logger.info(f"Deactivated {self.name} strategy") 