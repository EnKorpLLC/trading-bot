import sys
from PyQt6.QtWidgets import QApplication
from .ui.main_window import MainWindow
from .core.engine import TradingEngine
from .utils.theme_manager import ThemeManager

def main():
    app = QApplication(sys.argv)
    
    # Initialize theme manager
    theme_manager = ThemeManager()
    theme_manager.apply_theme(app)
    
    # Initialize trading engine with dummy credentials
    # These will be updated through the setup wizard
    trading_engine = TradingEngine("", "")
    
    # Create and show main window
    window = MainWindow(trading_engine)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 