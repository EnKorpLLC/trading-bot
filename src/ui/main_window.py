from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QVBoxLayout, 
    QPushButton, QLabel, QComboBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QGridLayout, QMessageBox, QGroupBox, QFormLayout, QDoubleSpinBox, QHBoxLayout
)
from PyQt6.QtCore import Qt, QTimer
import logging
from typing import Dict, Optional
from PyQt6.QtWidgets import QApplication

from ..core.engine import TradingEngine
from .strategy_panel import StrategyPanel
from .market_panel import MarketPanel
from .trades_panel import TradesPanel
from .setup_wizard import APISetupWizard
from ..utils.theme_manager import ThemeManager
from ..core.mode_manager import ModeManager, TradingMode
from ..core.safety_system import SafetySystem
from ..core.independent_mode import IndependentMode
from ..utils.notification_manager import NotificationManager

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self, trading_engine: TradingEngine):
        super().__init__()
        self.trading_engine = trading_engine
        self.theme_manager = ThemeManager()
        
        # Initialize mode and safety systems
        self.mode_manager = ModeManager(self)
        self.safety_system = SafetySystem(self.mode_manager, self)
        
        # Initialize independent mode
        self.independent_mode = IndependentMode(
            trading_engine=self.trading_engine,
            mode_manager=self.mode_manager,
            safety_system=self.safety_system,
            parent_widget=self
        )
        
        self.init_ui()
        
        # Update timer for real-time data
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_displays)
        self.update_timer.start(1000)
        
        # Initialize notification manager
        self.notification_manager = NotificationManager()
        
        # Show welcome message
        self.show_welcome_message()
        
    def show_welcome_message(self):
        """Show a welcome message introducing the application."""
        welcome = QMessageBox(self)
        welcome.setIcon(QMessageBox.Icon.Information)
        welcome.setWindowTitle("Welcome to Trading Bot")
        welcome.setText(
            "Welcome to Trading Bot!\n\n"
            "Feel free to explore the interface and familiarize yourself with the features:\n\n"
            "• Market Analysis - View market data and trends\n"
            "• Strategies - Configure and test trading strategies\n"
            "• Active Trades - Monitor your trading activity\n\n"
            "When you're ready to start trading, you'll need to connect your Trade Locker account.\n"
            "You can do this anytime through the Settings menu."
        )
        welcome.exec()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle('Trading Bot Control Panel')
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create control panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # Create tab widget
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Create and add tabs
        self.strategy_panel = StrategyPanel(self.trading_engine)
        self.market_panel = MarketPanel(self.trading_engine)
        self.trades_panel = TradesPanel(self.trading_engine)
        
        tabs.addTab(self.market_panel, "Market Analysis")
        tabs.addTab(self.strategy_panel, "Strategies")
        tabs.addTab(self.trades_panel, "Active Trades")
        
        # Add mode selector to toolbar
        self._add_mode_selector()
        
        # Add independent mode controls
        self._add_independent_mode_controls()
        
    def _create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # Settings menu
        settings_menu = menubar.addMenu('Settings')
        
        # API Setup action
        api_setup_action = settings_menu.addAction('Configure API Credentials')
        api_setup_action.triggered.connect(self.show_setup_wizard)
        
        # Theme toggle action
        theme_action = settings_menu.addAction('Toggle Theme')
        theme_action.triggered.connect(self.toggle_theme)
        
    def create_control_panel(self) -> QWidget:
        """Create the top control panel."""
        panel = QWidget()
        self.control_panel_layout = QVBoxLayout(panel)  # Store layout reference
        
        # Create top controls group
        top_controls = QGroupBox("Trading Controls")
        top_layout = QGridLayout()
        
        # Trading controls
        self.trading_enabled = QCheckBox("Enable Trading")
        self.trading_enabled.setChecked(False)
        self.trading_enabled.stateChanged.connect(self.toggle_trading)
        
        self.user_confirmation = QCheckBox("Require User Confirmation")
        self.user_confirmation.setChecked(False)
        self.user_confirmation.stateChanged.connect(self.toggle_user_confirmation)
        
        # Status indicators
        self.connection_status = QLabel("Status: Disconnected")
        self.active_strategies = QLabel("Active Strategies: 0")
        self.open_trades = QLabel("Open Trades: 0")
        
        # Add independent mode status
        self.independent_status = QLabel("Independent Mode: Inactive")
        self.current_pnl = QLabel("Current P&L: $0.00")
        
        # Add widgets to top layout
        top_layout.addWidget(self.trading_enabled, 0, 0)
        top_layout.addWidget(self.user_confirmation, 0, 1)
        top_layout.addWidget(self.connection_status, 0, 2)
        top_layout.addWidget(self.active_strategies, 0, 3)
        top_layout.addWidget(self.open_trades, 0, 4)
        
        # Add theme toggle button
        theme_btn = QPushButton("Toggle Theme")
        theme_btn.clicked.connect(self.toggle_theme)
        top_layout.addWidget(theme_btn, 0, 5)
        
        top_controls.setLayout(top_layout)
        self.control_panel_layout.addWidget(top_controls)
        
        # Add status bar for real-time metrics
        self._add_status_bar()
        
        return panel
        
    def toggle_trading(self, state: int):
        """Enable or disable trading."""
        enabled = bool(state)
        if enabled:
            if not self.trading_engine.has_credentials():
                response = QMessageBox.question(
                    self,
                    "API Credentials Required",
                    "To enable trading, you need to connect your Trade Locker account.\n\n"
                    "Would you like to set up your API credentials now?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if response == QMessageBox.StandardButton.Yes:
                    self.show_setup_wizard()
                self.trading_enabled.setChecked(False)
                return
            # Add safety confirmation
            # TODO: Add confirmation dialog
            logger.info("Trading enabled")
        else:
            logger.info("Trading disabled")
            
    def toggle_user_confirmation(self, state: int):
        """Toggle user confirmation requirement."""
        required = bool(state)
        self.trading_engine.set_user_confirmation(required)
        
    def update_displays(self):
        """Update all display elements with current data."""
        try:
            # Update status indicators
            self.connection_status.setText(f"Status: {self.trading_engine.get_connection_status()}")
            self.active_strategies.setText(f"Active Strategies: {len(self.trading_engine.strategy_manager.strategies)}")
            self.open_trades.setText(f"Open Trades: {len(self.trading_engine.active_trades)}")
            
            # Update independent mode status
            if self.independent_mode.is_active:
                pnl = self.independent_mode.current_balance - self.independent_mode.initial_balance
                self.independent_status.setText("Independent Mode: Active")
                self.current_pnl.setText(f"Current P&L: ${pnl:.2f}")
            else:
                self.independent_status.setText("Independent Mode: Inactive")
                
            # Update status bar
            balance = self.trading_engine.get_account_balance()
            daily_pnl = self.trading_engine.get_daily_pnl()
            drawdown = self.trading_engine.get_current_drawdown()
            
            self.status_balance.setText(f"Balance: ${balance:.2f}")
            self.status_daily_pnl.setText(f"Daily P&L: ${daily_pnl:.2f}")
            self.status_drawdown.setText(f"Drawdown: {drawdown:.2f}%")
            self.status_mode.setText(f"Mode: {self.mode_manager.get_current_mode().value}")
            
            # Update panels
            self.strategy_panel.update_display()
            self.market_panel.update_display()
            self.trades_panel.update_display()
            
        except Exception as e:
            logger.error(f"Error updating displays: {str(e)}")
        
    def check_api_credentials(self) -> bool:
        """Check if API credentials are configured."""
        return self.trading_engine.has_credentials()
        
    def show_setup_wizard(self):
        """Show the API setup wizard."""
        wizard = APISetupWizard(self)
        if wizard.exec():
            credentials = wizard.get_credentials()
            if credentials:
                success = self.trading_engine.set_credentials(
                    credentials['api_key'],
                    credentials['api_secret']
                )
                if success:
                    QMessageBox.information(
                        self,
                        "Success",
                        "API credentials configured successfully!"
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Error",
                        "Failed to verify API credentials. Please try again."
                    )
        else:
            # User clicked "Skip for Now"
            QMessageBox.information(
                self,
                "Setup Skipped",
                "You can configure your API credentials later through the Settings menu.\n\n"
                "For now, you can explore the application's features in demo mode."
            )
        
    def toggle_theme(self):
        """Toggle between light and dark themes."""
        self.theme_manager.toggle_theme(QApplication.instance()) 
        
    def _add_mode_selector(self):
        """Add trading mode selector to toolbar."""
        mode_toolbar = self.addToolBar("Trading Mode")
        
        mode_label = QLabel("Trading Mode: ")
        mode_toolbar.addWidget(mode_label)
        
        mode_combo = QComboBox()
        mode_combo.addItems([mode.value for mode in TradingMode])
        mode_combo.setCurrentText(self.mode_manager.get_current_mode().value)
        mode_combo.currentTextChanged.connect(self._handle_mode_change)
        mode_toolbar.addWidget(mode_combo)
        
    def _handle_mode_change(self, new_mode: str):
        """Handle trading mode change."""
        success = self.mode_manager.switch_mode(TradingMode(new_mode))
        if success and new_mode == TradingMode.LIVE.value:
            self._show_live_guidelines()
            
    def _show_live_guidelines(self):
        """Show guidelines for live trading."""
        guidelines = QMessageBox(self)
        guidelines.setIcon(QMessageBox.Icon.Information)
        guidelines.setWindowTitle("Live Trading Guidelines")
        guidelines.setText(
            "Please follow these guidelines for safe live trading:\n\n"
            "1. Start with small position sizes\n"
            "2. Monitor your trades regularly\n"
            "3. Use stop losses for all trades\n"
            "4. Don't risk more than 1% per trade\n"
            "5. Keep detailed trading records\n\n"
            "The safety system will help enforce these rules."
        )
        guidelines.exec() 
        
    def _add_independent_mode_controls(self):
        """Add independent mode controls to control panel."""
        independent_group = QGroupBox("Independent Mode")
        layout = QVBoxLayout()
        
        # Create controls
        self.independent_switch = QCheckBox("Enable Independent Mode")
        self.independent_switch.stateChanged.connect(self._handle_independent_mode)
        
        # Add status labels
        status_layout = QHBoxLayout()
        status_layout.addWidget(self.independent_status)
        status_layout.addWidget(self.current_pnl)
        
        # Add limit inputs
        limits_layout = QFormLayout()
        self.max_loss_input = QDoubleSpinBox()
        self.max_loss_input.setRange(0, 1000000)
        self.max_loss_input.setPrefix("$")
        self.max_loss_input.setDecimals(2)
        
        self.take_profit_input = QDoubleSpinBox()
        self.take_profit_input.setRange(0, 1000000)
        self.take_profit_input.setPrefix("$")
        self.take_profit_input.setDecimals(2)
        
        self.max_drawdown_input = QDoubleSpinBox()
        self.max_drawdown_input.setRange(0, 100)
        self.max_drawdown_input.setSuffix("%")
        self.max_drawdown_input.setDecimals(1)
        
        self.daily_loss_input = QDoubleSpinBox()
        self.daily_loss_input.setRange(0, 1000000)
        self.daily_loss_input.setPrefix("$")
        self.daily_loss_input.setDecimals(2)
        
        limits_layout.addRow("Max Loss:", self.max_loss_input)
        limits_layout.addRow("Take Profit:", self.take_profit_input)
        limits_layout.addRow("Max Drawdown:", self.max_drawdown_input)
        limits_layout.addRow("Daily Loss Limit:", self.daily_loss_input)
        
        # Add to layout
        layout.addWidget(self.independent_switch)
        layout.addLayout(status_layout)
        layout.addLayout(limits_layout)
        
        independent_group.setLayout(layout)
        self.control_panel_layout.addWidget(independent_group)
        
    def _handle_independent_mode(self, state: int):
        """Handle independent mode toggle."""
        if state == Qt.CheckState.Checked:
            limits = {
                'max_loss': self.max_loss_input.value(),
                'take_profit': self.take_profit_input.value(),
                'max_drawdown': self.max_drawdown_input.value() / 100,
                'daily_loss_limit': self.daily_loss_input.value(),
                'position_limit': 5  # Default value
            }
            
            if not self.independent_mode.start(limits):
                self.independent_switch.setChecked(False)
        else:
            self.independent_mode.stop("User disabled independent mode") 
        
    def _add_status_bar(self):
        """Add status bar for real-time metrics."""
        self.statusBar = self.statusBar()
        
        # Add permanent widgets to status bar
        self.status_balance = QLabel("Balance: $0.00")
        self.status_daily_pnl = QLabel("Daily P&L: $0.00")
        self.status_drawdown = QLabel("Drawdown: 0.00%")
        self.status_mode = QLabel("Mode: Demo")
        
        self.statusBar.addPermanentWidget(self.status_balance)
        self.statusBar.addPermanentWidget(self.status_daily_pnl)
        self.statusBar.addPermanentWidget(self.status_drawdown)
        self.statusBar.addPermanentWidget(self.status_mode) 
        
    def _handle_trade_signal(self, signal: Dict):
        """Handle new trade signal."""
        # ... existing trade handling ...
        
        # Send notification
        self.notification_manager.send_notification(
            "New Trade Signal",
            f"Signal for {signal['symbol']}: {signal['side'].upper()} at {signal['entry_price']}",
            priority="normal",
            channels=["device", "email"]  # Customize based on importance
        )
        
    def _handle_trade_exit(self, trade: Dict):
        """Handle trade exit."""
        # ... existing exit handling ...
        
        # Send notification with appropriate priority
        priority = "high" if trade['pnl'] < 0 else "normal"
        self.notification_manager.send_notification(
            "Trade Closed",
            f"Closed {trade['symbol']} trade: {trade['pnl']:.2f} profit/loss",
            priority=priority,
            channels=["device", "email", "sms"]  # Important events get all channels
        ) 