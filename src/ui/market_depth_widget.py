from typing import Dict, List, Optional
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

logger = logging.getLogger(__name__)

class MarketDepthWidget(QWidget):
    """Widget for displaying market depth and liquidity."""
    
    def __init__(self):
        super().__init__()
        self.asks: List[Dict] = []
        self.bids: List[Dict] = []
        self.total_ask_volume = 0.0
        self.total_bid_volume = 0.0
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Ask volume
        ask_volume_layout = QHBoxLayout()
        ask_volume_layout.addWidget(QLabel("Ask Volume:"))
        self.ask_volume_label = QLabel("0.00")
        self.ask_volume_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        ask_volume_layout.addWidget(self.ask_volume_label)
        header_layout.addLayout(ask_volume_layout)
        
        header_layout.addStretch()
        
        # Bid volume
        bid_volume_layout = QHBoxLayout()
        bid_volume_layout.addWidget(QLabel("Bid Volume:"))
        self.bid_volume_label = QLabel("0.00")
        self.bid_volume_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        bid_volume_layout.addWidget(self.bid_volume_label)
        header_layout.addLayout(bid_volume_layout)
        
        layout.addLayout(header_layout)
        
        # Market depth table
        self.depth_table = QTableWidget()
        self.depth_table.setColumnCount(6)
        self.depth_table.setHorizontalHeaderLabels([
            "Ask Size",
            "Ask Price",
            "Ask Total",
            "Bid Total",
            "Bid Price",
            "Bid Size"
        ])
        
        # Set column resize modes
        header = self.depth_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.depth_table)
        
    def update_depth(self, asks: List[Dict], bids: List[Dict]):
        """Update market depth display."""
        try:
            self.asks = asks
            self.bids = bids
            
            # Calculate totals
            self.total_ask_volume = sum(ask['size'] for ask in asks)
            self.total_bid_volume = sum(bid['size'] for bid in bids)
            
            # Update volume labels
            self.ask_volume_label.setText(f"{self.total_ask_volume:,.2f}")
            self.bid_volume_label.setText(f"{self.total_bid_volume:,.2f}")
            
            # Update depth table
            max_rows = max(len(asks), len(bids))
            self.depth_table.setRowCount(max_rows)
            
            ask_total = 0.0
            bid_total = 0.0
            
            for i in range(max_rows):
                # Ask side
                if i < len(asks):
                    ask = asks[i]
                    ask_total += ask['size']
                    
                    # Size
                    size_item = QTableWidgetItem(f"{ask['size']:,.2f}")
                    size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                    self.depth_table.setItem(i, 0, size_item)
                    
                    # Price
                    price_item = QTableWidgetItem(f"{ask['price']:.5f}")
                    price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                    price_item.setBackground(QColor(255, 200, 200))
                    self.depth_table.setItem(i, 1, price_item)
                    
                    # Total
                    total_item = QTableWidgetItem(f"{ask_total:,.2f}")
                    total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                    self.depth_table.setItem(i, 2, total_item)
                else:
                    self.depth_table.setItem(i, 0, QTableWidgetItem(""))
                    self.depth_table.setItem(i, 1, QTableWidgetItem(""))
                    self.depth_table.setItem(i, 2, QTableWidgetItem(""))
                    
                # Bid side
                if i < len(bids):
                    bid = bids[i]
                    bid_total += bid['size']
                    
                    # Total
                    total_item = QTableWidgetItem(f"{bid_total:,.2f}")
                    total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                    self.depth_table.setItem(i, 3, total_item)
                    
                    # Price
                    price_item = QTableWidgetItem(f"{bid['price']:.5f}")
                    price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                    price_item.setBackground(QColor(200, 255, 200))
                    self.depth_table.setItem(i, 4, price_item)
                    
                    # Size
                    size_item = QTableWidgetItem(f"{bid['size']:,.2f}")
                    size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                    self.depth_table.setItem(i, 5, size_item)
                else:
                    self.depth_table.setItem(i, 3, QTableWidgetItem(""))
                    self.depth_table.setItem(i, 4, QTableWidgetItem(""))
                    self.depth_table.setItem(i, 5, QTableWidgetItem(""))
                    
        except Exception as e:
            logger.error(f"Error updating market depth: {str(e)}")
            
    def clear(self):
        """Clear market depth display."""
        try:
            self.asks.clear()
            self.bids.clear()
            self.total_ask_volume = 0.0
            self.total_bid_volume = 0.0
            
            self.ask_volume_label.setText("0.00")
            self.bid_volume_label.setText("0.00")
            
            self.depth_table.setRowCount(0)
            
        except Exception as e:
            logger.error(f"Error clearing market depth: {str(e)}") 