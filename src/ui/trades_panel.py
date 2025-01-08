from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QMenu, QMessageBox, QLabel,
    QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QAction

logger = logging.getLogger(__name__)

class TradesPanel(QWidget):
    """Widget for displaying and managing positions and trades."""
    
    # Signals
    positionClosed = pyqtSignal(str)  # Position ID
    
    def __init__(self):
        super().__init__()
        self.positions: Dict[str, Dict] = {}  # Position ID -> Position details
        self.trades: List[Dict] = []  # List of completed trades
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tabs = QTabWidget()
        
        # Positions tab
        positions_tab = QWidget()
        positions_layout = QVBoxLayout(positions_tab)
        
        # Positions toolbar
        positions_toolbar = QHBoxLayout()
        
        close_all_btn = QPushButton("Close All")
        close_all_btn.clicked.connect(self._close_all_positions)
        positions_toolbar.addWidget(close_all_btn)
        
        positions_toolbar.addStretch()
        
        # Total P&L display
        self.total_pnl_label = QLabel("Total P&L: $0.00")
        positions_toolbar.addWidget(self.total_pnl_label)
        
        positions_layout.addLayout(positions_toolbar)
        
        # Positions table
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(8)
        self.positions_table.setHorizontalHeaderLabels([
            "Symbol",
            "Side",
            "Size",
            "Entry",
            "Current",
            "P&L",
            "P&L %",
            "Duration"
        ])
        
        # Set column resize modes
        header = self.positions_table.horizontalHeader()
        for i in range(8):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
            
        # Enable context menu
        self.positions_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.positions_table.customContextMenuRequested.connect(self._show_position_menu)
        
        positions_layout.addWidget(self.positions_table)
        
        tabs.addTab(positions_tab, "Positions")
        
        # Trades tab
        trades_tab = QWidget()
        trades_layout = QVBoxLayout(trades_tab)
        
        # Trades toolbar
        trades_toolbar = QHBoxLayout()
        
        trades_toolbar.addWidget(QLabel("Symbol:"))
        self.symbol_filter = QComboBox()
        trades_toolbar.addWidget(self.symbol_filter)
        
        trades_toolbar.addWidget(QLabel("Period:"))
        self.period_filter = QComboBox()
        self.period_filter.addItems(["All", "Today", "This Week", "This Month", "Custom"])
        trades_toolbar.addWidget(self.period_filter)
        
        trades_toolbar.addStretch()
        
        trades_layout.addLayout(trades_toolbar)
        
        # Trades table
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(9)
        self.trades_table.setHorizontalHeaderLabels([
            "Time",
            "Symbol",
            "Side",
            "Size",
            "Entry",
            "Exit",
            "P&L",
            "P&L %",
            "Duration"
        ])
        
        # Set column resize modes
        header = self.trades_table.horizontalHeader()
        for i in range(9):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
            
        trades_layout.addWidget(self.trades_table)
        
        tabs.addTab(trades_tab, "Trades")
        
        layout.addWidget(tabs)
        
    def update_position(self, position_id: str, position: Dict):
        """Update position details."""
        try:
            self.positions[position_id] = position
            self._update_positions_table()
            self._update_total_pnl()
            
        except Exception as e:
            logger.error(f"Error updating position: {str(e)}")
            
    def remove_position(self, position_id: str):
        """Remove position from display."""
        try:
            if position_id in self.positions:
                del self.positions[position_id]
                self._update_positions_table()
                self._update_total_pnl()
                
        except Exception as e:
            logger.error(f"Error removing position: {str(e)}")
            
    def add_trade(self, trade: Dict):
        """Add completed trade to history."""
        try:
            self.trades.append(trade)
            self._update_trades_table()
            
            # Update symbol filter if needed
            symbol = trade['symbol']
            if symbol not in [self.symbol_filter.itemText(i) for i in range(self.symbol_filter.count())]:
                self.symbol_filter.addItem(symbol)
                
        except Exception as e:
            logger.error(f"Error adding trade: {str(e)}")
            
    def clear(self):
        """Clear all positions and trades."""
        try:
            self.positions.clear()
            self.trades.clear()
            self._update_positions_table()
            self._update_trades_table()
            self._update_total_pnl()
            
        except Exception as e:
            logger.error(f"Error clearing trades panel: {str(e)}")
            
    def _update_positions_table(self):
        """Update positions table display."""
        try:
            self.positions_table.setRowCount(len(self.positions))
            
            for i, (position_id, position) in enumerate(self.positions.items()):
                # Symbol
                self.positions_table.setItem(i, 0, QTableWidgetItem(position['symbol']))
                
                # Side
                side_item = QTableWidgetItem(position['side'])
                if position['side'] == "Long":
                    side_item.setBackground(QColor(200, 255, 200))
                else:
                    side_item.setBackground(QColor(255, 200, 200))
                self.positions_table.setItem(i, 1, side_item)
                
                # Size
                size_item = QTableWidgetItem(f"{position['size']:.2f}")
                size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.positions_table.setItem(i, 2, size_item)
                
                # Entry price
                entry_item = QTableWidgetItem(f"{position['entry_price']:.5f}")
                entry_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.positions_table.setItem(i, 3, entry_item)
                
                # Current price
                current_item = QTableWidgetItem(f"{position['current_price']:.5f}")
                current_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.positions_table.setItem(i, 4, current_item)
                
                # P&L
                pnl = position['unrealized_pnl']
                pnl_item = QTableWidgetItem(f"${pnl:.2f}")
                pnl_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                if pnl > 0:
                    pnl_item.setBackground(QColor(200, 255, 200))
                elif pnl < 0:
                    pnl_item.setBackground(QColor(255, 200, 200))
                self.positions_table.setItem(i, 5, pnl_item)
                
                # P&L %
                pnl_pct = position['unrealized_pnl_pct']
                pnl_pct_item = QTableWidgetItem(f"{pnl_pct:.2f}%")
                pnl_pct_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                if pnl_pct > 0:
                    pnl_pct_item.setBackground(QColor(200, 255, 200))
                elif pnl_pct < 0:
                    pnl_pct_item.setBackground(QColor(255, 200, 200))
                self.positions_table.setItem(i, 6, pnl_pct_item)
                
                # Duration
                duration = datetime.now() - position['open_time']
                duration_str = str(duration).split('.')[0]  # Remove microseconds
                self.positions_table.setItem(i, 7, QTableWidgetItem(duration_str))
                
                # Store position ID as item data
                for col in range(8):
                    self.positions_table.item(i, col).setData(Qt.ItemDataRole.UserRole, position_id)
                    
        except Exception as e:
            logger.error(f"Error updating positions table: {str(e)}")
            
    def _update_trades_table(self):
        """Update trades table display."""
        try:
            # Apply filters
            filtered_trades = self.trades
            
            # Symbol filter
            symbol = self.symbol_filter.currentText()
            if symbol and symbol != "All":
                filtered_trades = [t for t in filtered_trades if t['symbol'] == symbol]
                
            # Period filter
            period = self.period_filter.currentText()
            if period != "All":
                now = datetime.now()
                if period == "Today":
                    filtered_trades = [
                        t for t in filtered_trades
                        if t['close_time'].date() == now.date()
                    ]
                elif period == "This Week":
                    start_of_week = now.date() - timedelta(days=now.weekday())
                    filtered_trades = [
                        t for t in filtered_trades
                        if t['close_time'].date() >= start_of_week
                    ]
                elif period == "This Month":
                    start_of_month = now.date().replace(day=1)
                    filtered_trades = [
                        t for t in filtered_trades
                        if t['close_time'].date() >= start_of_month
                    ]
                    
            # Update table
            self.trades_table.setRowCount(len(filtered_trades))
            
            for i, trade in enumerate(filtered_trades):
                # Time
                time_item = QTableWidgetItem(
                    trade['close_time'].strftime("%Y-%m-%d %H:%M:%S")
                )
                self.trades_table.setItem(i, 0, time_item)
                
                # Symbol
                self.trades_table.setItem(i, 1, QTableWidgetItem(trade['symbol']))
                
                # Side
                side_item = QTableWidgetItem(trade['side'])
                if trade['side'] == "Long":
                    side_item.setBackground(QColor(200, 255, 200))
                else:
                    side_item.setBackground(QColor(255, 200, 200))
                self.trades_table.setItem(i, 2, side_item)
                
                # Size
                size_item = QTableWidgetItem(f"{trade['size']:.2f}")
                size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.trades_table.setItem(i, 3, size_item)
                
                # Entry price
                entry_item = QTableWidgetItem(f"{trade['entry_price']:.5f}")
                entry_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.trades_table.setItem(i, 4, entry_item)
                
                # Exit price
                exit_item = QTableWidgetItem(f"{trade['exit_price']:.5f}")
                exit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.trades_table.setItem(i, 5, exit_item)
                
                # P&L
                pnl = trade['realized_pnl']
                pnl_item = QTableWidgetItem(f"${pnl:.2f}")
                pnl_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                if pnl > 0:
                    pnl_item.setBackground(QColor(200, 255, 200))
                elif pnl < 0:
                    pnl_item.setBackground(QColor(255, 200, 200))
                self.trades_table.setItem(i, 6, pnl_item)
                
                # P&L %
                pnl_pct = trade['realized_pnl_pct']
                pnl_pct_item = QTableWidgetItem(f"{pnl_pct:.2f}%")
                pnl_pct_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                if pnl_pct > 0:
                    pnl_pct_item.setBackground(QColor(200, 255, 200))
                elif pnl_pct < 0:
                    pnl_pct_item.setBackground(QColor(255, 200, 200))
                self.trades_table.setItem(i, 7, pnl_pct_item)
                
                # Duration
                duration = trade['close_time'] - trade['open_time']
                duration_str = str(duration).split('.')[0]  # Remove microseconds
                self.trades_table.setItem(i, 8, QTableWidgetItem(duration_str))
                
        except Exception as e:
            logger.error(f"Error updating trades table: {str(e)}")
            
    def _update_total_pnl(self):
        """Update total P&L display."""
        try:
            total_pnl = sum(p['unrealized_pnl'] for p in self.positions.values())
            self.total_pnl_label.setText(f"Total P&L: ${total_pnl:,.2f}")
            
            # Set color based on P&L
            if total_pnl > 0:
                self.total_pnl_label.setStyleSheet("color: green;")
            elif total_pnl < 0:
                self.total_pnl_label.setStyleSheet("color: red;")
            else:
                self.total_pnl_label.setStyleSheet("")
                
        except Exception as e:
            logger.error(f"Error updating total P&L: {str(e)}")
            
    def _show_position_menu(self, position):
        """Show context menu for positions table."""
        try:
            row = self.positions_table.rowAt(position.y())
            if row >= 0:
                position_id = self.positions_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                
                menu = QMenu(self)
                
                # Close position action
                close_action = QAction("Close Position", self)
                close_action.triggered.connect(lambda: self._close_position(position_id))
                menu.addAction(close_action)
                
                menu.exec(self.positions_table.mapToGlobal(position))
                
        except Exception as e:
            logger.error(f"Error showing position menu: {str(e)}")
            
    def _close_position(self, position_id: str):
        """Close selected position."""
        try:
            reply = QMessageBox.question(
                self,
                "Close Position",
                "Are you sure you want to close this position?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.positionClosed.emit(position_id)
                
        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
            
    def _close_all_positions(self):
        """Close all open positions."""
        try:
            if not self.positions:
                QMessageBox.information(
                    self,
                    "Close All Positions",
                    "No open positions to close."
                )
                return
                
            reply = QMessageBox.question(
                self,
                "Close All Positions",
                f"Are you sure you want to close {len(self.positions)} open positions?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                for position_id in list(self.positions.keys()):
                    self.positionClosed.emit(position_id)
                    
        except Exception as e:
            logger.error(f"Error closing all positions: {str(e)}") 