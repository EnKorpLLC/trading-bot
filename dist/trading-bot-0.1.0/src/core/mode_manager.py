from enum import Enum
from typing import Optional
import logging
from PyQt6.QtWidgets import QMessageBox, QWidget
from ..utils.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class TradingMode(Enum):
    DEMO = "demo"
    SANDBOX = "sandbox"
    LIVE = "live"

class ModeManager:
    def __init__(self, parent_widget: Optional[QWidget] = None):
        self.current_mode = TradingMode.DEMO
        self.parent = parent_widget
        self.config = ConfigManager()
        self._load_saved_mode()
        
    def _load_saved_mode(self):
        """Load previously saved trading mode."""
        saved_mode = self.config.get_setting('trading_mode')
        if saved_mode:
            self.current_mode = TradingMode(saved_mode)
            
    def get_current_mode(self) -> TradingMode:
        """Get current trading mode."""
        return self.current_mode
        
    def is_live(self) -> bool:
        """Check if currently in live trading mode."""
        return self.current_mode == TradingMode.LIVE
        
    def switch_mode(self, new_mode: TradingMode) -> bool:
        """
        Switch to a different trading mode with safety checks.
        Returns True if mode switch was successful.
        """
        if new_mode == self.current_mode:
            return True
            
        if new_mode == TradingMode.LIVE:
            if not self._confirm_live_trading():
                return False
                
        # Perform mode switch
        self.current_mode = new_mode
        self.config.set_setting('trading_mode', new_mode.value)
        logger.info(f"Switched to {new_mode.value} trading mode")
        
        return True
        
    def _confirm_live_trading(self) -> bool:
        """Show warning and get confirmation for live trading."""
        if not self.parent:
            return False
            
        warning_msg = QMessageBox(self.parent)
        warning_msg.setIcon(QMessageBox.Icon.Warning)
        warning_msg.setWindowTitle("Live Trading Warning")
        warning_msg.setText("⚠️ You are about to switch to LIVE trading mode!")
        warning_msg.setInformativeText(
            "In live mode, real money will be at risk. Make sure you:\n\n"
            "1. Have thoroughly tested your strategies in demo mode\n"
            "2. Understand all risks involved\n"
            "3. Are using proper risk management\n"
            "4. Have verified all API credentials\n\n"
            "Do you want to proceed with live trading?"
        )
        warning_msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        warning_msg.setDefaultButton(QMessageBox.StandardButton.No)
        
        response = warning_msg.exec()
        return response == QMessageBox.StandardButton.Yes
        
    def get_api_endpoint(self) -> str:
        """Get appropriate API endpoint for current mode."""
        if self.current_mode == TradingMode.LIVE:
            return "https://api.trade-locker.com/v1/"
        elif self.current_mode == TradingMode.SANDBOX:
            return "https://sandbox.trade-locker.com/v1/"
        else:  # DEMO mode
            return "https://demo.trade-locker.com/v1/"
            
    def validate_mode_requirements(self) -> bool:
        """Validate requirements for current mode."""
        if self.current_mode == TradingMode.LIVE:
            return self._validate_live_requirements()
        return True
        
    def _validate_live_requirements(self) -> bool:
        """Validate requirements for live trading."""
        # Check API credentials
        credentials = self.config.get_api_credentials()
        if not credentials:
            self._show_error("Missing API Credentials",
                           "Live trading requires valid API credentials.")
            return False
            
        # Check strategy backtesting
        if not self._verify_strategy_testing():
            self._show_error("Insufficient Testing",
                           "Strategies must be thoroughly tested before live trading.")
            return False
            
        return True
        
    def _verify_strategy_testing(self) -> bool:
        """Verify that strategies have been properly tested."""
        # TODO: Implement verification of strategy testing history
        # This should check:
        # 1. Number of backtest runs
        # 2. Demo trading results
        # 3. Risk parameters
        return False
        
    def _show_error(self, title: str, message: str):
        """Show error message to user."""
        if self.parent:
            QMessageBox.critical(self.parent, title, message) 