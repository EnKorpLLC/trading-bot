import pytest
from src.core.engine import TradingEngine
from src.risk.risk_manager import RiskManager
from src.data.data_manager import DataManager

class TestTradingFlow:
    @pytest.fixture
    def trading_system(self, test_config):
        # Initialize components
        config_manager = ConfigManager()
        risk_manager = RiskManager(config_manager)
        data_manager = DataManager(CacheManager())
        trading_engine = TradingEngine(risk_manager, data_manager)
        
        return {
            'engine': trading_engine,
            'risk': risk_manager,
            'data': data_manager
        }
        
    def test_complete_trade_flow(self, trading_system, mock_market_data):
        # Test complete trading flow
        engine = trading_system['engine']
        
        # 1. Place trade
        trade_request = {
            'symbol': 'BTC/USD',
            'side': 'buy',
            'size': '100'
        }
        trade = engine.execute_trade(trade_request)
        assert trade['status'] == 'open'
        
        # 2. Update position
        engine.update_position(trade['id'], {'pnl': 50})
        
        # 3. Close trade
        close_result = engine.close_trade(trade['id'])
        assert close_result['status'] == 'closed' 