from typing import Dict, Optional, List
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
    QPushButton, QLabel, QScrollArea, QFrame,
    QSpinBox, QDoubleSpinBox, QCheckBox, QTabWidget,
    QGridLayout, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from ..config.market_config import ALL_PAIRS, TIMEFRAMES
from ..strategies.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class ParameterWidget(QWidget):
    """Widget for editing a single strategy parameter."""
    
    valueChanged = pyqtSignal(str, object)  # Parameter name, new value
    
    def __init__(self, name: str, value: object, param_type: type):
        super().__init__()
        self.name = name
        self.value = value
        self.param_type = param_type
        self._init_ui()
        
    def _init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Parameter label
        label = QLabel(self.name.replace('_', ' ').title())
        layout.addWidget(label)
        
        # Create appropriate input widget based on parameter type
        if self.param_type == bool:
            self.input_widget = QCheckBox()
            self.input_widget.setChecked(self.value)
            self.input_widget.stateChanged.connect(self._value_changed)
            
        elif self.param_type == int:
            self.input_widget = QSpinBox()
            self.input_widget.setRange(-999999, 999999)
            self.input_widget.setValue(self.value)
            self.input_widget.valueChanged.connect(self._value_changed)
            
        elif self.param_type == float:
            self.input_widget = QDoubleSpinBox()
            self.input_widget.setRange(-999999.99, 999999.99)
            self.input_widget.setDecimals(4)
            self.input_widget.setValue(self.value)
            self.input_widget.valueChanged.connect(self._value_changed)
            
        else:  # str or other types
            self.input_widget = QComboBox()
            self.input_widget.addItem(str(self.value))
            self.input_widget.currentTextChanged.connect(self._value_changed)
            
        layout.addWidget(self.input_widget)
        self.setLayout(layout)
        
    def _value_changed(self, value):
        """Handle value change and emit signal."""
        self.value = value
        self.valueChanged.emit(self.name, value)

class StrategyConfigWidget(QWidget):
    """Widget for configuring strategy parameters."""
    
    parameterChanged = pyqtSignal(str, object)  # Parameter name, new value
    
    def __init__(self, strategy: BaseStrategy):
        super().__init__()
        self.strategy = strategy
        self.parameter_widgets = {}
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout()
        
        # Create parameter widgets
        for name, value in self.strategy.parameters.items():
            param_widget = ParameterWidget(name, value, type(value))
            param_widget.valueChanged.connect(self._parameter_changed)
            self.parameter_widgets[name] = param_widget
            layout.addWidget(param_widget)
            
        layout.addStretch()
        self.setLayout(layout)
        
    def _parameter_changed(self, name: str, value: object):
        """Handle parameter change."""
        self.strategy.parameters[name] = value
        self.parameterChanged.emit(name, value)

