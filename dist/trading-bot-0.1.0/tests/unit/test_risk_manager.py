import pytest
from decimal import Decimal
from src.risk.risk_manager import RiskManager, RiskLimits
from src.utils.config_manager import ConfigManager

class TestRiskManager:
    @pytest.fixture
    def risk_manager(self, test_config):
        config_manager = ConfigManager()
        config_manager.update_setting('risk_management', test_config['risk_management'])
        return RiskManager(config_manager)
        
    def test_validate_position_size(self, risk_manager):
        # Test valid position size
        trade_request = {
            'symbol': 'BTC/USD',
            'size': '100'
        }
        assert risk_manager._validate_position_size(trade_request)
        
        # Test invalid position size
        trade_request['size'] = '2000'
        assert not risk_manager._validate_position_size(trade_request)
        
    def test_validate_drawdown(self, risk_manager):
        # Set up initial state
        risk_manager.peak_balance = Decimal('1000')
        risk_manager.current_balance = Decimal('950')
        
        # Test within drawdown limit
        assert risk_manager._validate_drawdown()
        
        # Test exceeding drawdown limit
        risk_manager.current_balance = Decimal('850')
        assert not risk_manager._validate_drawdown() 