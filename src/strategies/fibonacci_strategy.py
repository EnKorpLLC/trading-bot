from typing import Dict, Optional, List
import pandas as pd
import numpy as np
from ..core.market_analyzer import MarketCondition
from .base_strategy import BaseStrategy
import logging

logger = logging.getLogger(__name__)

def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average"""
    return data.ewm(span=period, adjust=False).mean()

class FibonacciStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Fibonacci Strategy")
        self.parameters = {
            'trend_period': 50,         # Period for trend identification
            'swing_threshold': 0.01,    # Minimum swing size (1%)
            'fib_levels': [0.236, 0.382, 0.5, 0.618, 0.786],  # Fibonacci levels
            'volume_threshold': 1.3,    # Volume requirement
            'risk_reward_ratio': 1.5,   # Risk/Reward ratio
            'confirmation_period': 3     # Bars needed for confirmation
        }
        self.identified_swings = []
        
    def analyze_market(self, data: Dict) -> Dict:
        """Analyze market for Fibonacci retracement opportunities."""
        analysis_results = {}
        
        for symbol, market_condition in data.items():
            df = self._get_market_data(symbol)
            if df is None:
                continue
                
            # Identify trend and swings
            trend_info = self._identify_trend(df)
            swings = self._identify_swings(df, trend_info)
            
            # Calculate Fibonacci levels
            fib_levels = self._calculate_fib_levels(df, swings)
            
            # Find potential setups
            setups = self._identify_setups(df, fib_levels, trend_info)
            
            analysis_results[symbol] = {
                'trend': trend_info,
                'swings': swings,
                'fib_levels': fib_levels,
                'setups': setups,
                'market_condition': market_condition
            }
            
        return analysis_results
        
    def generate_signals(self, analysis: Dict) -> Optional[Dict]:
        """Generate trading signals based on Fibonacci analysis."""
        for symbol, data in analysis.items():
            setups = data['setups']
            market_condition = data['market_condition']
            
            for setup in setups:
                if self._validate_setup(setup, market_condition):
                    return self._create_trade_signal(setup, symbol)
                    
        return None
        
    def _identify_trend(self, df: pd.DataFrame) -> Dict:
        """Identify market trend using multiple timeframes."""
        # Replace talib.EMA with custom EMA implementation
        ema20 = calculate_ema(df['close'], timeperiod=20)
        ema50 = calculate_ema(df['close'], timeperiod=50)
        ema200 = calculate_ema(df['close'], timeperiod=200)
        
        current_price = df['close'].iloc[-1]
        
        # Determine trend strength and direction
        trend_direction = ('uptrend' if current_price > ema50.iloc[-1] else 'downtrend')
        trend_strength = 'strong' if abs(current_price - ema50.iloc[-1]) > df['atr'].iloc[-1] else 'weak'
        
        return {
            'direction': trend_direction,
            'strength': trend_strength,
            'ema20': ema20,
            'ema50': ema50,
            'ema200': ema200
        }
        
    def _identify_swings(self, df: pd.DataFrame, trend_info: Dict) -> List[Dict]:
        """Identify significant price swings."""
        swings = []
        min_swing_size = df['close'].mean() * self.parameters['swing_threshold']
        
        # Find swing highs and lows
        for i in range(2, len(df)-2):
            # Swing high
            if (df['high'].iloc[i] > df['high'].iloc[i-1] and 
                df['high'].iloc[i] > df['high'].iloc[i-2] and
                df['high'].iloc[i] > df['high'].iloc[i+1] and
                df['high'].iloc[i] > df['high'].iloc[i+2]):
                swing_size = df['high'].iloc[i] - df['low'].iloc[i-2:i+2].min()
                if swing_size >= min_swing_size:
                    swings.append({
                        'type': 'high',
                        'price': df['high'].iloc[i],
                        'time': df.index[i],
                        'size': swing_size
                    })
                    
            # Swing low
            if (df['low'].iloc[i] < df['low'].iloc[i-1] and 
                df['low'].iloc[i] < df['low'].iloc[i-2] and
                df['low'].iloc[i] < df['low'].iloc[i+1] and
                df['low'].iloc[i] < df['low'].iloc[i+2]):
                swing_size = df['high'].iloc[i-2:i+2].max() - df['low'].iloc[i]
                if swing_size >= min_swing_size:
                    swings.append({
                        'type': 'low',
                        'price': df['low'].iloc[i],
                        'time': df.index[i],
                        'size': swing_size
                    })
                    
        return swings
        
    def _calculate_fib_levels(self, df: pd.DataFrame, swings: List[Dict]) -> List[Dict]:
        """Calculate Fibonacci retracement levels for identified swings."""
        fib_levels = []
        
        for i in range(1, len(swings)):
            swing1 = swings[i-1]
            swing2 = swings[i]
            
            if swing1['type'] != swing2['type']:  # Only calculate for alternating swings
                high = max(swing1['price'], swing2['price'])
                low = min(swing1['price'], swing2['price'])
                range_size = high - low
                
                levels = {
                    'start_price': swing1['price'],
                    'end_price': swing2['price'],
                    'start_time': swing1['time'],
                    'end_time': swing2['time'],
                    'direction': 'up' if swing2['price'] > swing1['price'] else 'down',
                    'levels': {}
                }
                
                # Calculate retracement levels
                for fib in self.parameters['fib_levels']:
                    if levels['direction'] == 'up':
                        levels['levels'][fib] = high - (range_size * fib)
                    else:
                        levels['levels'][fib] = low + (range_size * fib)
                        
                fib_levels.append(levels)
                
        return fib_levels
        
    def _identify_setups(self, df: pd.DataFrame, fib_levels: List[Dict], trend_info: Dict) -> List[Dict]:
        """Identify potential trading setups at Fibonacci levels."""
        setups = []
        current_price = df['close'].iloc[-1]
        
        for fib in fib_levels[-3:]:  # Look at most recent levels
            for level_value, price_level in fib['levels'].items():
                # Check if price is near a Fibonacci level
                if abs(current_price - price_level) / price_level < 0.001:
                    setups.append({
                        'type': 'bullish' if fib['direction'] == 'up' else 'bearish',
                        'entry': current_price,
                        'fib_level': level_value,
                        'swing_start': fib['start_price'],
                        'swing_end': fib['end_price'],
                        'level_price': price_level
                    })
                    
        return setups
        
    def _validate_setup(self, setup: Dict, market_condition: MarketCondition) -> bool:
        """Validate if a Fibonacci setup is tradeable."""
        # Check market conditions
        if market_condition.volume_profile == 'low':
            return False
            
        # Check trend alignment
        if (setup['type'] == 'bullish' and market_condition.trend == 'downtrend' or
            setup['type'] == 'bearish' and market_condition.trend == 'uptrend'):
            return False
            
        return True
        
    def _create_trade_signal(self, setup: Dict, symbol: str) -> Dict:
        """Create a trade signal from a valid Fibonacci setup."""
        entry_price = setup['entry']
        
        # Calculate stop loss and take profit based on swing points
        if setup['type'] == 'bullish':
            stop_loss = min(setup['swing_start'], setup['swing_end']) * 0.99  # 1% below swing
            range_size = entry_price - stop_loss
            take_profit = entry_price + (range_size * self.parameters['risk_reward_ratio'])
        else:
            stop_loss = max(setup['swing_start'], setup['swing_end']) * 1.01  # 1% above swing
            range_size = stop_loss - entry_price
            take_profit = entry_price - (range_size * self.parameters['risk_reward_ratio'])
            
        return {
            'symbol': symbol,
            'side': 'buy' if setup['type'] == 'bullish' else 'sell',
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'reason': f"{setup['type']} setup at {setup['fib_level']} Fibonacci level"
        }
        
    def _get_market_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get market data for analysis."""
        # TODO: Implement market data retrieval
        return None 