from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime
from ..strategies.base_strategy import BaseStrategy
from .market_simulator import MarketSimulator
from .historical_data_manager import HistoricalDataManager
import logging

logger = logging.getLogger(__name__)

class BacktestManager:
    def __init__(self):
        self.data_manager = HistoricalDataManager()
        self.market_simulator = MarketSimulator()
        self.results: Dict = {}
        self.current_test: Optional[Dict] = None
        
    def run_backtest(self, 
                    strategy: BaseStrategy,
                    symbols: List[str],
                    start_date: datetime,
                    end_date: datetime,
                    timeframe: str = '1h',
                    initial_capital: float = 10000.0,
                    **parameters) -> Dict:
        """Run a complete backtest for a strategy."""
        try:
            # Initialize test
            self.current_test = {
                'strategy': strategy.__class__.__name__,
                'symbols': symbols,
                'timeframe': timeframe,
                'start_date': start_date,
                'end_date': end_date,
                'initial_capital': initial_capital,
                'parameters': parameters,
                'trades': [],
                'equity_curve': []
            }
            
            # Load and validate data
            self._prepare_data(symbols, start_date, end_date, timeframe)
            
            # Update strategy parameters if provided
            if parameters:
                strategy.parameters.update(parameters)
            
            # Run simulation
            self._run_simulation(strategy)
            
            # Calculate and store results
            results = self._calculate_results()
            self.results[strategy.__class__.__name__] = results
            
            return results
            
        except Exception as e:
            logger.error(f"Backtest failed: {str(e)}")
            raise
            
    def _prepare_data(self, symbols: List[str], start_date: datetime, 
                     end_date: datetime, timeframe: str):
        """Prepare data for backtesting."""
        for symbol in symbols:
            self.data_manager.load_data(symbol, timeframe, start_date, end_date)
            
        if not self.data_manager.validate_data():
            raise ValueError("Data validation failed")
            
    def _run_simulation(self, strategy: BaseStrategy):
        """Execute the backtest simulation."""
        self.market_simulator.reset(
            self.data_manager,
            self.current_test['initial_capital']
        )
        
        while self.market_simulator.next():
            # Get current market state
            market_data = self.market_simulator.get_market_data()
            
            # Generate signals
            analysis = strategy.analyze_market(market_data)
            signals = strategy.generate_signals(analysis)
            
            # Process signals
            if signals:
                for signal in signals:
                    self.market_simulator.process_signal(signal)
                    
            # Update positions
            self.market_simulator.update_positions()
            
            # Record state
            self._record_state()
            
    def _record_state(self):
        """Record current simulation state."""
        state = self.market_simulator.get_current_state()
        self.current_test['equity_curve'].append({
            'timestamp': state['timestamp'],
            'equity': state['equity'],
            'open_positions': len(state['positions']),
            'daily_pnl': state['daily_pnl']
        })
        
    def _calculate_results(self) -> Dict:
        """Calculate backtest performance metrics."""
        equity_curve = pd.DataFrame(self.current_test['equity_curve'])
        trades = pd.DataFrame(self.market_simulator.get_closed_trades())
        
        # Calculate key metrics
        total_trades = len(trades)
        winning_trades = len(trades[trades['pnl'] > 0])
        
        results = {
            'summary': {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'win_rate': winning_trades / total_trades if total_trades > 0 else 0,
                'profit_factor': self._calculate_profit_factor(trades),
                'sharpe_ratio': self._calculate_sharpe_ratio(equity_curve),
                'max_drawdown': self._calculate_max_drawdown(equity_curve),
                'total_return': self._calculate_total_return(equity_curve),
                'avg_trade_duration': trades['duration'].mean() if len(trades) > 0 else 0
            },
            'equity_curve': equity_curve,
            'trades': trades,
            'parameters': self.current_test['parameters']
        }
        
        return results
        
    def _calculate_sharpe_ratio(self, equity_curve: pd.DataFrame) -> float:
        """Calculate Sharpe ratio."""
        if len(equity_curve) < 2:
            return 0.0
            
        returns = equity_curve['equity'].pct_change().dropna()
        if len(returns) == 0:
            return 0.0
            
        return np.sqrt(252) * (returns.mean() / returns.std())
        
    def _calculate_max_drawdown(self, equity_curve: pd.DataFrame) -> float:
        """Calculate maximum drawdown."""
        if len(equity_curve) < 2:
            return 0.0
            
        peak = equity_curve['equity'].expanding(min_periods=1).max()
        drawdown = (equity_curve['equity'] - peak) / peak
        return abs(drawdown.min())
        
    def _calculate_profit_factor(self, trades: pd.DataFrame) -> float:
        """Calculate profit factor."""
        if len(trades) == 0:
            return 0.0
            
        gross_profit = trades[trades['pnl'] > 0]['pnl'].sum()
        gross_loss = abs(trades[trades['pnl'] < 0]['pnl'].sum())
        
        return gross_profit / gross_loss if gross_loss != 0 else float('inf')
        
    def _calculate_total_return(self, equity_curve: pd.DataFrame) -> float:
        """Calculate total return."""
        if len(equity_curve) < 2:
            return 0.0
            
        initial = equity_curve['equity'].iloc[0]
        final = equity_curve['equity'].iloc[-1]
        return (final - initial) / initial
        
    def optimize_parameters(self, 
                          strategy: BaseStrategy,
                          param_grid: Dict,
                          symbols: List[str],
                          start_date: datetime,
                          end_date: datetime,
                          timeframe: str = '1h',
                          optimization_metric: str = 'sharpe_ratio') -> Dict:
        """Optimize strategy parameters using grid search."""
        best_result = None
        best_params = None
        best_metric = float('-inf')
        
        # Generate parameter combinations
        param_combinations = self._generate_param_combinations(param_grid)
        
        for params in param_combinations:
            # Run backtest with current parameters
            result = self.run_backtest(
                strategy=strategy,
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                timeframe=timeframe,
                **params
            )
            
            # Check if current result is better
            current_metric = result['summary'][optimization_metric]
            if current_metric > best_metric:
                best_metric = current_metric
                best_params = params
                best_result = result
                
        return {
            'best_parameters': best_params,
            'best_result': best_result,
            'optimization_metric': optimization_metric,
            'metric_value': best_metric
        }
        
    def _generate_param_combinations(self, param_grid: Dict) -> List[Dict]:
        """Generate all possible parameter combinations."""
        import itertools
        
        keys = param_grid.keys()
        values = param_grid.values()
        combinations = list(itertools.product(*values))
        
        return [dict(zip(keys, combo)) for combo in combinations] 