from PyQt6.QtWidgets import QApplication
import sys
from .ui.main_window import MainWindow
from .core.engine import TradingEngine
from .utils.logger_config import setup_logging, ErrorTracker
from .utils.update_monitor import UpdateMonitor

def main():
    # Set up logging and error tracking
    error_tracker = setup_logging()
    
    # Create update monitor
    update_monitor = UpdateMonitor(error_tracker)
    
    # Create application
    app = QApplication(sys.argv)
    
    # Check for updates
    if update_info := update_monitor.check_for_updates():
        # Show update dialog
        # TODO: Implement update dialog
        pass
        
    # Create main components
    trading_engine = TradingEngine()
    main_window = MainWindow(trading_engine)
    main_window.show()
    
    # Start application
    exit_code = app.exec()
    
    # Report any errors before exit
    update_monitor.report_errors()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main() 