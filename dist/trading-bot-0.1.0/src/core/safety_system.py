from typing import Dict, Optional
from datetime import datetime, timedelta
import logging
from .mode_manager import ModeManager, TradingMode
from ..utils.config_manager import ConfigManager
from PyQt6.QtWidgets import QMessageBox, QWidget

logger = logging.getLogger(__name__)

class SafetySystem:
    def __init__(self, mode_manager: ModeManager, parent_widget: Optional[QWidget] = None):
        self.mode_manager = mode_manager
        self.parent = parent_widget
        self.config = ConfigManager()
        
        # Load safety settings
        self.safety_settings = {
            'max_daily_trades': 10,
            'max_daily_loss': 0.02,  # 2% of account
            'max_position_size': 0.05,  # 5% of account
            'required_demo_trades': 100,
            'min_demo_success_rate': 0.55,  # 55% win rate
            'max_concurrent_trades': 3
        }
        self._load_safety_settings()
        
        # Initialize tracking
        self.daily_stats = {
            'trades': 0,
            'losses': 0.0,
            'start_balance': 0.0
        }
        self.reset_daily_stats()
        
    def _load_safety_settings(self):
        """Load saved safety settings."""
        saved_settings = self.config.get_setting('safety_settings')
        if saved_settings:
            self.safety_settings.update(saved_settings)
            
    def reset_daily_stats(self):
        """Reset daily trading statistics."""
        self.daily_stats = {
            'trades': 0,
            'losses': 0.0,
            'start_balance': self.config.get_setting('account_balance', 0.0),
            'last_reset': datetime.now()
        }
        
    def can_place_trade(self, trade_signal: Dict) -> bool:
        """Check if it's safe to place a new trade."""
        if self.mode_manager.is_live():
            checks = [
                self._check_daily_limits(),
                self._check_position_size(trade_signal),
                self._check_demo_requirements(),
                self._check_concurrent_trades()
            ]
            return all(checks)
        return True
        
    def _check_daily_limits(self) -> bool:
        """Check if daily trading limits have been reached."""
        # Reset stats if it's a new day
        if (datetime.now() - self.daily_stats['last_reset']) > timedelta(days=1):
            self.reset_daily_stats()
            
        # Check number of trades
        if self.daily_stats['trades'] >= self.safety_settings['max_daily_trades']:
            self._show_warning("Daily Trade Limit",
                             "Maximum number of daily trades reached.")
            return False
            
        # Check daily losses
        current_balance = self.config.get_setting('account_balance', 0.0)
        daily_loss_pct = (self.daily_stats['start_balance'] - current_balance) / self.daily_stats['start_balance']
        
        if daily_loss_pct >= self.safety_settings['max_daily_loss']:
            self._show_warning("Daily Loss Limit",
                             "Maximum daily loss limit reached. Trading suspended.")
            return False
            
        return True
        
    def _check_position_size(self, trade_signal: Dict) -> bool:
        """Verify position size is within limits."""
        account_balance = self.config.get_setting('account_balance', 0.0)
        position_size = trade_signal.get('size', 0) * trade_signal.get('entry_price', 0)
        
        if position_size / account_balance > self.safety_settings['max_position_size']:
            self._show_warning("Position Size Limit",
                             "Trade size exceeds maximum allowed position size.")
            return False
            
        return True
        
    def _check_demo_requirements(self) -> bool:
        """Verify sufficient demo trading experience."""
        demo_stats = self.config.get_setting('demo_trading_stats', {})
        
        if demo_stats.get('total_trades', 0) < self.safety_settings['required_demo_trades']:
            self._show_warning("Insufficient Demo Trading",
                             "More demo trading required before live trading.")
            return False
            
        win_rate = demo_stats.get('win_rate', 0)
        if win_rate < self.safety_settings['min_demo_success_rate']:
            self._show_warning("Low Success Rate",
                             "Demo trading success rate below required minimum.")
            return False
            
        return True
        
    def _check_concurrent_trades(self) -> bool:
        """Check if maximum number of concurrent trades is reached."""
        current_trades = len(self.config.get_setting('open_positions', []))
        
        if current_trades >= self.safety_settings['max_concurrent_trades']:
            self._show_warning("Concurrent Trades Limit",
                             "Maximum number of concurrent trades reached.")
            return False
            
        return True
        
    def record_trade(self, trade_result: Dict):
        """Record trade result for safety monitoring."""
        self.daily_stats['trades'] += 1
        
        if trade_result['pnl'] < 0:
            self.daily_stats['losses'] += abs(trade_result['pnl'])
            
        # Update config with latest stats
        self.config.set_setting('last_trade_stats', {
            'timestamp': datetime.now().isoformat(),
            'daily_stats': self.daily_stats
        })
        
    def _show_warning(self, title: str, message: str):
        """Show warning message to user."""
        if self.parent:
            QMessageBox.warning(self.parent, title, message)
        logger.warning(f"{title}: {message}") 