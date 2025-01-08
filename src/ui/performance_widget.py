from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTabWidget, QFrame, QGridLayout, QComboBox,
    QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import pyqtgraph as pg
import numpy as np

logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """Container for trading performance metrics."""
    
    def __init__(self):
        # Account metrics
        self.initial_balance = 0.0
        self.current_balance = 0.0
        self.peak_balance = 0.0
        self.total_pnl = 0.0
        self.total_pnl_pct = 0.0
        self.max_drawdown = 0.0
        self.max_drawdown_pct = 0.0
        
        # Trade metrics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.win_rate = 0.0
        self.avg_win = 0.0
        self.avg_loss = 0.0
        self.profit_factor = 0.0
        self.risk_reward_ratio = 0.0
        
        # Risk metrics
        self.sharpe_ratio = 0.0
        self.sortino_ratio = 0.0
        self.max_consecutive_wins = 0
        self.max_consecutive_losses = 0
        self.avg_trade_duration = timedelta()
        self.avg_bars_in_trade = 0

class PerformanceWidget(QWidget):
    """Widget for displaying trading performance metrics and statistics."""
    
    def __init__(self):
        super().__init__()
        self.metrics = PerformanceMetrics()
        self.equity_curve = []
        self.drawdown_curve = []
        self.trade_history = []
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tabs = QTabWidget()
        
        # Overview tab
        overview_tab = QWidget()
        overview_layout = QVBoxLayout(overview_tab)
        
        # Metrics grid
        metrics_frame = QFrame()
        metrics_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        metrics_layout = QGridLayout(metrics_frame)
        
        # Account metrics
        metrics_layout.addWidget(QLabel("Account Metrics"), 0, 0, 1, 2)
        metrics_layout.addWidget(QLabel("Initial Balance:"), 1, 0)
        self.initial_balance_label = QLabel("$0.00")
        metrics_layout.addWidget(self.initial_balance_label, 1, 1)
        
        metrics_layout.addWidget(QLabel("Current Balance:"), 2, 0)
        self.current_balance_label = QLabel("$0.00")
        metrics_layout.addWidget(self.current_balance_label, 2, 1)
        
        metrics_layout.addWidget(QLabel("Total P&L:"), 3, 0)
        self.total_pnl_label = QLabel("$0.00 (0.00%)")
        metrics_layout.addWidget(self.total_pnl_label, 3, 1)
        
        metrics_layout.addWidget(QLabel("Max Drawdown:"), 4, 0)
        self.max_drawdown_label = QLabel("$0.00 (0.00%)")
        metrics_layout.addWidget(self.max_drawdown_label, 4, 1)
        
        # Trade metrics
        metrics_layout.addWidget(QLabel("Trade Metrics"), 5, 0, 1, 2)
        metrics_layout.addWidget(QLabel("Total Trades:"), 6, 0)
        self.total_trades_label = QLabel("0")
        metrics_layout.addWidget(self.total_trades_label, 6, 1)
        
        metrics_layout.addWidget(QLabel("Win Rate:"), 7, 0)
        self.win_rate_label = QLabel("0.00%")
        metrics_layout.addWidget(self.win_rate_label, 7, 1)
        
        metrics_layout.addWidget(QLabel("Profit Factor:"), 8, 0)
        self.profit_factor_label = QLabel("0.00")
        metrics_layout.addWidget(self.profit_factor_label, 8, 1)
        
        metrics_layout.addWidget(QLabel("Risk/Reward:"), 9, 0)
        self.risk_reward_label = QLabel("0.00")
        metrics_layout.addWidget(self.risk_reward_label, 9, 1)
        
        # Risk metrics
        metrics_layout.addWidget(QLabel("Risk Metrics"), 10, 0, 1, 2)
        metrics_layout.addWidget(QLabel("Sharpe Ratio:"), 11, 0)
        self.sharpe_ratio_label = QLabel("0.00")
        metrics_layout.addWidget(self.sharpe_ratio_label, 11, 1)
        
        metrics_layout.addWidget(QLabel("Sortino Ratio:"), 12, 0)
        self.sortino_ratio_label = QLabel("0.00")
        metrics_layout.addWidget(self.sortino_ratio_label, 12, 1)
        
        overview_layout.addWidget(metrics_frame)
        
        # Equity curve
        self.equity_plot = pg.PlotWidget()
        self.equity_plot.setBackground('w')
        self.equity_plot.showGrid(x=True, y=True)
        self.equity_plot.setLabel('left', 'Balance ($)')
        self.equity_plot.setLabel('bottom', 'Time')
        self.equity_curve_line = self.equity_plot.plot(pen=pg.mkPen('b', width=2))
        overview_layout.addWidget(self.equity_plot)
        
        # Drawdown chart
        self.drawdown_plot = pg.PlotWidget()
        self.drawdown_plot.setBackground('w')
        self.drawdown_plot.showGrid(x=True, y=True)
        self.drawdown_plot.setLabel('left', 'Drawdown (%)')
        self.drawdown_plot.setLabel('bottom', 'Time')
        self.drawdown_curve_line = self.drawdown_plot.plot(pen=pg.mkPen('r', width=2))
        overview_layout.addWidget(self.drawdown_plot)
        
        tabs.addTab(overview_tab, "Overview")
        
        # Trades tab
        trades_tab = QWidget()
        trades_layout = QVBoxLayout(trades_tab)
        
        # Trade filters
        filters_layout = QHBoxLayout()
        
        filters_layout.addWidget(QLabel("Symbol:"))
        self.symbol_filter = QComboBox()
        filters_layout.addWidget(self.symbol_filter)
        
        filters_layout.addWidget(QLabel("Period:"))
        self.period_filter = QComboBox()
        self.period_filter.addItems(["All", "Today", "This Week", "This Month", "Custom"])
        filters_layout.addWidget(self.period_filter)
        
        filters_layout.addStretch()
        trades_layout.addLayout(filters_layout)
        
        # Trades table
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(8)
        self.trades_table.setHorizontalHeaderLabels([
            "Time",
            "Symbol",
            "Type",
            "Entry",
            "Exit",
            "Size",
            "P&L",
            "Duration"
        ])
        self.trades_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        trades_layout.addWidget(self.trades_table)
        
        tabs.addTab(trades_tab, "Trades")
        
        layout.addWidget(tabs)
        
    def update_metrics(self, metrics: PerformanceMetrics):
        """Update performance metrics display."""
        try:
            # Update account metrics
            self.initial_balance_label.setText(f"${metrics.initial_balance:,.2f}")
            self.current_balance_label.setText(f"${metrics.current_balance:,.2f}")
            self.total_pnl_label.setText(
                f"${metrics.total_pnl:,.2f} ({metrics.total_pnl_pct:.2f}%)"
            )
            self.max_drawdown_label.setText(
                f"${metrics.max_drawdown:,.2f} ({metrics.max_drawdown_pct:.2f}%)"
            )
            
            # Update trade metrics
            self.total_trades_label.setText(str(metrics.total_trades))
            self.win_rate_label.setText(f"{metrics.win_rate:.2f}%")
            self.profit_factor_label.setText(f"{metrics.profit_factor:.2f}")
            self.risk_reward_label.setText(f"{metrics.risk_reward_ratio:.2f}")
            
            # Update risk metrics
            self.sharpe_ratio_label.setText(f"{metrics.sharpe_ratio:.2f}")
            self.sortino_ratio_label.setText(f"{metrics.sortino_ratio:.2f}")
            
        except Exception as e:
            logger.error(f"Error updating metrics: {str(e)}")
            
    def update_equity_curve(self, timestamps: List[datetime], balances: List[float]):
        """Update equity curve chart."""
        try:
            self.equity_curve_line.setData(
                x=[t.timestamp() for t in timestamps],
                y=balances
            )
            
        except Exception as e:
            logger.error(f"Error updating equity curve: {str(e)}")
            
    def update_drawdown_curve(self, timestamps: List[datetime], drawdowns: List[float]):
        """Update drawdown curve chart."""
        try:
            self.drawdown_curve_line.setData(
                x=[t.timestamp() for t in timestamps],
                y=drawdowns
            )
            
        except Exception as e:
            logger.error(f"Error updating drawdown curve: {str(e)}")
            
    def update_trades(self, trades: List[Dict]):
        """Update trades table."""
        try:
            self.trades_table.setRowCount(len(trades))
            
            for i, trade in enumerate(trades):
                # Time
                time_item = QTableWidgetItem(
                    trade['time'].strftime("%Y-%m-%d %H:%M:%S")
                )
                self.trades_table.setItem(i, 0, time_item)
                
                # Symbol
                self.trades_table.setItem(i, 1, QTableWidgetItem(trade['symbol']))
                
                # Type
                self.trades_table.setItem(i, 2, QTableWidgetItem(trade['type']))
                
                # Entry
                entry_item = QTableWidgetItem(f"{trade['entry_price']:.5f}")
                entry_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.trades_table.setItem(i, 3, entry_item)
                
                # Exit
                exit_item = QTableWidgetItem(f"{trade['exit_price']:.5f}")
                exit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.trades_table.setItem(i, 4, exit_item)
                
                # Size
                size_item = QTableWidgetItem(f"{trade['size']:.2f}")
                size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.trades_table.setItem(i, 5, size_item)
                
                # P&L
                pnl = trade['pnl']
                pnl_item = QTableWidgetItem(f"${pnl:.2f}")
                pnl_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                if pnl > 0:
                    pnl_item.setBackground(QColor(200, 255, 200))
                elif pnl < 0:
                    pnl_item.setBackground(QColor(255, 200, 200))
                self.trades_table.setItem(i, 6, pnl_item)
                
                # Duration
                duration = trade['duration']
                duration_str = str(duration).split('.')[0]  # Remove microseconds
                self.trades_table.setItem(i, 7, QTableWidgetItem(duration_str))
                
            self.trades_table.resizeColumnsToContents()
            
        except Exception as e:
            logger.error(f"Error updating trades table: {str(e)}")
            
    def set_available_symbols(self, symbols: List[str]):
        """Set available trading symbols."""
        try:
            self.symbol_filter.clear()
            self.symbol_filter.addItem("All")
            self.symbol_filter.addItems(symbols)
            
        except Exception as e:
            logger.error(f"Error setting available symbols: {str(e)}") 