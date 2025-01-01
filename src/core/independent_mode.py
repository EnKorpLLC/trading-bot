from typing import Dict, Optional
from datetime import datetime
import logging
from decimal import Decimal
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QTimer
import threading
from .mode_manager import ModeManager
from .safety_system import SafetySystem
from ..utils.config_manager import ConfigManager
from ..utils.notification_manager import NotificationManager
from ..utils.sound_manager import SoundManager

logger = logging.getLogger(__name__)

class IndependentMode:
    def __init__(self, 
                 trading_engine,
                 mode_manager: ModeManager,
                 safety_system: SafetySystem,
                 parent_widget=None):
        self.trading_engine = trading_engine
        self.mode_manager = mode_manager
        self.safety_system = safety_system
        self.parent = parent_widget
        self.config = ConfigManager()
        self.notification_manager = NotificationManager()
        self.sound_manager = SoundManager()
        
        # Independent mode settings
        self.is_active = False
        self.limits = {
            'max_loss': 0.0,  # Maximum allowed loss
            'take_profit': 0.0,  # Profit target
            'max_drawdown': 0.0,  # Maximum drawdown allowed
            'daily_loss_limit': 0.0,  # Daily loss limit
            'position_limit': 0  # Maximum number of positions
        }
        
        # Performance tracking
        self.initial_balance = 0.0
        self.current_balance = 0.0
        self.peak_balance = 0.0
        self.daily_pnl = 0.0
        
        # Monitoring
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._monitor_performance)
        self.monitor_interval = 5000  # 5 seconds
        
    def start(self, limits: Dict[str, float]) -> bool:
        """Start independent trading mode with specified limits."""
        try:
            if not self._validate_limits(limits):
                return False
                
            if not self._confirm_start():
                return False
                
            # Initialize tracking
            self.limits.update(limits)
            self.initial_balance = self.trading_engine.get_account_balance()
            self.current_balance = self.initial_balance
            self.peak_balance = self.initial_balance
            self.daily_pnl = 0.0
            
            # Start monitoring
            self.is_active = True
            self.monitor_timer.start(self.monitor_interval)
            
            # Log and notify
            logger.info("Independent trading mode activated")
            self.notification_manager.send_notification(
                "Independent Mode Started",
                f"Trading bot is now operating independently with:\n"
                f"Max Loss: ${self.limits['max_loss']}\n"
                f"Take Profit: ${self.limits['take_profit']}"
            )
            
            # Start trading thread
            self.trading_thread = threading.Thread(target=self._run_trading_loop)
            self.trading_thread.daemon = True
            self.trading_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting independent mode: {str(e)}")
            return False
            
    def stop(self, reason: str = "User requested stop"):
        """Stop independent trading mode."""
        try:
            if not self.is_active:
                return
                
            self.is_active = False
            self.monitor_timer.stop()
            
            # Close all positions
            self._close_all_positions()
            
            # Calculate final performance
            final_pnl = self.current_balance - self.initial_balance
            
            # Log and notify
            logger.info(f"Independent mode stopped: {reason}")
            self.notification_manager.send_notification(
                "Independent Mode Stopped",
                f"Reason: {reason}\n"
                f"Final P&L: ${final_pnl:.2f}"
            )
            
            # Show summary dialog
            self._show_summary_dialog(reason, final_pnl)
            
        except Exception as e:
            logger.error(f"Error stopping independent mode: {str(e)}")
            
    def _validate_limits(self, limits: Dict[str, float]) -> bool:
        """Validate trading limits."""
        try:
            account_balance = self.trading_engine.get_account_balance()
            
            # Check if limits are reasonable
            if limits['max_loss'] > account_balance * 0.5:
                self._show_error("Invalid Limits", 
                               "Maximum loss cannot exceed 50% of account balance")
                return False
                
            if limits['max_drawdown'] > limits['max_loss']:
                self._show_error("Invalid Limits",
                               "Maximum drawdown cannot exceed maximum loss limit")
                return False
                
            if limits['daily_loss_limit'] > limits['max_loss']:
                self._show_error("Invalid Limits",
                               "Daily loss limit cannot exceed maximum loss limit")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating limits: {str(e)}")
            return False
            
    def _monitor_performance(self):
        """Monitor trading performance and limits."""
        try:
            if not self.is_active:
                return
                
            # Update current balance
            self.current_balance = self.trading_engine.get_account_balance()
            self.peak_balance = max(self.peak_balance, self.current_balance)
            
            # Calculate metrics
            total_pnl = self.current_balance - self.initial_balance
            drawdown = (self.peak_balance - self.current_balance) / self.peak_balance
            
            # Check limits with sound alerts
            if total_pnl <= -self.limits['max_loss']:
                self.sound_manager.play_sound('loss_limit')
                self.stop("Maximum loss limit reached")
                return
                
            if total_pnl >= self.limits['take_profit']:
                self.sound_manager.play_sound('profit_target')
                self.stop("Take profit target reached")
                return
                
            if drawdown >= self.limits['max_drawdown']:
                self.stop("Maximum drawdown limit reached")
                return
                
            if self.daily_pnl <= -self.limits['daily_loss_limit']:
                self.stop("Daily loss limit reached")
                return
                
            # Update daily P&L at day change
            current_time = datetime.now()
            if current_time.hour == 0 and current_time.minute == 0:
                self.daily_pnl = 0.0
                
        except Exception as e:
            logger.error(f"Error in performance monitoring: {str(e)}")
            
    def _run_trading_loop(self):
        """Main trading loop for independent mode."""
        while self.is_active:
            try:
                # Get market analysis
                analysis = self.trading_engine.analyze_markets()
                
                # Generate signals
                signals = self.trading_engine.generate_signals(analysis)
                
                # Execute trades if they pass safety checks
                for signal in signals:
                    if self.safety_system.can_place_trade(signal):
                        self.trading_engine.execute_trade(signal)
                        
                # Sleep to prevent excessive CPU usage
                threading.Event().wait(1)  # 1 second delay
                
            except Exception as e:
                logger.error(f"Error in trading loop: {str(e)}")
                
    def _close_all_positions(self):
        """Close all open positions."""
        try:
            positions = self.trading_engine.get_open_positions()
            for position in positions:
                self.trading_engine.close_position(position['id'])
        except Exception as e:
            logger.error(f"Error closing positions: {str(e)}")
            
    def _confirm_start(self) -> bool:
        """Get user confirmation to start independent mode."""
        if not self.parent:
            return True
            
        msg = QMessageBox(self.parent)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Start Independent Mode")
        msg.setText("Are you sure you want to start independent trading mode?")
        msg.setInformativeText(
            f"The bot will trade autonomously with these limits:\n"
            f"Max Loss: ${self.limits['max_loss']}\n"
            f"Take Profit: ${self.limits['take_profit']}\n"
            f"Max Drawdown: {self.limits['max_drawdown']*100}%\n"
            f"Daily Loss Limit: ${self.limits['daily_loss_limit']}"
        )
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        
        return msg.exec() == QMessageBox.StandardButton.Yes
        
    def _show_summary_dialog(self, reason: str, final_pnl: float):
        """Show summary dialog when independent mode stops."""
        if not self.parent:
            return
            
        msg = QMessageBox(self.parent)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Independent Mode Summary")
        msg.setText(f"Independent trading mode stopped\nReason: {reason}")
        msg.setInformativeText(
            f"Trading Summary:\n"
            f"Initial Balance: ${self.initial_balance:.2f}\n"
            f"Final Balance: ${self.current_balance:.2f}\n"
            f"Total P&L: ${final_pnl:.2f}\n"
            f"Peak Balance: ${self.peak_balance:.2f}\n"
            f"Max Drawdown: {((self.peak_balance - self.current_balance) / self.peak_balance * 100):.1f}%"
        )
        msg.exec()
        
    def _show_error(self, title: str, message: str):
        """Show error message."""
        if self.parent:
            QMessageBox.critical(self.parent, title, message)
        logger.error(f"{title}: {message}") 