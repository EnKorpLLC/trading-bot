from typing import Dict, List, Optional
import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                          QHeaderView, QLabel)
from PyQt5.QtCore import pyqtSignal, Qt

logger = logging.getLogger(__name__)

class TradeHistoryWidget(QWidget):
    """Widget for displaying trade history."""
    
    # Signals
    trade_selected = pyqtSignal(dict)  # Emitted when a trade is selected
    
    def __init__(self):
        """Initialize the trade history widget."""
        super().__init__()
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Create header
        header = QLabel("Trade History")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Time", "Symbol", "Type", "Size",
            "Entry", "Exit", "Profit/Loss"
        ])
        
        # Set column stretching
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        # Connect signals
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
        layout.addWidget(self.table)
        
    def update_trades(self, trades: List[Dict]):
        """Update the trade history display."""
        try:
            self.table.setRowCount(len(trades))
            
            for row, trade in enumerate(trades):
                # Time
                time_item = QTableWidgetItem(trade.get('close_time', ''))
                self.table.setItem(row, 0, time_item)
                
                # Symbol
                symbol_item = QTableWidgetItem(trade.get('symbol', ''))
                self.table.setItem(row, 1, symbol_item)
                
                # Type
                type_item = QTableWidgetItem(trade.get('type', '').upper())
                type_item.setForeground(
                    Qt.green if trade.get('type') == 'long' else Qt.red
                )
                self.table.setItem(row, 2, type_item)
                
                # Size
                size_item = QTableWidgetItem(f"{trade.get('size', 0):.2f}")
                self.table.setItem(row, 3, size_item)
                
                # Entry price
                entry_item = QTableWidgetItem(f"{trade.get('entry_price', 0):.5f}")
                self.table.setItem(row, 4, entry_item)
                
                # Exit price
                exit_item = QTableWidgetItem(f"{trade.get('exit_price', 0):.5f}")
                self.table.setItem(row, 5, exit_item)
                
                # Profit/Loss
                profit = trade.get('profit', 0)
                profit_item = QTableWidgetItem(f"${profit:.2f}")
                profit_item.setForeground(Qt.green if profit >= 0 else Qt.red)
                self.table.setItem(row, 6, profit_item)
                
                # Store trade data
                for col in range(7):
                    self.table.item(row, col).setData(Qt.UserRole, trade)
            
            # Sort by time (newest first)
            self.table.sortItems(0, Qt.DescendingOrder)
            
        except Exception as e:
            logger.error(f"Error updating trade history: {str(e)}")
    
    def _on_selection_changed(self):
        """Handle trade selection."""
        try:
            selected_items = self.table.selectedItems()
            if selected_items:
                # Get trade data from first selected item
                trade = selected_items[0].data(Qt.UserRole)
                if trade:
                    self.trade_selected.emit(trade)
                    
        except Exception as e:
            logger.error(f"Error handling trade selection: {str(e)}") 