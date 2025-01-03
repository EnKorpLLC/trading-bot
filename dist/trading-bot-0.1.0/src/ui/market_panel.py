from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QLabel, QComboBox
)
from PyQt6.QtCore import Qt
import logging

logger = logging.getLogger(__name__)

class MarketPanel(QWidget):
    def __init__(self, trading_engine):
        super().__init__()
        self.trading_engine = trading_engine
        self.init_ui()
        
    def init_ui(self):
        """Initialize the market panel UI."""
        layout = QVBoxLayout(self)
        
        # Market selector
        controls = QHBoxLayout()
        
        self.market_selector = QComboBox()
        self.market_selector.currentTextChanged.connect(self.update_display)
        
        controls.addWidget(QLabel("Select Market:"))
        controls.addWidget(self.market_selector)
        controls.addStretch()
        
        layout.addLayout(controls)
        
        # Market analysis table
        self.analysis_table = QTableWidget()
        self.analysis_table.setColumnCount(5)
        self.analysis_table.setHorizontalHeaderLabels([
            "Metric", "Value", "Support Levels", "Resistance Levels", "Volume Profile"
        ])
        
        layout.addWidget(self.analysis_table)
        
    def update_display(self):
        """Update the market analysis display."""
        market = self.market_selector.currentText()
        if not market:
            return
            
        analysis = self.trading_engine.analyze_markets().get(market)
        if not analysis:
            return
            
        self.analysis_table.setRowCount(4)
        
        # Update analysis data
        self.analysis_table.setItem(0, 0, QTableWidgetItem("Trend"))
        self.analysis_table.setItem(0, 1, QTableWidgetItem(analysis.trend))
        
        self.analysis_table.setItem(1, 0, QTableWidgetItem("Volatility"))
        self.analysis_table.setItem(1, 1, QTableWidgetItem(f"{analysis.volatility:.2f}"))
        
        self.analysis_table.setItem(2, 0, QTableWidgetItem("Support Levels"))
        self.analysis_table.setItem(2, 1, QTableWidgetItem(
            ", ".join(f"{level:.2f}" for level in analysis.support_levels)
        ))
        
        self.analysis_table.setItem(3, 0, QTableWidgetItem("Resistance Levels"))
        self.analysis_table.setItem(3, 1, QTableWidgetItem(
            ", ".join(f"{level:.2f}" for level in analysis.resistance_levels)
        )) 