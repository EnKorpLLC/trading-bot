from typing import Dict, Optional, List
import pandas as pd
import numpy as np
from ..core.market_analyzer import MarketCondition
from .base_strategy import BaseStrategy
import logging
import talib

logger = logging.getLogger(__name__)

class BreakoutStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Breakout Strategy")
        self.parameters = {
            'lookback_period': 20,      # Period for identifying range
            'volume_multiplier': 1.5,    # Required volume increase for breakout
            'min_range_period': 5,       # Minimum bars in range
            'atr_period': 14,           # ATR period for volatility
            'risk_reward_ratio': 2.0,    # Risk/Reward ratio for trades
            'min_range_size': 0.01      # Minimum range size as % of price
        }
        
    def analyze_market(self, data: Dict) -> Dict:
        """Analyze market for breakout patterns."""
        analysis_results = {}
        
        for symbol, market_condition in data.items():
            df = self._get_market_data(symbol)
            if df is None:
                continue
                
            # Calculate key levels and ranges
            ranges = self._identify_ranges(df)
            
            # Identify potential breakouts
            breakouts = self._identify_breakouts(df, ranges)
            
            analysis_results[symbol] = {
                'ranges': ranges,
                'breakouts': breakouts,
                'market_condition': market_condition
            }
            
        return analysis_results
        
    def generate_signals(self, analysis: Dict) -> Optional[Dict]:
        """Generate trading signals based on breakout analysis."""
        for symbol, data in analysis.items():
            breakouts = data['breakouts']
            market_condition = data['market_condition']
            
            for breakout in breakouts:
                if self._validate_breakout(breakout, market_condition):
                    return self._create_trade_signal(breakout, symbol)
                    
        return None
        
    def _identify_ranges(self, df: pd.DataFrame) -> List[Dict]:
        """Identify price ranges in the market."""
        ranges = []
        lookback = self.parameters['lookback_period']
        
        # Calculate ATR for volatility context
        atr = talib.ATR(df['high'], df['low'], df['close'], 
                       timeperiod=self.parameters['atr_period'])
        
        for i in range(lookback, len(df)):
            window = df.iloc[i-lookback:i]
            
            # Calculate range metrics
            range_high = window['high'].max()
            range_low = window['low'].min()
            range_size = range_high - range_low
            
            # Check if price is in a range
            if (range_size / df['close'].iloc[i] >= self.parameters['min_range_size'] and
                self._is_sideways(window)):
                ranges.append({
                    'high': range_high,
                    'low': range_low,
                    'size': range_size,
                    'volume_avg': window['volume'].mean(),
                    'atr': atr.iloc[i],
                    'period_start': window.index[0],
                    'period_end': window.index[-1]
                })
                
        return ranges
        
    def _identify_breakouts(self, df: pd.DataFrame, ranges: List[Dict]) -> List[Dict]:
        """Identify potential breakouts from ranges."""
        breakouts = []
        current_price = df['close'].iloc[-1]
        current_volume = df['volume'].iloc[-1]
        
        for range_data in ranges:
            # Check for upward breakout
            if (current_price > range_data['high'] and 
                current_volume > range_data['volume_avg'] * self.parameters['volume_multiplier']):
                breakouts.append({
                    'type': 'bullish',
                    'entry': current_price,
                    'range_high': range_data['high'],
                    'range_low': range_data['low'],
                    'atr': range_data['atr'],
                    'volume_increase': current_volume / range_data['volume_avg']
                })
                
            # Check for downward breakout
            elif (current_price < range_data['low'] and 
                  current_volume > range_data['volume_avg'] * self.parameters['volume_multiplier']):
                breakouts.append({
                    'type': 'bearish',
                    'entry': current_price,
                    'range_high': range_data['high'],
                    'range_low': range_data['low'],
                    'atr': range_data['atr'],
                    'volume_increase': current_volume / range_data['volume_avg']
                })
                
        return breakouts
        
    def _validate_breakout(self, breakout: Dict, market_condition: MarketCondition) -> bool:
        """Validate if a breakout is tradeable."""
        # Check market volatility
        if market_condition.volatility < 0.5 or market_condition.volatility > 2.0:
            return False
            
        # Check volume conditions
        if market_condition.volume_profile == 'low':
            return False
            
        # Check trend alignment
        if (breakout['type'] == 'bullish' and market_condition.trend == 'downtrend' or
            breakout['type'] == 'bearish' and market_condition.trend == 'uptrend'):
            return False
            
        return True
        
    def _create_trade_signal(self, breakout: Dict, symbol: str) -> Dict:
        """Create a trade signal from a valid breakout."""
        entry_price = breakout['entry']
        atr = breakout['atr']
        
        # Calculate stop loss and take profit using ATR
        stop_distance = atr * 1.5
        stop_loss = entry_price - stop_distance if breakout['type'] == 'bullish' else entry_price + stop_distance
        take_profit = entry_price + (stop_distance * self.parameters['risk_reward_ratio']) if breakout['type'] == 'bullish' else entry_price - (stop_distance * self.parameters['risk_reward_ratio'])
        
        return {
            'symbol': symbol,
            'side': 'buy' if breakout['type'] == 'bullish' else 'sell',
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'reason': f"{breakout['type']} breakout with {breakout['volume_increase']:.1f}x volume"
        }
        
    def _is_sideways(self, df: pd.DataFrame) -> bool:
        """Check if price action is sideways/ranging."""
        # Calculate linear regression slope
        prices = df['close'].values
        slope = np.polyfit(np.arange(len(prices)), prices, 1)[0]
        
        # Check if slope is relatively flat
        return abs(slope) < 0.1 * np.mean(prices)
        
    def _get_market_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get market data for analysis."""
        # TODO: Implement market data retrieval
        return None 