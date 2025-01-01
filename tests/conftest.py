import pytest
from pathlib import Path
import sys
import os

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.append(str(src_path))

@pytest.fixture
def test_config():
    """Provide test configuration."""
    return {
        "api_credentials": {
            "exchange": "test_exchange",
            "api_key": "test_key",
            "api_secret": "test_secret"
        },
        "risk_management": {
            "max_position_size": 1000,
            "max_daily_loss": 500,
            "max_drawdown": 0.1
        }
    }

@pytest.fixture
def mock_market_data():
    """Provide mock market data."""
    return {
        "symbol": "BTC/USD",
        "timeframe": "1h",
        "data": [
            {
                "timestamp": "2024-01-01T00:00:00",
                "open": 40000,
                "high": 41000,
                "low": 39000,
                "close": 40500,
                "volume": 100
            }
        ]
    } 