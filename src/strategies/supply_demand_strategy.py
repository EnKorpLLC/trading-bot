from typing import Dict, Optional, List
import pandas as pd
import numpy as np
from ..core.market_analyzer import MarketCondition
from .base_strategy import BaseStrategy
import logging

logger = logging.getLogger(__name__)

class SupplyDemandStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Supply Demand Strategy")
        self.parameters = {
            'zone_lookback': 30,        # Bars to look back for zones
            'min_zone_size': 0.002,     # Minimum zone size as % of price
            'min_zone_strength': 2,     # Minimum times zone was respected
            'volume_threshold': 1.5,     # Volume requirement for zone creation
            'risk_reward_ratio': 2.0,    # Risk/Reward ratio for trades
            'zone_expiry': 100          # Maximum age of zones in bars
        }
        self.zones: Dict[str, List[Dict]] = {'supply': [], 'demand': []}
        
    def analyze_market(self, data: Dict) -> Dict:
        """Analyze market for supply and demand zones."""
        analysis_results = {}
        
        for symbol, market_condition in data.items():
            df = self._get_market_data(symbol)
            if df is None:
                continue
                
            # Update supply and demand zones
            self._update_zones(df)
            
            # Find active zone interactions
            interactions = self._find_zone_interactions(df)
            
            analysis_results[symbol] = {
                'zones': self.zones,
                'interactions': interactions,
                'market_condition': market_condition
            }
            
        return analysis_results
        
    def generate_signals(self, analysis: Dict) -> Optional[Dict]:
        """Generate trading signals based on zone interactions."""
        for symbol, data in analysis.items():
            interactions = data['interactions']
            market_condition = data['market_condition']
            
            for interaction in interactions:
                if self._validate_interaction(interaction, market_condition):
                    return self._create_trade_signal(interaction, symbol)
                    
        return None
        
    def _update_zones(self, df: pd.DataFrame):
        """Update supply and demand zones."""
        # Remove expired zones
        self._clean_expired_zones(df)
        
        # Identify new zones
        new_zones = self._identify_zones(df)
        
        # Add new zones
        self.zones['supply'].extend(new_zones['supply'])
        self.zones['demand'].extend(new_zones['demand'])
        
    def _identify_zones(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """Identify supply and demand zones."""
        new_zones = {'supply': [], 'demand': []}
        lookback = self.parameters['zone_lookback']
        
        for i in range(lookback, len(df)):
            window = df.iloc[i-lookback:i]
            current_price = df['close'].iloc[i]
            
            # Check for supply zone formation
            if self._is_supply_zone(window):
                zone = {
                    'type': 'supply',
                    'upper': window['high'].max(),
                    'lower': window['close'].min(),
                    'strength': 1,
                    'created_at': window.index[-1],
                    'last_test': window.index[-1],
                    'volume': window['volume'].mean()
                }
                new_zones['supply'].append(zone)
                
            # Check for demand zone formation
            if self._is_demand_zone(window):
                zone = {
                    'type': 'demand',
                    'upper': window['close'].max(),
                    'lower': window['low'].min(),
                    'strength': 1,
                    'created_at': window.index[-1],
                    'last_test': window.index[-1],
                    'volume': window['volume'].mean()
                }
                new_zones['demand'].append(zone)
                
        return new_zones
        
    def _is_supply_zone(self, df: pd.DataFrame) -> bool:
        """Check if price action forms a supply zone."""
        # Check for strong rejection from highs
        high_point = df['high'].max()
        rejection_size = high_point - df['close'].iloc[-1]
        avg_range = (df['high'] - df['low']).mean()
        
        return (rejection_size > avg_range * 1.5 and
                df['volume'].iloc[-1] > df['volume'].mean() * self.parameters['volume_threshold'])
                
    def _is_demand_zone(self, df: pd.DataFrame) -> bool:
        """Check if price action forms a demand zone."""
        # Check for strong rejection from lows
        low_point = df['low'].min()
        rejection_size = df['close'].iloc[-1] - low_point
        avg_range = (df['high'] - df['low']).mean()
        
        return (rejection_size > avg_range * 1.5 and
                df['volume'].iloc[-1] > df['volume'].mean() * self.parameters['volume_threshold'])
                
    def _find_zone_interactions(self, df: pd.DataFrame) -> List[Dict]:
        """Find current interactions with supply/demand zones."""
        interactions = []
        current_price = df['close'].iloc[-1]
        
        # Check supply zones
        for zone in self.zones['supply']:
            if zone['lower'] <= current_price <= zone['upper']:
                interactions.append({
                    'type': 'supply',
                    'zone': zone,
                    'price': current_price
                })
                
        # Check demand zones
        for zone in self.zones['demand']:
            if zone['lower'] <= current_price <= zone['upper']:
                interactions.append({
                    'type': 'demand',
                    'zone': zone,
                    'price': current_price
                })
                
        return interactions
        
    def _validate_interaction(self, interaction: Dict, market_condition: MarketCondition) -> bool:
        """Validate if a zone interaction is tradeable."""
        zone = interaction['zone']
        
        # Check zone strength
        if zone['strength'] < self.parameters['min_zone_strength']:
            return False
            
        # Check market conditions
        if market_condition.volume_profile == 'low':
            return False
            
        # Check trend alignment
        if (interaction['type'] == 'demand' and market_condition.trend == 'downtrend' or
            interaction['type'] == 'supply' and market_condition.trend == 'uptrend'):
            return False
            
        return True
        
    def _create_trade_signal(self, interaction: Dict, symbol: str) -> Dict:
        """Create a trade signal from a valid zone interaction."""
        zone = interaction['zone']
        current_price = interaction['price']
        
        if interaction['type'] == 'supply':
            entry_price = current_price
            stop_loss = zone['upper'] + (zone['upper'] - zone['lower']) * 0.1
            take_profit = entry_price - (stop_loss - entry_price) * self.parameters['risk_reward_ratio']
            side = 'sell'
        else:
            entry_price = current_price
            stop_loss = zone['lower'] - (zone['upper'] - zone['lower']) * 0.1
            take_profit = entry_price + (entry_price - stop_loss) * self.parameters['risk_reward_ratio']
            side = 'buy'
            
        return {
            'symbol': symbol,
            'side': side,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'reason': f"{interaction['type']} zone interaction (strength: {zone['strength']})"
        }
        
    def _clean_expired_zones(self, df: pd.DataFrame):
        """Remove expired or invalidated zones."""
        current_time = df.index[-1]
        
        for zone_type in ['supply', 'demand']:
            self.zones[zone_type] = [
                zone for zone in self.zones[zone_type]
                if (current_time - zone['created_at']).total_seconds() / 3600 < self.parameters['zone_expiry']
            ]
            
    def _get_market_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get market data for analysis."""
        # TODO: Implement market data retrieval
        return None 