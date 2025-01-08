from typing import Dict, List, Optional
import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog,
    QFormLayout, QLineEdit, QComboBox, QDoubleSpinBox,
    QLabel, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

logger = logging.getLogger(__name__)

class Alert:
    """Trading alert configuration."""
    
    def __init__(
        self,
        symbol: str,
        condition: str,
        value: float,
        message: str,
        enabled: bool = True
    ):
        self.symbol = symbol
        self.condition = condition
        self.value = value
        self.message = message
        self.enabled = enabled
        self.triggered = False
        self.trigger_time: Optional[datetime] = None
        
    def check_condition(self, price: float) -> bool:
        """Check if alert condition is met."""
        if not self.enabled or self.triggered:
            return False
            
        if self.condition == "Above" and price > self.value:
            return True
        elif self.condition == "Below" and price < self.value:
            return True
        elif self.condition == "Equals" and abs(price - self.value) < 0.0001:
            return True
            
        return False
        
    def trigger(self):
        """Mark alert as triggered."""
        self.triggered = True
        self.trigger_time = datetime.now()
        
    def reset(self):
        """Reset alert state."""
        self.triggered = False
        self.trigger_time = None

class AlertDialog(QDialog):
    """Dialog for creating/editing alerts."""
    
    def __init__(self, symbols: List[str], alert: Optional[Alert] = None):
        super().__init__()
        self.symbols = symbols
        self.alert = alert
        self._init_ui()
        
    def _init_ui(self):
        """Initialize dialog UI."""
        self.setWindowTitle("Create Alert")
        layout = QFormLayout(self)
        
        # Symbol selector
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(self.symbols)
        if self.alert:
            self.symbol_combo.setCurrentText(self.alert.symbol)
        layout.addRow("Symbol:", self.symbol_combo)
        
        # Condition selector
        self.condition_combo = QComboBox()
        self.condition_combo.addItems(["Above", "Below", "Equals"])
        if self.alert:
            self.condition_combo.setCurrentText(self.alert.condition)
        layout.addRow("Condition:", self.condition_combo)
        
        # Value input
        self.value_spin = QDoubleSpinBox()
        self.value_spin.setRange(0, 1000000)
        self.value_spin.setDecimals(5)
        if self.alert:
            self.value_spin.setValue(self.alert.value)
        layout.addRow("Value:", self.value_spin)
        
        # Message input
        self.message_edit = QLineEdit()
        if self.alert:
            self.message_edit.setText(self.alert.message)
        layout.addRow("Message:", self.message_edit)
        
        # Enabled checkbox
        self.enabled_check = QCheckBox("Enabled")
        self.enabled_check.setChecked(True if not self.alert else self.alert.enabled)
        layout.addRow("", self.enabled_check)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addRow("", button_layout)
        
    def get_alert(self) -> Alert:
        """Get alert configuration from dialog."""
        return Alert(
            symbol=self.symbol_combo.currentText(),
            condition=self.condition_combo.currentText(),
            value=self.value_spin.value(),
            message=self.message_edit.text(),
            enabled=self.enabled_check.isChecked()
        )

