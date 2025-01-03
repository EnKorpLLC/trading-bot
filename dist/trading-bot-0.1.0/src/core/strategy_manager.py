from typing import Dict, List, Optional
import logging
from datetime import datetime
import pandas as pd
from dataclasses import dataclass

from .market_analyzer import MarketCondition
from ..strategies.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

@dataclass
class StrategyPerformance:
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_profit: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    avg_profit_per_trade: float = 0.0
    last_updated: datetime = datetime.now()

class StrategyManager:
    def __init__(self):
        self.strategies: Dict[str, BaseStrategy] = {}
        self.performance_metrics: Dict[str, StrategyPerformance] = {}
        self.market_conditions: Dict[str, List[str]] = {
            'trending': ['breakout', 'fvg', 'topdown'],
            'ranging': ['consolidation', 'scalping', 'opposition'],
            'volatile': ['supply_demand', 'liquidity', 'fibonacci'],
            'low_volatility': ['tetris', 'consolidation']
        }
        
    def add_strategy(self, strategy: BaseStrategy) -> None:
        """Add a new strategy to the manager."""
        self.strategies[strategy.name] = strategy
        self.performance_metrics[strategy.name] = StrategyPerformance()
        logger.info(f"Added strategy: {strategy.name}")
        
    def select_strategies(self, market_condition: MarketCondition) -> List[BaseStrategy]:
        """Select appropriate strategies based on market condition."""
        selected_strategies = []
        
        # Determine market state
        if market_condition.volatility > 1.5:
            state = 'volatile'
        elif market_condition.volatility < 0.5:
            state = 'low_volatility'
        elif market_condition.trend in ['uptrend', 'downtrend']:
            state = 'trending'
        else:
            state = 'ranging'
            
        # Get suitable strategies for this market state
        suitable_strategy_names = self.market_conditions[state]
        
        # Filter active strategies that match current conditions
        for name in suitable_strategy_names:
            if name in self.strategies and self.strategies[name].is_active:
                selected_strategies.append(self.strategies[name])
                
        logger.info(f"Selected strategies for {state} market: {[s.name for s in selected_strategies]}")
        return selected_strategies
        
    def update_performance(self, strategy_name: str, trade_result: Dict) -> None:
        """Update performance metrics for a strategy."""
        if strategy_name not in self.performance_metrics:
            logger.warning(f"No performance metrics found for strategy: {strategy_name}")
            return
            
        metrics = self.performance_metrics[strategy_name]
        metrics.total_trades += 1
        
        profit = trade_result.get('profit', 0)
        metrics.total_profit += profit
        
        if profit > 0:
            metrics.winning_trades += 1
        elif profit < 0:
            metrics.losing_trades += 1
            
        # Update win rate
        metrics.win_rate = metrics.winning_trades / metrics.total_trades if metrics.total_trades > 0 else 0
        
        # Update average profit per trade
        metrics.avg_profit_per_trade = metrics.total_profit / metrics.total_trades if metrics.total_trades > 0 else 0
        
        # Update timestamp
        metrics.last_updated = datetime.now()
        
        logger.info(f"Updated performance metrics for {strategy_name}: Win Rate={metrics.win_rate:.2%}")
        
    def get_performance_report(self) -> Dict[str, Dict]:
        """Generate performance report for all strategies."""
        report = {}
        for name, metrics in self.performance_metrics.items():
            report[name] = {
                'win_rate': metrics.win_rate,
                'total_trades': metrics.total_trades,
                'total_profit': metrics.total_profit,
                'avg_profit': metrics.avg_profit_per_trade,
                'last_updated': metrics.last_updated.isoformat()
            }
        return report 