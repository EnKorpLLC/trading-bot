from typing import Dict, Optional
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QSplitter, QFrame, QDockWidget,
    QMenuBar, QMenu, QToolBar, QStatusBar, QLabel
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon

from .strategy_panel import StrategyPanel
from .advanced_chart import AdvancedChart
from .alert_system import AlertSystem
from .trades_panel import TradesPanel
from .order_book_widget import OrderBookWidget
from .market_depth_widget import MarketDepthWidget
from .performance_widget import PerformanceWidget
from ..core.engine import TradingEngine

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main application window with advanced trading interface."""
    
    def __init__(self, trading_engine: Optional[TradingEngine] = None):
        super().__init__()
        self.engine = trading_engine or TradingEngine()
        self.chart = None
        self.balance_label = None
        self._init_ui()

    def _init_ui(self):
        """Initialize the user interface."""
        try:
            # Set window properties
            self.setWindowTitle("Trading Bot")
            self.setMinimumSize(1200, 800)

            # Create main widget and layout
            main_widget = QWidget()
            self.setCentralWidget(main_widget)
            layout = QVBoxLayout(main_widget)

            # Create main splitter
            splitter = QSplitter(Qt.Orientation.Horizontal)
            layout.addWidget(splitter)

            # Add chart
            self.chart = AdvancedChart()
            splitter.addWidget(self.chart)

            # Create right panel
            right_panel = QWidget()
            right_layout = QVBoxLayout(right_panel)
            splitter.addWidget(right_panel)

            # Add strategy panel
            self.strategy_panel = StrategyPanel(self.engine)
            right_layout.addWidget(self.strategy_panel)

            # Add trades panel
            self.trades_panel = TradesPanel()
            right_layout.addWidget(self.trades_panel)

            # Set up status bar
            status_bar = QStatusBar()
            self.setStatusBar(status_bar)
            self.balance_label = QLabel("Balance: $0.00")
            status_bar.addPermanentWidget(self.balance_label)

            # Connect signals
            self.strategy_panel.strategy_changed.connect(self._on_strategy_changed)
            self.strategy_panel.config_changed.connect(self._on_config_changed)

            logger.info("UI initialization completed successfully")

        except Exception as e:
            logger.error(f"Error initializing UI: {str(e)}")
            raise

    def _on_strategy_changed(self, strategy_name: str):
        """Handle strategy change."""
        try:
            # Update chart indicators
            self.chart.clear_indicators()
            strategy = self.engine.strategy_manager.get_strategy(strategy_name)
            if strategy:
                for indicator in strategy.get_indicators():
                    self.chart.add_indicator(indicator)
                    
        except Exception as e:
            logger.error(f"Error handling strategy change: {str(e)}")
            
    def _on_config_changed(self, config: Dict):
        """Handle strategy configuration change."""
        try:
            self.engine.update_strategy_config(config)
            
        except Exception as e:
            logger.error(f"Error handling config change: {str(e)}")
            
    def _on_alert_triggered(self, message: str):
        """Handle alert trigger."""
        try:
            self.statusBar().showMessage(message, 3000)
            
        except Exception as e:
            logger.error(f"Error handling alert: {str(e)}")
            
    def _update_balance(self, balance: float):
        """Update balance display."""
        try:
            self.balance_label.setText(f"Balance: ${balance:,.2f}")
            
        except Exception as e:
            logger.error(f"Error updating balance: {str(e)}")
            
    def closeEvent(self, event):
        """Handle application close."""
        try:
            # Stop trading
            self.engine.stop()
            
            # Save window state
            # TODO: Save window geometry and state
            
            event.accept()
            
        except Exception as e:
            logger.error(f"Error closing application: {str(e)}")
            event.accept()