class AlertSystem(QWidget):
    """Widget for managing and displaying trading alerts."""
    
    # Signals
    alertTriggered = pyqtSignal(str)  # Emits alert message
    
    def __init__(self):
        super().__init__()
        self.alerts: List[Alert] = []
        self.symbols: List[str] = []
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        add_btn = QPushButton("Add Alert")
        add_btn.clicked.connect(self._add_alert)
        toolbar.addWidget(add_btn)
        
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self._edit_alert)
        toolbar.addWidget(edit_btn)
        
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_alert)
        toolbar.addWidget(remove_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._clear_alerts)
        toolbar.addWidget(clear_btn)
        
        toolbar.addStretch()
        
        reset_btn = QPushButton("Reset Triggered")
        reset_btn.clicked.connect(self._reset_triggered)
        toolbar.addWidget(reset_btn)
        
        layout.addLayout(toolbar)
        
        # Alerts table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Symbol",
            "Condition",
            "Value",
            "Message",
            "Enabled",
            "Triggered",
            "Time"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.table)
        
    def set_available_symbols(self, symbols: List[str]):
        """Set available trading symbols."""
        self.symbols = symbols
        
    def add_alert(self, alert: Alert):
        """Add a new alert."""
        try:
            self.alerts.append(alert)
            self._update_table()
            
        except Exception as e:
            logger.error(f"Error adding alert: {str(e)}")
            
    def check_alerts(self, symbol: str, price: float):
        """Check alerts for a symbol."""
        try:
            for alert in self.alerts:
                if (
                    alert.symbol == symbol and
                    not alert.triggered and
                    alert.enabled and
                    alert.check_condition(price)
                ):
                    alert.trigger()
                    self.alertTriggered.emit(alert.message)
                    self._update_table()
                    
        except Exception as e:
            logger.error(f"Error checking alerts: {str(e)}")
            
    def _add_alert(self):
        """Show dialog to add new alert."""
        try:
            dialog = AlertDialog(self.symbols)
            if dialog.exec():
                self.add_alert(dialog.get_alert())
                
        except Exception as e:
            logger.error(f"Error adding alert: {str(e)}")
            
    def _edit_alert(self):
        """Edit selected alert."""
        try:
            row = self.table.currentRow()
            if row >= 0:
                alert = self.alerts[row]
                dialog = AlertDialog(self.symbols, alert)
                if dialog.exec():
                    self.alerts[row] = dialog.get_alert()
                    self._update_table()
                    
        except Exception as e:
            logger.error(f"Error editing alert: {str(e)}")
            
    def _remove_alert(self):
        """Remove selected alert."""
        try:
            row = self.table.currentRow()
            if row >= 0:
                del self.alerts[row]
                self._update_table()
                
        except Exception as e:
            logger.error(f"Error removing alert: {str(e)}")
            
    def _clear_alerts(self):
        """Remove all alerts."""
        try:
            self.alerts.clear()
            self._update_table()
            
        except Exception as e:
            logger.error(f"Error clearing alerts: {str(e)}")
            
    def _reset_triggered(self):
        """Reset all triggered alerts."""
        try:
            for alert in self.alerts:
                alert.reset()
            self._update_table()
            
        except Exception as e:
            logger.error(f"Error resetting alerts: {str(e)}")
            
    def _update_table(self):
        """Update alerts table."""
        try:
            self.table.setRowCount(len(self.alerts))
            
            for i, alert in enumerate(self.alerts):
                # Symbol
                self.table.setItem(i, 0, QTableWidgetItem(alert.symbol))
                
                # Condition
                self.table.setItem(i, 1, QTableWidgetItem(alert.condition))
                
                # Value
                value_item = QTableWidgetItem(f"{alert.value:.5f}")
                value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.table.setItem(i, 2, value_item)
                
                # Message
                self.table.setItem(i, 3, QTableWidgetItem(alert.message))
                
                # Enabled
                enabled_item = QTableWidgetItem("Yes" if alert.enabled else "No")
                enabled_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, 4, enabled_item)
                
                # Triggered
                triggered_item = QTableWidgetItem("Yes" if alert.triggered else "No")
                triggered_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if alert.triggered:
                    triggered_item.setBackground(QColor(255, 200, 200))
                self.table.setItem(i, 5, triggered_item)
                
                # Time
                time_str = (
                    alert.trigger_time.strftime("%Y-%m-%d %H:%M:%S")
                    if alert.trigger_time else ""
                )
                time_item = QTableWidgetItem(time_str)
                time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, 6, time_item)
                
            self.table.resizeColumnsToContents()
            
        except Exception as e:
            logger.error(f"Error updating table: {str(e)}") 