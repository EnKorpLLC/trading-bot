import sys
import os
from PyQt6.QtWidgets import QApplication

def get_base_path():
    """Get the base path for the application, works both in development and when frozen"""
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle (frozen)
        return os.path.dirname(sys.executable)
    # If running from source
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Set up the base path
base_path = get_base_path()
if base_path not in sys.path:
    sys.path.insert(0, base_path)

from src.ui.main_window import MainWindow
from src.core.engine import TradingEngine
from src.utils.theme_manager import ThemeManager

__version__ = "0.2.0"

def main():
    app = QApplication(sys.argv)
    
    # Initialize theme manager
    theme_manager = ThemeManager()
    theme_manager.apply_theme(app)
    
    # Create trading engine without credentials initially
    trading_engine = TradingEngine(api_key=None, api_secret=None)
    
    # Create and show main window
    window = MainWindow(trading_engine)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 