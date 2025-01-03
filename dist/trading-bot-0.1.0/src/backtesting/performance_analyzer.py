from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    avg_trade: float
    avg_win: float
    avg_loss: float
    max_consecutive_losses: int
    recovery_factor: float
    risk_reward_ratio: float
    expectancy: float
    trades_per_month: float

class PerformanceAnalyzer:
    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate
        
    def analyze(self, equity_curve: pd.DataFrame, trades: pd.DataFrame) -> Dict:
        """Analyze backtest performance and generate metrics."""
        try:
            # Calculate basic metrics
            metrics = PerformanceMetrics(
                total_return=self._calculate_total_return(equity_curve),
                sharpe_ratio=self._calculate_sharpe_ratio(equity_curve),
                max_drawdown=self._calculate_max_drawdown(equity_curve),
                win_rate=self._calculate_win_rate(trades),
                profit_factor=self._calculate_profit_factor(trades),
                avg_trade=trades['pnl'].mean(),
                avg_win=trades[trades['pnl'] > 0]['pnl'].mean(),
                avg_loss=abs(trades[trades['pnl'] < 0]['pnl'].mean()),
                max_consecutive_losses=self._calculate_max_consecutive_losses(trades),
                recovery_factor=self._calculate_recovery_factor(equity_curve),
                risk_reward_ratio=self._calculate_risk_reward_ratio(trades),
                expectancy=self._calculate_expectancy(trades),
                trades_per_month=self._calculate_trades_per_month(trades)
            )
            
            # Generate detailed analysis
            analysis = {
                'summary': self._create_summary(metrics),
                'monthly_returns': self._calculate_monthly_returns(equity_curve),
                'drawdown_periods': self._analyze_drawdowns(equity_curve),
                'trade_analysis': self._analyze_trades(trades),
                'risk_metrics': self._calculate_risk_metrics(equity_curve, trades)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing performance: {str(e)}")
            raise
            
    def _create_summary(self, metrics: PerformanceMetrics) -> Dict:
        """Create performance summary."""
        return {
            'total_return_pct': metrics.total_return * 100,
            'sharpe_ratio': metrics.sharpe_ratio,
            'max_drawdown_pct': metrics.max_drawdown * 100,
            'win_rate_pct': metrics.win_rate * 100,
            'profit_factor': metrics.profit_factor,
            'avg_trade': metrics.avg_trade,
            'risk_reward_ratio': metrics.risk_reward_ratio,
            'expectancy': metrics.expectancy,
            'recovery_factor': metrics.recovery_factor,
            'trades_per_month': metrics.trades_per_month
        }
        
    def _calculate_sharpe_ratio(self, equity_curve: pd.DataFrame) -> float:
        """Calculate Sharpe ratio."""
        returns = equity_curve['equity'].pct_change().dropna()
        excess_returns = returns - self.risk_free_rate / 252  # Daily risk-free rate
        return np.sqrt(252) * excess_returns.mean() / excess_returns.std()
        
    def _calculate_max_drawdown(self, equity_curve: pd.DataFrame) -> float:
        """Calculate maximum drawdown and duration."""
        rolling_max = equity_curve['equity'].expanding().max()
        drawdowns = equity_curve['equity'] / rolling_max - 1
        return abs(drawdowns.min())
        
    def _analyze_drawdowns(self, equity_curve: pd.DataFrame) -> List[Dict]:
        """Analyze drawdown periods."""
        equity = equity_curve['equity']
        drawdown_periods = []
        peak = equity.iloc[0]
        peak_idx = 0
        
        for idx, value in equity.items():
            if value > peak:
                # New peak
                if idx > peak_idx + 1:  # If there was a drawdown
                    drawdown_periods.append({
                        'start_date': equity_curve.index[peak_idx],
                        'end_date': idx,
                        'depth': (lowest_value - peak) / peak,
                        'length': (idx - equity_curve.index[peak_idx]).days,
                        'recovery': (value - lowest_value) / lowest_value
                    })
                peak = value
                peak_idx = equity_curve.index.get_loc(idx)
            else:
                # In drawdown
                lowest_value = min(value, equity[peak_idx:equity_curve.index.get_loc(idx)+1].min())
                
        return drawdown_periods
        
    def _calculate_monthly_returns(self, equity_curve: pd.DataFrame) -> pd.Series:
        """Calculate monthly returns."""
        return equity_curve['equity'].resample('M').last().pct_change()
        
    def _analyze_trades(self, trades: pd.DataFrame) -> Dict:
        """Analyze trade characteristics."""
        return {
            'avg_duration': trades['duration'].mean(),
            'win_rate_by_day': self._calculate_win_rate_by_day(trades),
            'profit_by_hour': self._calculate_profit_by_hour(trades),
            'consecutive_wins': self._calculate_consecutive_stats(trades, True),
            'consecutive_losses': self._calculate_consecutive_stats(trades, False),
            'profit_factor_by_month': self._calculate_profit_factor_by_month(trades)
        }
        
    def _calculate_risk_metrics(self, equity_curve: pd.DataFrame, trades: pd.DataFrame) -> Dict:
        """Calculate risk-related metrics."""
        returns = equity_curve['equity'].pct_change().dropna()
        
        return {
            'value_at_risk': self._calculate_var(returns),
            'conditional_var': self._calculate_cvar(returns),
            'beta': self._calculate_beta(returns),
            'alpha': self._calculate_alpha(returns),
            'sortino_ratio': self._calculate_sortino_ratio(returns),
            'calmar_ratio': self._calculate_calmar_ratio(equity_curve),
            'tail_ratio': self._calculate_tail_ratio(returns)
        }
        
    def _calculate_var(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """Calculate Value at Risk."""
        return abs(np.percentile(returns, (1 - confidence) * 100))
        
    def _calculate_cvar(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """Calculate Conditional Value at Risk (Expected Shortfall)."""
        var = self._calculate_var(returns, confidence)
        return abs(returns[returns <= -var].mean())
        
    def _calculate_sortino_ratio(self, returns: pd.Series) -> float:
        """Calculate Sortino ratio."""
        negative_returns = returns[returns < 0]
        downside_std = np.sqrt(np.mean(negative_returns ** 2))
        excess_return = returns.mean() - self.risk_free_rate / 252
        return np.sqrt(252) * excess_return / downside_std if downside_std != 0 else 0
        
    def _calculate_calmar_ratio(self, equity_curve: pd.DataFrame) -> float:
        """Calculate Calmar ratio."""
        max_dd = self._calculate_max_drawdown(equity_curve)
        annual_return = self._calculate_total_return(equity_curve) * 252 / len(equity_curve)
        return annual_return / max_dd if max_dd != 0 else 0
        
    def _calculate_tail_ratio(self, returns: pd.Series) -> float:
        """Calculate tail ratio."""
        tail_size = int(len(returns) * 0.01)  # 1% tail
        left_tail = abs(returns.nsmallest(tail_size).mean())
        right_tail = returns.nlargest(tail_size).mean()
        return right_tail / left_tail if left_tail != 0 else float('inf')
        
    def _calculate_win_rate_by_day(self, trades: pd.DataFrame) -> pd.Series:
        """Calculate win rate by day of week."""
        trades['day'] = trades['entry_time'].dt.day_name()
        return trades.groupby('day')['pnl'].apply(lambda x: (x > 0).mean())
        
    def _calculate_profit_by_hour(self, trades: pd.DataFrame) -> pd.Series:
        """Calculate average profit by hour."""
        trades['hour'] = trades['entry_time'].dt.hour
        return trades.groupby('hour')['pnl'].mean()
        
    def _calculate_consecutive_stats(self, trades: pd.DataFrame, wins: bool) -> Dict:
        """Calculate statistics about consecutive wins or losses."""
        streak = 0
        max_streak = 0
        streaks = []
        
        for pnl in trades['pnl']:
            if (pnl > 0) == wins:
                streak += 1
            else:
                if streak > 0:
                    streaks.append(streak)
                    max_streak = max(max_streak, streak)
                streak = 0
                
        return {
            'max_streak': max_streak,
            'avg_streak': np.mean(streaks) if streaks else 0,
            'streak_distribution': pd.Series(streaks).value_counts().sort_index()
        } 