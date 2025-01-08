from typing import Dict, List, Optional
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
    QToolBar, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor, QAction, QIcon
import pyqtgraph as pg
import numpy as np

from ..core.indicators import Indicator
from ..core.drawing_tools import DrawingTool

logger = logging.getLogger(__name__)

class AdvancedChart(QWidget):
    """Advanced chart widget with multiple timeframes and drawing tools."""
    
    # Signals
    timeframeChanged = pyqtSignal(str)
    symbolChanged = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
        self.current_timeframe = "15m"
        self.current_symbol = ""
        self.indicators: List[Indicator] = []
        self.drawing_tools: List[DrawingTool] = []
        self.is_drawing = False
        self.drawing_start_point = None
        
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the chart UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create toolbar
        toolbar = QToolBar()
        layout.addWidget(toolbar)
        
        # Symbol selector
        self.symbol_selector = QComboBox()
        self.symbol_selector.currentTextChanged.connect(self._on_symbol_changed)
        toolbar.addWidget(self.symbol_selector)
        
        # Timeframe selector
        self.timeframe_selector = QComboBox()
        self.timeframe_selector.addItems(self.timeframes)
        self.timeframe_selector.setCurrentText(self.current_timeframe)
        self.timeframe_selector.currentTextChanged.connect(self._on_timeframe_changed)
        toolbar.addWidget(self.timeframe_selector)
        
        toolbar.addSeparator()
        
        # Drawing tools
        self.line_tool = QAction(QIcon("assets/line.png"), "Line", self)
        self.line_tool.setCheckable(True)
        self.line_tool.triggered.connect(lambda: self._activate_drawing_tool("line"))
        toolbar.addAction(self.line_tool)
        
        self.fib_tool = QAction(QIcon("assets/fib.png"), "Fibonacci", self)
        self.fib_tool.setCheckable(True)
        self.fib_tool.triggered.connect(lambda: self._activate_drawing_tool("fibonacci"))
        toolbar.addAction(self.fib_tool)
        
        self.rect_tool = QAction(QIcon("assets/rect.png"), "Rectangle", self)
        self.rect_tool.setCheckable(True)
        self.rect_tool.triggered.connect(lambda: self._activate_drawing_tool("rectangle"))
        toolbar.addAction(self.rect_tool)
        
        toolbar.addSeparator()
        
        # Clear drawings button
        clear_btn = QAction(QIcon("assets/clear.png"), "Clear All", self)
        clear_btn.triggered.connect(self.clear_drawings)
        toolbar.addAction(clear_btn)
        
        # Create chart widget
        self.chart_widget = pg.PlotWidget()
        self.chart_widget.showGrid(x=True, y=True)
        self.chart_widget.setBackground('w')
        
        # Create price plot
        self.price_plot = self.chart_widget.plot(pen=pg.mkPen('b', width=2))
        
        # Create volume plot
        self.volume_plot = pg.PlotWidget()
        self.volume_plot.setBackground('w')
        self.volume_plot.setMaximumHeight(100)
        self.volume_bars = pg.BarGraphItem(x=[], height=[], width=0.8)
        self.volume_plot.addItem(self.volume_bars)
        
        # Create splitter for price and volume
        chart_layout = QVBoxLayout()
        chart_layout.setSpacing(0)
        chart_layout.addWidget(self.chart_widget)
        chart_layout.addWidget(self.volume_plot)
        
        chart_frame = QFrame()
        chart_frame.setLayout(chart_layout)
        layout.addWidget(chart_frame)
        
        # Connect mouse events
        self.chart_widget.scene().sigMouseClicked.connect(self._on_mouse_clicked)
        self.chart_widget.scene().sigMouseMoved.connect(self._on_mouse_moved)
        
    def set_available_symbols(self, symbols: List[str]):
        """Set available trading symbols."""
        try:
            self.symbol_selector.clear()
            self.symbol_selector.addItems(symbols)
            
            if symbols and not self.current_symbol:
                self.current_symbol = symbols[0]
                self.symbol_selector.setCurrentText(self.current_symbol)
                
        except Exception as e:
            logger.error(f"Error setting available symbols: {str(e)}")
            
    def update_data(self, data: Dict):
        """Update chart with new market data."""
        try:
            # Extract OHLCV data
            timestamps = np.array(data['timestamps'])
            opens = np.array(data['opens'])
            highs = np.array(data['highs'])
            lows = np.array(data['lows'])
            closes = np.array(data['closes'])
            volumes = np.array(data['volumes'])
            
            # Update price plot
            self.price_plot.setData(timestamps, closes)
            
            # Update volume plot
            self.volume_bars.setOpts(x=timestamps, height=volumes)
            
            # Update indicators
            self._update_indicators(data)
            
            # Auto-scale views
            self.chart_widget.autoRange()
            self.volume_plot.autoRange()
            
        except Exception as e:
            logger.error(f"Error updating chart data: {str(e)}")
            
    def add_indicator(self, indicator: Indicator):
        """Add a new indicator to the chart."""
        try:
            self.indicators.append(indicator)
            plot_item = self.chart_widget.plot(pen=pg.mkPen(indicator.color, width=1))
            indicator.set_plot_item(plot_item)
            
        except Exception as e:
            logger.error(f"Error adding indicator: {str(e)}")
            
    def clear_indicators(self):
        """Remove all indicators from the chart."""
        try:
            for indicator in self.indicators:
                self.chart_widget.removeItem(indicator.plot_item)
            self.indicators.clear()
            
        except Exception as e:
            logger.error(f"Error clearing indicators: {str(e)}")
            
    def add_drawing(self, drawing: DrawingTool):
        """Add a new drawing tool to the chart."""
        try:
            self.drawing_tools.append(drawing)
            self.chart_widget.addItem(drawing.get_plot_item())
                
        except Exception as e:
            logger.error(f"Error adding drawing: {str(e)}")
            
    def clear_drawings(self):
        """Remove all drawings from the chart."""
        try:
            for drawing in self.drawing_tools:
                self.chart_widget.removeItem(drawing.get_plot_item())
            self.drawing_tools.clear()
                
        except Exception as e:
            logger.error(f"Error clearing drawings: {str(e)}")
            
    def _update_indicators(self, data: Dict):
        """Update all indicators with new data."""
        try:
            for indicator in self.indicators:
                values = indicator.calculate(data)
                indicator.plot_item.setData(data['timestamps'], values)
                    
        except Exception as e:
            logger.error(f"Error updating indicators: {str(e)}")
            
    def _on_symbol_changed(self, symbol: str):
        """Handle symbol change."""
        try:
            self.current_symbol = symbol
            self.symbolChanged.emit(symbol)
                
        except Exception as e:
            logger.error(f"Error handling symbol change: {str(e)}")
            
    def _on_timeframe_changed(self, timeframe: str):
        """Handle timeframe change."""
        try:
            self.current_timeframe = timeframe
            self.timeframeChanged.emit(timeframe)
            
        except Exception as e:
            logger.error(f"Error handling timeframe change: {str(e)}")
            
    def _activate_drawing_tool(self, tool_type: str):
        """Activate a drawing tool."""
        try:
            # Deactivate all tools
            self.line_tool.setChecked(False)
            self.fib_tool.setChecked(False)
            self.rect_tool.setChecked(False)
            
            # Activate selected tool
            if tool_type == "line":
                self.line_tool.setChecked(True)
            elif tool_type == "fibonacci":
                self.fib_tool.setChecked(True)
            elif tool_type == "rectangle":
                self.rect_tool.setChecked(True)
                
            self.is_drawing = True
            self.drawing_start_point = None
                
        except Exception as e:
            logger.error(f"Error activating drawing tool: {str(e)}")
            
    def _on_mouse_clicked(self, event):
        """Handle mouse click events for drawing tools."""
        try:
            if not self.is_drawing:
                return
                
            pos = event.scenePos()
            point = self.chart_widget.plotItem.vb.mapSceneToView(pos)
            
            if self.drawing_start_point is None:
                # Start drawing
                self.drawing_start_point = point
            else:
                # Finish drawing
                if self.line_tool.isChecked():
                    drawing = DrawingTool.create_line(
                        self.drawing_start_point,
                        point
                    )
                elif self.fib_tool.isChecked():
                    drawing = DrawingTool.create_fibonacci(
                        self.drawing_start_point,
                        point
                    )
                elif self.rect_tool.isChecked():
                    drawing = DrawingTool.create_rectangle(
                        self.drawing_start_point,
                        point
                    )
                else:
                    drawing = None
                    
                if drawing:
                    self.add_drawing(drawing)
                    
                # Reset drawing state
                self.is_drawing = False
                self.drawing_start_point = None
                self.line_tool.setChecked(False)
                self.fib_tool.setChecked(False)
                self.rect_tool.setChecked(False)
                
        except Exception as e:
            logger.error(f"Error handling mouse click: {str(e)}")
            
    def _on_mouse_moved(self, pos):
        """Handle mouse move events for drawing preview."""
        try:
            if not self.is_drawing or self.drawing_start_point is None:
                return
                
            point = self.chart_widget.plotItem.vb.mapSceneToView(pos)
            
            # TODO: Implement drawing preview
                
        except Exception as e:
            logger.error(f"Error handling mouse move: {str(e)}") 