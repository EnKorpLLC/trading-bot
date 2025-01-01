from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QLabel, QComboBox
)
from PyQt6.QtCore import Qt
import logging

logger = logging.getLogger(__name__)

class StrategyPanel(QWidget):
    def __init__(self, trading_engine):
        super().__init__()
        self.trading_engine = trading_engine
        self.init_ui()
        
    def init_ui(self):
        """Initialize the strategy panel UI."""
        layout = QVBoxLayout(self)
        
        # Strategy controls
        controls = QHBoxLayout()
        
        self.strategy_selector = QComboBox()
        self.strategy_selector.addItems([
            "FVG Strategy",
            "Breakout Strategy",
            "Supply Demand Strategy",
            "Scalping Strategy",
            "Fibonacci Strategy"
        ])
        
        self.activate_btn = QPushButton("Activate Strategy")
        self.activate_btn.clicked.connect(self.activate_strategy)
        
        controls.addWidget(QLabel("Select Strategy:"))
        controls.addWidget(self.strategy_selector)
        controls.addWidget(self.activate_btn)
        controls.addStretch()
        
        layout.addLayout(controls)
        
        # Strategy performance table
        self.performance_table = QTableWidget()
        self.performance_table.setColumnCount(6)
        self.performance_table.setHorizontalHeaderLabels([
            "Strategy", "Status", "Win Rate", "Total Trades",
            "Total Profit", "Last Updated"
        ])
        
        layout.addWidget(self.performance_table)
        
    def activate_strategy(self):
        """Activate the selected strategy."""
        strategy_name = self.strategy_selector.currentText()
        # TODO: Implement strategy activation
        logger.info(f"Activating strategy: {strategy_name}")
        
    def update_display(self):
        """Update the strategy performance display."""
        performance = self.trading_engine.strategy_manager.get_performance_report()
        
        self.performance_table.setRowCount(len(performance))
        
        for row, (name, metrics) in enumerate(performance.items()):
            self.performance_table.setItem(row, 0, QTableWidgetItem(name))
            self.performance_table.setItem(row, 1, QTableWidgetItem(
                "Active" if name in self.trading_engine.strategy_manager.strategies else "Inactive"
            ))
            self.performance_table.setItem(row, 2, QTableWidgetItem(f"{metrics['win_rate']:.2%}"))
            self.performance_table.setItem(row, 3, QTableWidgetItem(str(metrics['total_trades'])))
            self.performance_table.setItem(row, 4, QTableWidgetItem(f"${metrics['total_profit']:.2f}"))
            self.performance_table.setItem(row, 5, QTableWidgetItem(metrics['last_updated'])) 