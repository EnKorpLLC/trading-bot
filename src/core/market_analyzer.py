from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MarketCondition:
    trend: str  # 'uptrend', 'downtrend', or 'ranging'
    volatility: float
    volume_profile: str  # 'high', 'medium', 'low'
    support_levels: List[float]
    resistance_levels: List[float]
    key_levels: Dict[str, float]

class MarketAnalyzer:
    def __init__(self):
        self.timeframes = ['1D', '4H', '1H', '15M', '5M']
        self.indicators = {}
        self.current_condition: Optional[MarketCondition] = None
        
    def calculate_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate technical indicators for analysis."""
        try:
            indicators = {}
            
            # Calculate moving averages
            indicators['sma_20'] = data['close'].rolling(window=20).mean()
            indicators['sma_50'] = data['close'].rolling(window=50).mean()
            indicators['ema_21'] = data['close'].ewm(span=21).mean()
            
            # Calculate RSI
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            indicators['rsi'] = 100 - (100 / (1 + rs))
            
            # Calculate volatility
            indicators['atr'] = self.calculate_atr(data)
            
            # Volume analysis
            indicators['volume_sma'] = data['volume'].rolling(window=20).mean()
            indicators['volume_ratio'] = data['volume'] / indicators['volume_sma']
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            raise

    def calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high = data['high']
        low = data['low']
        close = data['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr

    def identify_key_levels(self, data: pd.DataFrame) -> Dict[str, List[float]]:
        """Identify support and resistance levels."""
        try:
            levels = {
                'support': [],
                'resistance': []
            }
            
            # Find swing lows for support
            for i in range(2, len(data) - 2):
                if (data['low'].iloc[i] < data['low'].iloc[i-1] and 
                    data['low'].iloc[i] < data['low'].iloc[i-2] and
                    data['low'].iloc[i] < data['low'].iloc[i+1] and
                    data['low'].iloc[i] < data['low'].iloc[i+2]):
                    levels['support'].append(data['low'].iloc[i])
            
            # Find swing highs for resistance
            for i in range(2, len(data) - 2):
                if (data['high'].iloc[i] > data['high'].iloc[i-1] and 
                    data['high'].iloc[i] > data['high'].iloc[i-2] and
                    data['high'].iloc[i] > data['high'].iloc[i+1] and
                    data['high'].iloc[i] > data['high'].iloc[i+2]):
                    levels['resistance'].append(data['high'].iloc[i])
            
            return levels
            
        except Exception as e:
            logger.error(f"Error identifying key levels: {str(e)}")
            raise

    def analyze_market_condition(self, data: pd.DataFrame) -> MarketCondition:
        """Analyze current market condition."""
        try:
            indicators = self.calculate_indicators(data)
            levels = self.identify_key_levels(data)
            
            # Determine trend
            trend = 'ranging'
            if (indicators['sma_20'].iloc[-1] > indicators['sma_50'].iloc[-1] and
                data['close'].iloc[-1] > indicators['sma_20'].iloc[-1]):
                trend = 'uptrend'
            elif (indicators['sma_20'].iloc[-1] < indicators['sma_50'].iloc[-1] and
                  data['close'].iloc[-1] < indicators['sma_20'].iloc[-1]):
                trend = 'downtrend'
            
            # Analyze volatility
            current_atr = indicators['atr'].iloc[-1]
            avg_atr = indicators['atr'].mean()
            volatility = current_atr / avg_atr
            
            # Analyze volume
            volume_profile = 'medium'
            if indicators['volume_ratio'].iloc[-1] > 1.5:
                volume_profile = 'high'
            elif indicators['volume_ratio'].iloc[-1] < 0.5:
                volume_profile = 'low'
            
            self.current_condition = MarketCondition(
                trend=trend,
                volatility=volatility,
                volume_profile=volume_profile,
                support_levels=levels['support'],
                resistance_levels=levels['resistance'],
                key_levels={
                    'last_price': data['close'].iloc[-1],
                    'daily_high': data['high'].max(),
                    'daily_low': data['low'].min()
                }
            )
            
            return self.current_condition
            
        except Exception as e:
            logger.error(f"Error analyzing market condition: {str(e)}")
            raise 