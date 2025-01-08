from typing import Dict, Any
import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QComboBox,
                          QDoubleSpinBox, QLabel, QPushButton, QFrame)
from PyQt5.QtCore import pyqtSignal

logger = logging.getLogger(__name__)

class StrategyControls(QWidget):
    """Widget for controlling trading strategy parameters."""
    
    # Signals
    strategy_changed = pyqtSignal(str)  # Emitted when strategy is changed
    parameters_changed = pyqtSignal(dict)  # Emitted when parameters are changed
    strategy_toggled = pyqtSignal(bool)  # Emitted when strategy is started/stopped
    
    def __init__(self):
        """Initialize the strategy controls widget."""
        super().__init__()
        self._setup_ui()
        self._current_strategy = None
        self._parameter_widgets = {}
        
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Create header
        header = QLabel("Strategy Controls")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)
        
        # Create strategy selector
        self.strategy_combo = QComboBox()
        self.strategy_combo.currentTextChanged.connect(self._on_strategy_changed)
        layout.addWidget(self.strategy_combo)
        
        # Create parameters form
        parameters_frame = QFrame()
        parameters_frame.setFrameStyle(QFrame.StyledPanel)
        self.parameters_layout = QFormLayout(parameters_frame)
        layout.addWidget(parameters_frame)
        
        # Create control buttons
        self.toggle_button = QPushButton("Start Strategy")
        self.toggle_button.setCheckable(True)
        self.toggle_button.toggled.connect(self._on_strategy_toggled)
        layout.addWidget(self.toggle_button)
        
    def set_available_strategies(self, strategies: list):
        """Set the list of available strategies."""
        try:
            current = self.strategy_combo.currentText()
            
            self.strategy_combo.clear()
            self.strategy_combo.addItems(strategies)
            
            if current in strategies:
                self.strategy_combo.setCurrentText(current)
                
        except Exception as e:
            logger.error(f"Error setting available strategies: {str(e)}")
            
    def set_strategy_parameters(self, parameters: Dict[str, Dict[str, Any]]):
        """Set up parameter controls for the current strategy."""
        try:
            # Clear existing parameters
            while self.parameters_layout.count():
                item = self.parameters_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self._parameter_widgets.clear()
            
            # Add new parameter controls
            for name, config in parameters.items():
                # Create label
                label = QLabel(name.replace('_', ' ').title())
                
                # Create parameter widget based on type
                if isinstance(config.get('default'), float):
                    widget = QDoubleSpinBox()
                    widget.setDecimals(config.get('decimals', 2))
                    widget.setMinimum(config.get('min', 0))
                    widget.setMaximum(config.get('max', 999999))
                    widget.setValue(config.get('default', 0))
                    widget.valueChanged.connect(self._on_parameter_changed)
                else:
                    widget = QComboBox()
                    widget.addItems(map(str, config.get('options', [])))
                    widget.setCurrentText(str(config.get('default', '')))
                    widget.currentTextChanged.connect(self._on_parameter_changed)
                
                self.parameters_layout.addRow(label, widget)
                self._parameter_widgets[name] = widget
                
        except Exception as e:
            logger.error(f"Error setting strategy parameters: {str(e)}")
            
    def get_parameters(self) -> Dict[str, Any]:
        """Get current parameter values."""
        try:
            parameters = {}
            for name, widget in self._parameter_widgets.items():
                if isinstance(widget, QDoubleSpinBox):
                    parameters[name] = widget.value()
                else:
                    parameters[name] = widget.currentText()
            return parameters
            
        except Exception as e:
            logger.error(f"Error getting parameters: {str(e)}")
            return {}
            
    def _on_strategy_changed(self, strategy_name: str):
        """Handle strategy selection change."""
        try:
            self._current_strategy = strategy_name
            self.strategy_changed.emit(strategy_name)
            
        except Exception as e:
            logger.error(f"Error handling strategy change: {str(e)}")
            
    def _on_parameter_changed(self, *args):
        """Handle parameter value change."""
        try:
            parameters = self.get_parameters()
            self.parameters_changed.emit(parameters)
            
        except Exception as e:
            logger.error(f"Error handling parameter change: {str(e)}")
            
    def _on_strategy_toggled(self, checked: bool):
        """Handle strategy start/stop toggle."""
        try:
            self.toggle_button.setText(
                "Stop Strategy" if checked else "Start Strategy"
            )
            self.strategy_toggled.emit(checked)
            
        except Exception as e:
            logger.error(f"Error handling strategy toggle: {str(e)}")
            
    def stop_strategy(self):
        """Stop the current strategy."""
        if self.toggle_button.isChecked():
            self.toggle_button.setChecked(False) 