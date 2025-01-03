import sys
from PyQt6.QtWidgets import QApplication, QInputDialog, QMessageBox, QLineEdit
from src.ui.main_window import MainWindow
from .core.engine import TradingEngine
from .utils.theme_manager import ThemeManager

def main():
    app = QApplication(sys.argv)
    
    # Initialize theme manager
    theme_manager = ThemeManager()
    theme_manager.apply_theme(app)
    
    # Prompt the user for their API key and secret using input dialogs
    api_key, ok1 = QInputDialog.getText(None, "API Key", "Please enter your API key:")
    if not ok1 or not api_key:
        QMessageBox.critical(None, "Error", "API key is required.")
        return  # Exit if no API key is provided

    api_secret, ok2 = QInputDialog.getText(None, "API Secret", "Please enter your API secret:", QLineEdit.EchoMode.Password)
    if not ok2 or not api_secret:
        QMessageBox.critical(None, "Error", "API secret is required.")
        return  # Exit if no API secret is provided
    
    trading_engine = TradingEngine(api_key, api_secret)
    
    # Create and show main window
    window = MainWindow(trading_engine)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 