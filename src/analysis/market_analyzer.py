from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from ..config.market_config import ALL_PAIRS, TIMEFRAMES
from ..core.tradelocker_client import TradeLockerClient

logger = logging.getLogger(__name__)

class MarketAnalyzer:
    def __init__(self, client: TradeLockerClient):
        self.client = client
        self.correlation_matrix: Optional[pd.DataFrame] = None
        self.volatility_data: Dict[str, float] = {}
        self.atr_data: Dict[str, float] = {}
        self.market_conditions: Dict[str, Dict] = {}
        self.last_update = datetime.min
        self.update_interval = timedelta(minutes=15)  # Update every 15 minutes
        
    async def update_market_metrics(self):
        """Update all market metrics if needed."""
        now = datetime.now()
        if now - self.last_update < self.update_interval:
            return
            
        try:
            # Update correlation matrix
            await self._update_correlation_matrix()
            
            # Update volatility metrics
            await self._update_volatility_metrics()
            
            # Update market conditions
            await self._update_market_conditions()
            
            self.last_update = now
            
        except Exception as e:
            logger.error(f"Error updating market metrics: {str(e)}")
            
    async def _update_correlation_matrix(self):
        """Calculate correlation matrix for all trading pairs."""
        try:
            # Get daily close prices for all pairs
            price_data = {}
            for symbol in ALL_PAIRS:
                data = await self._get_historical_data(symbol, "1d", 30)  # 30 days of daily data
                if not data.empty:
                    price_data[symbol] = data['close']
                    
            if price_data:
                # Create DataFrame with all price series
                df = pd.DataFrame(price_data)
                
                # Calculate returns
                returns = df.pct_change().dropna()
                
                # Calculate correlation matrix
                self.correlation_matrix = returns.corr()
                
        except Exception as e:
            logger.error(f"Error updating correlation matrix: {str(e)}")
            
    async def _update_volatility_metrics(self):
        """Calculate volatility metrics for all pairs."""
        try:
            for symbol in ALL_PAIRS:
                # Get hourly data for more granular volatility calculation
                data = await self._get_historical_data(symbol, "1h", 168)  # 1 week of hourly data
                
                if not data.empty:
                    # Calculate returns volatility
                    returns = data['close'].pct_change().dropna()
                    volatility = returns.std() * np.sqrt(24)  # Annualized volatility
                    self.volatility_data[symbol] = volatility
                    
                    # Calculate ATR
                    atr = self._calculate_atr(data)
                    self.atr_data[symbol] = atr
                    
        except Exception as e:
            logger.error(f"Error updating volatility metrics: {str(e)}")
            
    async def _update_market_conditions(self):
        """Analyze current market conditions for all pairs."""
        try:
            for symbol in ALL_PAIRS:
                data = await self._get_historical_data(symbol, "1h", 200)  # 200 hours for trend analysis
                
                if not data.empty:
                    conditions = self._analyze_market_conditions(data)
                    self.market_conditions[symbol] = conditions
                    
        except Exception as e:
            logger.error(f"Error updating market conditions: {str(e)}")
            
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range."""
        try:
            high = data['high']
            low = data['low']
            close = data['close']
            
            # Calculate True Range
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # Calculate ATR
            atr = tr.rolling(window=period).mean().iloc[-1]
            return atr
            
        except Exception as e:
            logger.error(f"Error calculating ATR: {str(e)}")
            return 0.0
            
    def _analyze_market_conditions(self, data: pd.DataFrame) -> Dict:
        """Analyze market conditions including trend, volatility, and volume profile."""
        try:
            close = data['close']
            volume = data['volume']
            
            # Calculate EMAs for trend
            ema20 = close.ewm(span=20).mean()
            ema50 = close.ewm(span=50).mean()
            ema200 = close.ewm(span=200).mean()
            
            # Determine trend
            last_close = close.iloc[-1]
            trend = "sideways"
            if last_close > ema50.iloc[-1] > ema200.iloc[-1]:
                trend = "uptrend"
            elif last_close < ema50.iloc[-1] < ema200.iloc[-1]:
                trend = "downtrend"
                
            # Calculate volatility
            returns_vol = close.pct_change().std() * np.sqrt(24)
            
            # Analyze volume profile
            avg_volume = volume.mean()
            recent_volume = volume.tail(24).mean()
            volume_profile = "normal"
            if recent_volume > avg_volume * 1.5:
                volume_profile = "high"
            elif recent_volume < avg_volume * 0.5:
                volume_profile = "low"
                
            # Calculate momentum
            roc = ((close.iloc[-1] - close.iloc[-20]) / close.iloc[-20]) * 100
            
            return {
                "trend": trend,
                "volatility": returns_vol,
                "volume_profile": volume_profile,
                "momentum": roc,
                "support_resistance": self._find_support_resistance(data),
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing market conditions: {str(e)}")
            return {}
            
    def _find_support_resistance(self, data: pd.DataFrame, 
                               window: int = 20, 
                               threshold: float = 0.02) -> Dict[str, List[float]]:
        """Find potential support and resistance levels."""
        try:
            highs = data['high'].rolling(window=window, center=True).max()
            lows = data['low'].rolling(window=window, center=True).min()
            
            # Find local maxima and minima
            resistance_levels = []
            support_levels = []
            
            for i in range(window, len(data) - window):
                # Check for resistance
                if highs.iloc[i] == data['high'].iloc[i]:
                    level = data['high'].iloc[i]
                    if not any(abs(level - r) / r < threshold for r in resistance_levels):
                        resistance_levels.append(level)
                
                # Check for support
                if lows.iloc[i] == data['low'].iloc[i]:
                    level = data['low'].iloc[i]
                    if not any(abs(level - s) / s < threshold for s in support_levels):
                        support_levels.append(level)
            
            return {
                "support": sorted(support_levels)[-3:],  # Top 3 support levels
                "resistance": sorted(resistance_levels)[:3]  # Bottom 3 resistance levels
            }
            
        except Exception as e:
            logger.error(f"Error finding support/resistance: {str(e)}")
            return {"support": [], "resistance": []}
            
    async def _get_historical_data(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Get historical price data with error handling."""
        try:
            data = await self.client.get_historical_data(symbol, timeframe, limit)
            return data if not data.empty else pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {str(e)}")
            return pd.DataFrame()
            
    def get_market_metrics(self, symbol: str) -> Dict:
        """Get all market metrics for a symbol."""
        return {
            "correlation": self.correlation_matrix.loc[symbol] if self.correlation_matrix is not None else None,
            "volatility": self.volatility_data.get(symbol),
            "atr": self.atr_data.get(symbol),
            "market_conditions": self.market_conditions.get(symbol)
        } 