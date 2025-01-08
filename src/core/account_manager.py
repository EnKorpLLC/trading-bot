from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class AccountManager:
    """Manages account tracking, margin calculations, and performance metrics."""
    
    def __init__(self):
        """Initialize account manager."""
        self.account_info = {}
        self.positions = []
        self.trade_history = []
        self.margin_used = 0.0
        self.available_margin = 0.0
        self.equity = 0.0
        self.balance = 0.0
        self.unrealized_pnl = 0.0
        self.realized_pnl = 0.0
        self.margin_level = 0.0
        
        # Performance metrics
        self.metrics = {
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "total_trades": 0,
            "profitable_trades": 0,
            "losing_trades": 0
        }
        
        # Risk limits
        self.max_position_size = 0.0
        self.max_total_exposure = 0.0
        self.min_margin_level = 50.0  # 50% minimum margin level
        
    def update_account_info(self, info: Dict):
        """Update account information and recalculate metrics."""
        self.account_info = info
        self.balance = float(info.get("balance", 0))
        self.equity = float(info.get("equity", 0))
        self.margin_used = float(info.get("margin_used", 0))
        self.available_margin = float(info.get("available_margin", 0))
        
        # Update risk limits based on account size
        self.max_position_size = self.equity * 0.02  # 2% max position size
        self.max_total_exposure = self.equity * 0.06  # 6% max total exposure
        
        # Calculate margin level
        if self.margin_used > 0:
            self.margin_level = (self.equity / self.margin_used) * 100
        else:
            self.margin_level = 100.0
            
        logger.info(f"Account info updated - Balance: {self.balance}, Equity: {self.equity}")
        
    def update_positions(self, positions: List[Dict]):
        """Update current positions and calculate unrealized P&L."""
        self.positions = positions
        total_unrealized = 0.0
        total_exposure = 0.0
        
        for position in positions:
            size = float(position.get("size", 0))
            entry_price = float(position.get("entry_price", 0))
            current_price = float(position.get("current_price", 0))
            
            # Calculate position P&L
            if position.get("type") == "long":
                unrealized = (current_price - entry_price) * size
            else:
                unrealized = (entry_price - current_price) * size
                
            total_unrealized += unrealized
            total_exposure += abs(size * current_price)
        
        self.unrealized_pnl = total_unrealized
        
        # Check exposure limits
        if total_exposure > self.max_total_exposure:
            logger.warning(f"Total exposure ({total_exposure}) exceeds limit ({self.max_total_exposure})")
    
    def add_trade(self, trade: Dict):
        """Add a completed trade to history and update metrics."""
        self.trade_history.append(trade)
        self.realized_pnl += float(trade.get("profit", 0))
        self._update_performance_metrics()
        
        logger.info(f"Trade recorded - Profit: {trade.get('profit')}, "
                   f"Total realized P&L: {self.realized_pnl}")
        
    def _update_performance_metrics(self):
        """Update performance metrics based on trade history."""
        if not self.trade_history:
            return
            
        # Basic metrics
        profits = [t["profit"] for t in self.trade_history if t["profit"] > 0]
        losses = [abs(t["profit"]) for t in self.trade_history if t["profit"] < 0]
        
        self.metrics["total_trades"] = len(self.trade_history)
        self.metrics["profitable_trades"] = len(profits)
        self.metrics["losing_trades"] = len(losses)
        
        if self.metrics["total_trades"] > 0:
            self.metrics["win_rate"] = (self.metrics["profitable_trades"] / 
                                      self.metrics["total_trades"]) * 100
                                      
        if profits:
            self.metrics["avg_win"] = sum(profits) / len(profits)
        if losses:
            self.metrics["avg_loss"] = sum(losses) / len(losses)
            
        if losses and sum(losses) > 0:
            self.metrics["profit_factor"] = sum(profits) / sum(losses)
            
        # Calculate drawdown
        balance_curve = self._calculate_balance_curve()
        self.metrics["max_drawdown"] = self._calculate_max_drawdown(balance_curve)
        
        # Calculate Sharpe ratio (if enough data)
        if len(balance_curve) > 30:  # Need at least 30 days of data
            self.metrics["sharpe_ratio"] = self._calculate_sharpe_ratio(balance_curve)
            
        logger.info(f"Performance metrics updated - Win rate: {self.metrics['win_rate']:.2f}%, "
                   f"Profit factor: {self.metrics['profit_factor']:.2f}")
    
    def _calculate_balance_curve(self) -> pd.Series:
        """Calculate daily balance curve from trade history."""
        if not self.trade_history:
            return pd.Series()
            
        # Convert trade history to DataFrame
        df = pd.DataFrame(self.trade_history)
        df["close_time"] = pd.to_datetime(df["close_time"])
        df = df.set_index("close_time")
        df = df.sort_index()
        
        # Resample to daily and calculate cumulative P&L
        daily_pnl = df["profit"].resample("D").sum()
        balance_curve = daily_pnl.cumsum() + self.balance
        
        return balance_curve
    
    def _calculate_max_drawdown(self, balance_curve: pd.Series) -> float:
        """Calculate maximum drawdown from balance curve."""
        if balance_curve.empty:
            return 0.0
            
        rolling_max = balance_curve.expanding().max()
        drawdowns = (balance_curve - rolling_max) / rolling_max * 100
        
        return abs(drawdowns.min())
    
    def _calculate_sharpe_ratio(self, balance_curve: pd.Series) -> float:
        """Calculate Sharpe ratio from balance curve."""
        if balance_curve.empty:
            return 0.0
            
        # Calculate daily returns
        daily_returns = balance_curve.pct_change().dropna()
        
        if len(daily_returns) < 2:
            return 0.0
            
        # Calculate annualized Sharpe ratio
        risk_free_rate = 0.02  # 2% annual risk-free rate
        daily_rf = (1 + risk_free_rate) ** (1/252) - 1
        
        excess_returns = daily_returns - daily_rf
        annualized_sharpe = np.sqrt(252) * (excess_returns.mean() / excess_returns.std())
        
        return annualized_sharpe
    
    def check_margin_requirements(self, order: Dict) -> bool:
        """Check if an order meets margin requirements."""
        required_margin = self._calculate_required_margin(order)
        
        # Check if we have enough available margin
        if required_margin > self.available_margin:
            logger.warning(f"Insufficient margin - Required: {required_margin}, "
                         f"Available: {self.available_margin}")
            return False
            
        # Check if this would put us below minimum margin level
        potential_margin_used = self.margin_used + required_margin
        if potential_margin_used > 0:
            potential_margin_level = (self.equity / potential_margin_used) * 100
            if potential_margin_level < self.min_margin_level:
                logger.warning(f"Order would put margin level below minimum - "
                             f"Potential level: {potential_margin_level:.2f}%")
                return False
                
        return True
    
    def _calculate_required_margin(self, order: Dict) -> float:
        """Calculate required margin for an order."""
        # This is a simplified calculation - adjust based on broker's requirements
        price = float(order.get("price", 0))
        size = float(order.get("size", 0))
        leverage = float(self.account_info.get("leverage", 100))
        
        return (price * size) / leverage
    
    def get_account_summary(self) -> Dict:
        """Get summary of account status and performance."""
        return {
            "balance": self.balance,
            "equity": self.equity,
            "margin_used": self.margin_used,
            "available_margin": self.available_margin,
            "margin_level": self.margin_level,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl,
            "total_pnl": self.unrealized_pnl + self.realized_pnl,
            "open_positions": len(self.positions),
            "performance_metrics": self.metrics
        }
        
    def get_trade_history(self) -> List[Dict]:
        """Get the trade history."""
        return self.trade_history 