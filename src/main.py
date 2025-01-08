import sys
import logging
from PyQt6.QtWidgets import QApplication, QInputDialog, QMessageBox, QLineEdit
from PyQt6.QtCore import Qt

from src.ui.main_window import MainWindow
from src.core.engine import TradingEngine
from src.utils.theme_manager import ThemeManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the trading bot application."""
    try:
        # Create application
        app = QApplication(sys.argv)
        
        # Initialize theme manager
        theme_manager = ThemeManager()
        theme_manager.apply_theme(app)
        
        # Prompt for API credentials
        api_key, ok1 = QInputDialog.getText(None, "API Key", "Please enter your API key:")
        if not ok1 or not api_key:
            QMessageBox.critical(None, "Error", "API key is required.")
            return
            
        api_secret, ok2 = QInputDialog.getText(
            None, 
            "API Secret", 
            "Please enter your API secret:", 
            QLineEdit.EchoMode.Password
        )
        if not ok2 or not api_secret:
            QMessageBox.critical(None, "Error", "API secret is required.")
            return
            
        # Create trading engine
        trading_engine = TradingEngine(api_key, api_secret)
        
        # Create and show main window
        window = MainWindow(trading_engine)
        window.show()
        
        # Set up available strategies
        strategies = trading_engine.strategy_manager.get_available_strategies()
        window.set_available_strategies(strategies)
        
        # Connect signals
        trading_engine.account_updated.connect(window.update_account_info)
        trading_engine.market_data_updated.connect(window.update_chart)
        trading_engine.order_book_updated.connect(window.update_order_book)
        trading_engine.trade_history_updated.connect(window.update_trade_history)
        
        # Start the application
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Error starting application: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 