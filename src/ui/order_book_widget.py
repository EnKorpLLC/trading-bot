from typing import Dict, List, Optional
import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QAction

logger = logging.getLogger(__name__)

class OrderBookWidget(QWidget):
    """Widget for displaying and managing orders."""
    
    # Signals
    orderCancelled = pyqtSignal(str)  # Order ID
    orderModified = pyqtSignal(str, Dict)  # Order ID, new parameters
    
    def __init__(self):
        super().__init__()
        self.orders: Dict[str, Dict] = {}  # Order ID -> Order details
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        cancel_all_btn = QPushButton("Cancel All")
        cancel_all_btn.clicked.connect(self._cancel_all_orders)
        toolbar.addWidget(cancel_all_btn)
        
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Orders table
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(8)
        self.orders_table.setHorizontalHeaderLabels([
            "Time",
            "Symbol",
            "Type",
            "Side",
            "Price",
            "Size",
            "Filled",
            "Status"
        ])
        
        # Set column resize modes
        header = self.orders_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        
        # Enable context menu
        self.orders_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.orders_table.customContextMenuRequested.connect(self._show_context_menu)
        
        layout.addWidget(self.orders_table)
        
    def update_order(self, order_id: str, order: Dict):
        """Update order details."""
        try:
            self.orders[order_id] = order
            self._update_table()
            
        except Exception as e:
            logger.error(f"Error updating order: {str(e)}")
            
    def remove_order(self, order_id: str):
        """Remove order from display."""
        try:
            if order_id in self.orders:
                del self.orders[order_id]
                self._update_table()
                
        except Exception as e:
            logger.error(f"Error removing order: {str(e)}")
            
    def clear(self):
        """Clear all orders."""
        try:
            self.orders.clear()
            self._update_table()
            
        except Exception as e:
            logger.error(f"Error clearing orders: {str(e)}")
            
    def _update_table(self):
        """Update orders table display."""
        try:
            self.orders_table.setRowCount(len(self.orders))
            
            for i, (order_id, order) in enumerate(self.orders.items()):
                # Time
                time_item = QTableWidgetItem(
                    order['time'].strftime("%Y-%m-%d %H:%M:%S")
                )
                self.orders_table.setItem(i, 0, time_item)
                
                # Symbol
                self.orders_table.setItem(i, 1, QTableWidgetItem(order['symbol']))
                
                # Type
                self.orders_table.setItem(i, 2, QTableWidgetItem(order['type']))
                
                # Side
                side_item = QTableWidgetItem(order['side'])
                if order['side'] == "Buy":
                    side_item.setBackground(QColor(200, 255, 200))
                else:
                    side_item.setBackground(QColor(255, 200, 200))
                self.orders_table.setItem(i, 3, side_item)
                
                # Price
                price_item = QTableWidgetItem(f"{order['price']:.5f}")
                price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.orders_table.setItem(i, 4, price_item)
                
                # Size
                size_item = QTableWidgetItem(f"{order['size']:.2f}")
                size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.orders_table.setItem(i, 5, size_item)
                
                # Filled
                filled = order.get('filled', 0)
                filled_pct = (filled / order['size']) * 100 if order['size'] > 0 else 0
                filled_item = QTableWidgetItem(f"{filled:.2f} ({filled_pct:.1f}%)")
                filled_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.orders_table.setItem(i, 6, filled_item)
                
                # Status
                status_item = QTableWidgetItem(order['status'])
                if order['status'] == "Filled":
                    status_item.setBackground(QColor(200, 255, 200))
                elif order['status'] == "Cancelled":
                    status_item.setBackground(QColor(255, 200, 200))
                elif order['status'] == "Rejected":
                    status_item.setBackground(QColor(255, 150, 150))
                self.orders_table.setItem(i, 7, status_item)
                
                # Store order ID as item data
                for col in range(8):
                    self.orders_table.item(i, col).setData(Qt.ItemDataRole.UserRole, order_id)
                
            self.orders_table.resizeColumnsToContents()
            
        except Exception as e:
            logger.error(f"Error updating table: {str(e)}")
            
    def _show_context_menu(self, position):
        """Show context menu for orders table."""
        try:
            row = self.orders_table.rowAt(position.y())
            if row >= 0:
                order_id = self.orders_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                order = self.orders[order_id]
                
                menu = QMenu(self)
                
                # Cancel order action
                if order['status'] not in ["Filled", "Cancelled", "Rejected"]:
                    cancel_action = QAction("Cancel Order", self)
                    cancel_action.triggered.connect(lambda: self._cancel_order(order_id))
                    menu.addAction(cancel_action)
                    
                    # Modify order action
                    modify_action = QAction("Modify Order", self)
                    modify_action.triggered.connect(lambda: self._modify_order(order_id))
                    menu.addAction(modify_action)
                    
                menu.exec(self.orders_table.mapToGlobal(position))
                
        except Exception as e:
            logger.error(f"Error showing context menu: {str(e)}")
            
    def _cancel_order(self, order_id: str):
        """Cancel selected order."""
        try:
            reply = QMessageBox.question(
                self,
                "Cancel Order",
                "Are you sure you want to cancel this order?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.orderCancelled.emit(order_id)
                
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            
    def _cancel_all_orders(self):
        """Cancel all active orders."""
        try:
            active_orders = [
                order_id for order_id, order in self.orders.items()
                if order['status'] not in ["Filled", "Cancelled", "Rejected"]
            ]
            
            if not active_orders:
                QMessageBox.information(
                    self,
                    "Cancel All Orders",
                    "No active orders to cancel."
                )
                return
                
            reply = QMessageBox.question(
                self,
                "Cancel All Orders",
                f"Are you sure you want to cancel {len(active_orders)} active orders?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                for order_id in active_orders:
                    self.orderCancelled.emit(order_id)
                    
        except Exception as e:
            logger.error(f"Error cancelling all orders: {str(e)}")
            
    def _modify_order(self, order_id: str):
        """Show dialog to modify order."""
        try:
            # TODO: Implement order modification dialog
            pass
            
        except Exception as e:
            logger.error(f"Error modifying order: {str(e)}") 