class StrategyPanel(QWidget):
    """Advanced strategy selection and configuration panel."""
    
    strategyChanged = pyqtSignal(str)  # Strategy name
    configurationChanged = pyqtSignal(Dict)  # Updated configuration
    
    def __init__(self, strategy_manager):
        super().__init__()
        self.strategy_manager = strategy_manager
        self.current_strategy = None
        self.config_widget = None
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout()
        
        # Create tabs for different sections
        tab_widget = QTabWidget()
        
        # Strategy Selection Tab
        selection_tab = QWidget()
        selection_layout = QVBoxLayout()
        
        # Strategy selection group
        strategy_group = QGroupBox("Strategy Selection")
        strategy_layout = QGridLayout()
        
        # Strategy dropdown
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(self.strategy_manager.get_available_strategies())
        self.strategy_combo.currentTextChanged.connect(self._strategy_changed)
        strategy_layout.addWidget(QLabel("Strategy:"), 0, 0)
        strategy_layout.addWidget(self.strategy_combo, 0, 1)
        
        # Timeframe selection
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(TIMEFRAMES)
        strategy_layout.addWidget(QLabel("Timeframe:"), 1, 0)
        strategy_layout.addWidget(self.timeframe_combo, 1, 1)
        
        # Symbol selection
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(ALL_PAIRS)
        strategy_layout.addWidget(QLabel("Symbol:"), 2, 0)
        strategy_layout.addWidget(self.symbol_combo, 2, 1)
        
        strategy_group.setLayout(strategy_layout)
        selection_layout.addWidget(strategy_group)
        
        # Strategy status and controls
        control_group = QGroupBox("Strategy Control")
        control_layout = QHBoxLayout()
        
        self.activate_button = QPushButton("Activate")
        self.activate_button.clicked.connect(self._toggle_strategy)
        control_layout.addWidget(self.activate_button)
        
        self.status_label = QLabel("Status: Inactive")
        control_layout.addWidget(self.status_label)
        
        control_group.setLayout(control_layout)
        selection_layout.addWidget(control_group)
        
        selection_layout.addStretch()
        selection_tab.setLayout(selection_layout)
        tab_widget.addTab(selection_tab, "Selection")
        
        # Configuration Tab
        config_tab = QWidget()
        self.config_layout = QVBoxLayout()
        
        # Scroll area for parameters
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.config_container = QWidget()
        self.config_container_layout = QVBoxLayout()
        self.config_container.setLayout(self.config_container_layout)
        scroll.setWidget(self.config_container)
        
        self.config_layout.addWidget(scroll)
        config_tab.setLayout(self.config_layout)
        tab_widget.addTab(config_tab, "Configuration")
        
        # Performance Tab
        performance_tab = QWidget()
        performance_layout = QVBoxLayout()
        
        # Performance metrics
        metrics_group = QGroupBox("Performance Metrics")
        metrics_layout = QGridLayout()
        
        self.win_rate_label = QLabel("Win Rate: 0%")
        metrics_layout.addWidget(self.win_rate_label, 0, 0)
        
        self.profit_factor_label = QLabel("Profit Factor: 0")
        metrics_layout.addWidget(self.profit_factor_label, 0, 1)
        
        self.avg_win_label = QLabel("Avg Win: $0")
        metrics_layout.addWidget(self.avg_win_label, 1, 0)
        
        self.avg_loss_label = QLabel("Avg Loss: $0")
        metrics_layout.addWidget(self.avg_loss_label, 1, 1)
        
        self.total_trades_label = QLabel("Total Trades: 0")
        metrics_layout.addWidget(self.total_trades_label, 2, 0)
        
        self.sharpe_ratio_label = QLabel("Sharpe Ratio: 0")
        metrics_layout.addWidget(self.sharpe_ratio_label, 2, 1)
        
        metrics_group.setLayout(metrics_layout)
        performance_layout.addWidget(metrics_group)
        
        # Add optimization button
        optimize_button = QPushButton("Optimize Parameters")
        optimize_button.clicked.connect(self._optimize_strategy)
        performance_layout.addWidget(optimize_button)
        
        performance_layout.addStretch()
        performance_tab.setLayout(performance_layout)
        tab_widget.addTab(performance_tab, "Performance")
        
        layout.addWidget(tab_widget)
        self.setLayout(layout)
        
    def _strategy_changed(self, strategy_name: str):
        """Handle strategy selection change."""
        try:
            # Get strategy instance
            self.current_strategy = self.strategy_manager.get_strategy(strategy_name)
            
            # Update configuration widget
            if self.current_strategy:
                self._update_config_widget()
                self.strategyChanged.emit(strategy_name)
                
        except Exception as e:
            logger.error(f"Error changing strategy: {str(e)}")
            
    def _update_config_widget(self):
        """Update configuration widget with current strategy parameters."""
        try:
            # Clear existing config
            for i in reversed(range(self.config_container_layout.count())):
                self.config_container_layout.itemAt(i).widget().setParent(None)
                
            # Create new config widget
            self.config_widget = StrategyConfigWidget(self.current_strategy)
            self.config_widget.parameterChanged.connect(self._config_changed)
            self.config_container_layout.addWidget(self.config_widget)
            
        except Exception as e:
            logger.error(f"Error updating config widget: {str(e)}")
            
    def _config_changed(self, name: str, value: object):
        """Handle configuration parameter change."""
        try:
            if self.current_strategy:
                self.current_strategy.parameters[name] = value
                self.configurationChanged.emit(self.current_strategy.parameters)
                
        except Exception as e:
            logger.error(f"Error updating configuration: {str(e)}")
            
    def _toggle_strategy(self):
        """Toggle strategy activation state."""
        try:
            if not self.current_strategy:
                return
                
            if self.current_strategy.is_active:
                self.strategy_manager.deactivate_strategy(self.current_strategy.name)
                self.activate_button.setText("Activate")
                self.status_label.setText("Status: Inactive")
            else:
                self.strategy_manager.activate_strategy(
                    self.current_strategy.name,
                    self.symbol_combo.currentText(),
                    self.timeframe_combo.currentText()
                )
                self.activate_button.setText("Deactivate")
                self.status_label.setText("Status: Active")
                
        except Exception as e:
            logger.error(f"Error toggling strategy: {str(e)}")
            
    def _optimize_strategy(self):
        """Launch strategy optimization dialog."""
        try:
            if not self.current_strategy:
                return
                
            # TODO: Implement strategy optimization dialog
            pass
            
        except Exception as e:
            logger.error(f"Error optimizing strategy: {str(e)}")
            
    def update_performance_metrics(self, metrics: Dict):
        """Update performance metrics display."""
        try:
            self.win_rate_label.setText(f"Win Rate: {metrics.get('win_rate', 0):.1f}%")
            self.profit_factor_label.setText(f"Profit Factor: {metrics.get('profit_factor', 0):.2f}")
            self.avg_win_label.setText(f"Avg Win: ${metrics.get('avg_win', 0):.2f}")
            self.avg_loss_label.setText(f"Avg Loss: ${metrics.get('avg_loss', 0):.2f}")
            self.total_trades_label.setText(f"Total Trades: {metrics.get('total_trades', 0)}")
            self.sharpe_ratio_label.setText(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
            
        except Exception as e:
            logger.error(f"Error updating performance metrics: {str(e)}") 