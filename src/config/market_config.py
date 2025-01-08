from typing import Dict, List

# Major Currency Pairs
MAJOR_PAIRS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF",
    "USD/CAD", "AUD/USD", "NZD/USD"
]

# Minor Currency Pairs
MINOR_PAIRS = [
    "EUR/GBP", "EUR/AUD", "GBP/JPY", "CHF/JPY",
    "EUR/CHF", "EUR/CAD", "AUD/CAD", "GBP/CHF"
]

# Exotic Currency Pairs
EXOTIC_PAIRS = [
    "USD/SGD", "USD/HKD", "USD/TRY", "USD/SEK",
    "USD/NOK", "USD/DKK", "EUR/NOK", "EUR/SEK"
]

# Commodity Pairs
COMMODITY_PAIRS = [
    "XAU/USD", "XAG/USD", "XPT/USD", "XPD/USD",
    "WTICO/USD", "NATGAS/USD"
]

# Cryptocurrency Pairs
CRYPTO_PAIRS = [
    "BTC/USD", "ETH/USD", "XRP/USD", "LTC/USD",
    "BCH/USD", "ADA/USD", "DOT/USD", "LINK/USD"
]

# All available trading pairs
ALL_PAIRS = MAJOR_PAIRS + MINOR_PAIRS + EXOTIC_PAIRS + COMMODITY_PAIRS + CRYPTO_PAIRS

# Timeframes available for trading
TIMEFRAMES = [
    "1m", "5m", "15m", "30m",
    "1h", "2h", "4h", "6h",
    "8h", "12h", "1d", "1w"
]

# Trading sessions
TRADING_SESSIONS = {
    "Sydney": {"start": "22:00", "end": "07:00"},
    "Tokyo": {"start": "00:00", "end": "09:00"},
    "London": {"start": "08:00", "end": "17:00"},
    "New York": {"start": "13:00", "end": "22:00"}
}

# Market specific settings
MARKET_SETTINGS = {
    "default": {
        "min_lot_size": 0.01,
        "max_lot_size": 100.0,
        "pip_value": 0.0001,
        "margin_requirement": 0.02,
        "min_distance_sl": 10,  # pips
        "min_distance_tp": 10,  # pips
        "commission": 0.0,
        "swap_long": -0.02,    # daily swap rate for long positions
        "swap_short": -0.02    # daily swap rate for short positions
    }
}

# Override settings for specific instruments
INSTRUMENT_SETTINGS = {
    "XAU/USD": {
        "min_lot_size": 0.01,
        "pip_value": 0.01,
        "margin_requirement": 0.05
    },
    "BTC/USD": {
        "min_lot_size": 0.001,
        "pip_value": 1.0,
        "margin_requirement": 0.1
    }
}

def get_pair_settings(pair: str) -> Dict:
    """Get settings for a specific trading pair."""
    base_settings = MARKET_SETTINGS["default"].copy()
    if pair in INSTRUMENT_SETTINGS:
        base_settings.update(INSTRUMENT_SETTINGS[pair])
    return base_settings

def get_available_pairs(pair_type: str = "all") -> List[str]:
    """Get available pairs by type."""
    pair_types = {
        "major": MAJOR_PAIRS,
        "minor": MINOR_PAIRS,
        "exotic": EXOTIC_PAIRS,
        "commodity": COMMODITY_PAIRS,
        "crypto": CRYPTO_PAIRS,
        "all": ALL_PAIRS
    }
    return pair_types.get(pair_type.lower(), []) 