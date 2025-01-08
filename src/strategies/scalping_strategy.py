from typing import Dict, Optional, List
import pandas as pd
import numpy as np
from ..core.market_analyzer import MarketCondition
from .base_strategy import BaseStrategy
import logging

# Custom indicator implementations
def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    return data.ewm(span=period, adjust=False).mean()

def calculate_sma(data: pd.Series, period: int) -> pd.Series:
    return data.rolling(window=period).mean()

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

logger = logging.getLogger(__name__)

class ScalpingStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Scalping Strategy")
        self.parameters = {
            'rsi_period': 14,           # RSI period
            'rsi_overbought': 70,       # RSI overbought threshold
            'rsi_oversold': 30,         # RSI oversold threshold
            'ema_fast': 8,              # Fast EMA period
            'ema_slow': 21,             # Slow EMA period
            'atr_period': 14,           # ATR period for volatility
            'min_volume': 1.2,          # Minimum volume multiplier
            'profit_target': 0.002,     # Target profit (0.2%)
            'max_loss': 0.001           # Maximum loss (0.1%)
        }
        
    def analyze_market(self, data: Dict) -> Dict:
        """Analyze market for scalping opportunities."""
        analysis_results = {}
        
        for symbol, market_condition in data.items():
            df = self._get_market_data(symbol)
            if df is None:
                continue
                
            # Calculate technical indicators
            indicators = self._calculate_indicators(df)
            
            # Find potential setups
            setups = self._identify_setups(df, indicators)
            
            analysis_results[symbol] = {
                'setups': setups,
                'indicators': indicators,
                'market_condition': market_condition
            }
            
        return analysis_results
        
    def generate_signals(self, analysis: Dict) -> Optional[Dict]:
        """Generate trading signals based on scalping analysis."""
        for symbol, data in analysis.items():
            setups = data['setups']
            market_condition = data['market_condition']
            
            for setup in setups:
                if self._validate_setup(setup, market_condition):
                    return self._create_trade_signal(setup, symbol)
                    
        return None
        
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate technical indicators for scalping."""
        # Calculate RSI
        rsi = calculate_rsi(df['close'], period=self.parameters['rsi_period'])
        
        # Calculate EMAs
        ema_fast = calculate_ema(df['close'], period=self.parameters['ema_fast'])
        ema_slow = calculate_ema(df['close'], period=self.parameters['ema_slow'])
        
        # Calculate ATR
        atr = calculate_atr(df['high'], df['low'], df['close'], 
                          period=self.parameters['atr_period'])
        
        # Calculate volume moving average
        volume_ma = calculate_sma(df['volume'], period=20)
        
        return {
            'rsi': rsi,
            'ema_fast': ema_fast,
            'ema_slow': ema_slow,
            'atr': atr,
            'volume_ma': volume_ma
        }
        
    def _identify_setups(self, df: pd.DataFrame, indicators: Dict) -> List[Dict]:
        """Identify potential scalping setups."""
        setups = []
        
        # Get latest values
        current_price = df['close'].iloc[-1]
        current_rsi = indicators['rsi'].iloc[-1]
        current_volume = df['volume'].iloc[-1]
        volume_ma = indicators['volume_ma'].iloc[-1]
        ema_fast = indicators['ema_fast'].iloc[-1]
        ema_slow = indicators['ema_slow'].iloc[-1]
        
        # Check for bullish setup
        if (current_rsi < self.parameters['rsi_oversold'] and
            ema_fast > ema_slow and
            current_volume > volume_ma * self.parameters['min_volume']):
            setups.append({
                'type': 'bullish',
                'entry': current_price,
                'rsi': current_rsi,
                'volume_ratio': current_volume / volume_ma,
                'atr': indicators['atr'].iloc[-1]
            })
            
        # Check for bearish setup
        elif (current_rsi > self.parameters['rsi_overbought'] and
              ema_fast < ema_slow and
              current_volume > volume_ma * self.parameters['min_volume']):
            setups.append({
                'type': 'bearish',
                'entry': current_price,
                'rsi': current_rsi,
                'volume_ratio': current_volume / volume_ma,
                'atr': indicators['atr'].iloc[-1]
            })
            
        return setups
        
    def _validate_setup(self, setup: Dict, market_condition: MarketCondition) -> bool:
        """Validate if a scalping setup is tradeable."""
        # Check market volatility
        if market_condition.volatility > 1.5:  # Avoid high volatility
            return False
            
        # Check volume conditions
        if market_condition.volume_profile == 'low':
            return False
            
        # Check if market is ranging (preferred for scalping)
        if market_condition.trend not in ['ranging', 'weak_trend']:
            return False
            
        return True
        
    def _create_trade_signal(self, setup: Dict, symbol: str) -> Dict:
        """Create a trade signal from a valid scalping setup."""
        entry_price = setup['entry']
        atr = setup['atr']
        
        # Calculate tight stop loss and take profit
        stop_distance = entry_price * self.parameters['max_loss']
        take_profit_distance = entry_price * self.parameters['profit_target']
        
        if setup['type'] == 'bullish':
            stop_loss = entry_price - stop_distance
            take_profit = entry_price + take_profit_distance
        else:
            stop_loss = entry_price + stop_distance
            take_profit = entry_price - take_profit_distance
            
        return {
            'symbol': symbol,
            'side': 'buy' if setup['type'] == 'bullish' else 'sell',
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'reason': (f"{setup['type']} scalp setup - RSI: {setup['rsi']:.1f}, "
                      f"Volume: {setup['volume_ratio']:.1f}x")
        }
        
    def _get_market_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get market data for analysis."""
        # TODO: Implement market data retrieval
        return None 