from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QLabel, QHeaderView
)
from PyQt6.QtCore import Qt
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TradesPanel(QWidget):
    def __init__(self, trading_engine):
        super().__init__()
        self.trading_engine = trading_engine
        self.init_ui()
        
    def init_ui(self):
        """Initialize the trades panel UI."""
        layout = QVBoxLayout(self)
        
        # Create header with summary
        header = QHBoxLayout()
        self.total_trades_label = QLabel("Total Trades: 0")
        self.active_trades_label = QLabel("Active Trades: 0")
        self.total_profit_label = QLabel("Total Profit: $0.00")
        
        header.addWidget(self.total_trades_label)
        header.addWidget(self.active_trades_label)
        header.addWidget(self.total_profit_label)
        header.addStretch()
        
        # Add close all trades button
        close_all_btn = QPushButton("Close All Trades")
        close_all_btn.clicked.connect(self.close_all_trades)
        header.addWidget(close_all_btn)
        
        layout.addLayout(header)
        
        # Create trades table
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(8)
        self.trades_table.setHorizontalHeaderLabels([
            "ID", "Strategy", "Symbol", "Type", "Entry Price",
            "Current Price", "Profit/Loss", "Actions"
        ])
        
        # Set column stretching
        header = self.trades_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.trades_table)
        
    def update_display(self):
        """Update the trades display."""
        active_trades = self.trading_engine.active_trades
        self.trades_table.setRowCount(len(active_trades))
        
        total_profit = 0.0
        
        for row, (trade_id, trade) in enumerate(active_trades.items()):
            # Add trade details to table
            self.trades_table.setItem(row, 0, QTableWidgetItem(trade_id))
            self.trades_table.setItem(row, 1, QTableWidgetItem(trade['signal']['strategy']))
            self.trades_table.setItem(row, 2, QTableWidgetItem(trade['signal']['signal']['symbol']))
            self.trades_table.setItem(row, 3, QTableWidgetItem(trade['signal']['signal']['side']))
            self.trades_table.setItem(row, 4, QTableWidgetItem(f"${trade['signal']['signal']['entry_price']:.2f}"))
            
            # Calculate current profit/loss
            current_price = self.get_current_price(trade['signal']['signal']['symbol'])
            profit = self.calculate_profit(trade, current_price)
            total_profit += profit
            
            self.trades_table.setItem(row, 5, QTableWidgetItem(f"${current_price:.2f}"))
            self.trades_table.setItem(row, 6, QTableWidgetItem(f"${profit:.2f}"))
            
            # Add close button
            close_button = QPushButton("Close")
            close_button.clicked.connect(lambda checked, tid=trade_id: self.close_trade(tid))
            self.trades_table.setCellWidget(row, 7, close_button)
            
        # Update summary labels
        self.total_trades_label.setText(f"Total Trades: {self.trading_engine.strategy_manager.get_total_trades()}")
        self.active_trades_label.setText(f"Active Trades: {len(active_trades)}")
        self.total_profit_label.setText(f"Total Profit: ${total_profit:.2f}")
        
    def close_trade(self, trade_id: str):
        """Close a specific trade."""
        try:
            self.trading_engine.close_trade(trade_id)
            logger.info(f"Closed trade: {trade_id}")
        except Exception as e:
            logger.error(f"Error closing trade {trade_id}: {str(e)}")
            
    def close_all_trades(self):
        """Close all active trades."""
        try:
            for trade_id in list(self.trading_engine.active_trades.keys()):
                self.close_trade(trade_id)
            logger.info("Closed all trades")
        except Exception as e:
            logger.error(f"Error closing all trades: {str(e)}")
            
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol."""
        # TODO: Implement real price fetching
        return 0.0
        
    def calculate_profit(self, trade: dict, current_price: float) -> float:
        """Calculate current profit/loss for a trade."""
        entry_price = float(trade['signal']['signal']['entry_price'])
        position_size = float(trade['position_size'])
        side = trade['signal']['signal']['side']
        
        if side.lower() == 'buy':
            return (current_price - entry_price) * position_size
        else:
            return (entry_price - current_price) * position_size 