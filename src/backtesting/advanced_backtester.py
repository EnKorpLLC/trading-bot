import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
from datetime import datetime

@dataclass
class BacktestResult:
    returns: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    trades: pd.DataFrame
    equity_curve: List[float]

class AdvancedBacktester:
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset the backtester state"""
        self.positions = []
        self.trades = []
        self.equity_curve = []
        self.current_position = None
    
    def calculate_metrics(self, trades_df: pd.DataFrame, equity_curve: List[float]) -> BacktestResult:
        """Calculate performance metrics from trades"""
        if not trades_df.empty:
            # Calculate returns
            total_return = (equity_curve[-1] / equity_curve[0]) - 1
            
            # Calculate Sharpe ratio (assuming risk-free rate of 0.02)
            returns_series = pd.Series(equity_curve).pct_change().dropna()
            sharpe_ratio = (returns_series.mean() - 0.02/252) / (returns_series.std() * np.sqrt(252))
            
            # Calculate maximum drawdown
            peak = pd.Series(equity_curve).expanding(min_periods=1).max()
            drawdown = (pd.Series(equity_curve) - peak) / peak
            max_drawdown = drawdown.min()
            
            # Calculate win rate
            winning_trades = trades_df[trades_df['profit'] > 0]
            win_rate = len(winning_trades) / len(trades_df) if len(trades_df) > 0 else 0
            
            return BacktestResult(
                returns=total_return,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                trades=trades_df,
                equity_curve=equity_curve
            )
        else:
            return BacktestResult(
                returns=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                trades=pd.DataFrame(),
                equity_curve=[1.0]
            )
    
    def run_backtest(self, data: pd.DataFrame, strategy_params: Dict[str, Any]) -> BacktestResult:
        """Run backtest with given strategy parameters"""
        self.reset()
        
        # Initial capital
        equity = 100000
        self.equity_curve.append(equity)
        
        trades_data = []
        position = None
        entry_price = 0
        entry_time = None
        
        for i in range(1, len(data)):
            current_price = data['close'].iloc[i]
            current_time = data.index[i]
            
            # Simple moving average strategy for demonstration
            short_ma = data['close'].rolling(
                window=int(strategy_params.get('short_window', 20))
            ).mean().iloc[i]
            
            long_ma = data['close'].rolling(
                window=int(strategy_params.get('long_window', 50))
            ).mean().iloc[i]
            
            # Trading logic
            if position is None:  # No position
                if short_ma > long_ma:  # Bullish crossover
                    position = 'long'
                    entry_price = current_price
                    entry_time = current_time
            
            elif position == 'long':  # Long position
                if short_ma < long_ma:  # Bearish crossover
                    # Close long position
                    profit = (current_price - entry_price) / entry_price
                    equity *= (1 + profit)
                    
                    trades_data.append({
                        'entry_time': entry_time,
                        'exit_time': current_time,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'position': position,
                        'profit': profit
                    })
                    
                    position = None
            
            self.equity_curve.append(equity)
        
        # Close any open position at the end
        if position is not None:
            profit = (current_price - entry_price) / entry_price
            equity *= (1 + profit)
            
            trades_data.append({
                'entry_time': entry_time,
                'exit_time': current_time,
                'entry_price': entry_price,
                'exit_price': current_price,
                'position': position,
                'profit': profit
            })
            
            self.equity_curve.append(equity)
        
        trades_df = pd.DataFrame(trades_data)
        return self.calculate_metrics(trades_df, self.equity_curve)
    
    def plot_results(self, result: BacktestResult):
        """Plot equity curve and trade points"""
        plt.figure(figsize=(12, 6))
        
        # Plot equity curve
        plt.plot(result.equity_curve, label='Equity Curve')
        
        # Add trade points
        for _, trade in result.trades.iterrows():
            if trade['profit'] > 0:
                color = 'g'
            else:
                color = 'r'
            
            plt.scatter(trade['entry_time'], result.equity_curve[trade['entry_time']], 
                       color=color, marker='^')
            plt.scatter(trade['exit_time'], result.equity_curve[trade['exit_time']], 
                       color=color, marker='v')
        
        plt.title('Backtest Results')
        plt.xlabel('Time')
        plt.ylabel('Equity')
        plt.legend()
        plt.grid(True)
        plt.show() 