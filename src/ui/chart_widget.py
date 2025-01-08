from typing import Dict, List, Optional, Tuple
import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSignal, Qt
import pyqtgraph as pg
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class ChartWidget(QWidget):
    """Widget for displaying price charts and technical indicators."""
    
    # Signals
    price_clicked = pyqtSignal(float, float)  # price, timestamp
    
    def __init__(self):
        """Initialize the chart widget."""
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setBackground('w')
        self.layout.addWidget(self.plot_widget)
        
        # Initialize plot items
        self.price_plot = None
        self.volume_plot = None
        self.indicator_plots = {}
        self.trade_markers = {}
        self.drawings = {}
        
        # Drawing state
        self.drawing_mode = None
        self.drawing_points = []
        
        # Set up mouse interaction
        self.plot_widget.scene().sigMouseClicked.connect(self._on_mouse_clicked)
        
        # Initialize data
        self.data = pd.DataFrame()
        self.last_price = 0.0
        
    def update_data(self, data: pd.DataFrame):
        """Update chart with new market data."""
        try:
            if data.empty:
                return
                
            self.data = data
            self._plot_price_data()
            self._plot_volume_data()
            self._update_indicators()
            
            # Update last known price
            self.last_price = float(data['close'].iloc[-1])
            
        except Exception as e:
            logger.error(f"Error updating chart data: {str(e)}")
    
    def _plot_price_data(self):
        """Plot price data as candlesticks."""
        try:
            if self.price_plot:
                self.plot_widget.removeItem(self.price_plot)
            
            # Create candlestick items
            candlestick_data = []
            for idx, row in self.data.iterrows():
                # Format: (timestamp, open, close, min, max)
                item = pg.CandlestickItem(
                    x=idx.timestamp(),
                    open=row['open'],
                    close=row['close'],
                    low=row['low'],
                    high=row['high']
                )
                candlestick_data.append(item)
            
            # Add candlesticks to plot
            for item in candlestick_data:
                self.plot_widget.addItem(item)
            
            self.price_plot = candlestick_data
            
        except Exception as e:
            logger.error(f"Error plotting price data: {str(e)}")
    
    def _plot_volume_data(self):
        """Plot volume data as bars."""
        try:
            if self.volume_plot:
                self.plot_widget.removeItem(self.volume_plot)
            
            # Create volume bars
            volume_data = self.data['volume'].values
            timestamps = [idx.timestamp() for idx in self.data.index]
            
            # Create bar graph
            self.volume_plot = pg.BarGraphItem(
                x=timestamps,
                height=volume_data,
                width=0.8,
                brush='b'
            )
            
            # Add to separate view box
            volume_view = self.plot_widget.addViewBox()
            volume_view.addItem(self.volume_plot)
            volume_view.setXLink(self.plot_widget.plotItem)
            
        except Exception as e:
            logger.error(f"Error plotting volume data: {str(e)}")
    
    def _update_indicators(self):
        """Update technical indicators."""
        try:
            # Clear existing indicators
            for plot in self.indicator_plots.values():
                self.plot_widget.removeItem(plot)
            self.indicator_plots.clear()
            
            # Calculate and plot indicators
            self._plot_moving_averages()
            self._plot_bollinger_bands()
            self._plot_rsi()
            self._plot_macd()
            
        except Exception as e:
            logger.error(f"Error updating indicators: {str(e)}")
    
    def _plot_moving_averages(self):
        """Plot moving averages."""
        try:
            # Calculate MAs
            ma20 = self.data['close'].rolling(window=20).mean()
            ma50 = self.data['close'].rolling(window=50).mean()
            
            # Create line plots
            timestamps = [idx.timestamp() for idx in self.data.index]
            
            self.indicator_plots['ma20'] = self.plot_widget.plot(
                timestamps, ma20.values,
                pen=pg.mkPen('b', width=1),
                name='MA(20)'
            )
            
            self.indicator_plots['ma50'] = self.plot_widget.plot(
                timestamps, ma50.values,
                pen=pg.mkPen('r', width=1),
                name='MA(50)'
            )
            
        except Exception as e:
            logger.error(f"Error plotting moving averages: {str(e)}")
    
    def _plot_bollinger_bands(self):
        """Plot Bollinger Bands."""
        try:
            # Calculate Bollinger Bands
            ma20 = self.data['close'].rolling(window=20).mean()
            std20 = self.data['close'].rolling(window=20).std()
            
            upper_band = ma20 + (std20 * 2)
            lower_band = ma20 - (std20 * 2)
            
            # Create line plots
            timestamps = [idx.timestamp() for idx in self.data.index]
            
            self.indicator_plots['bb_upper'] = self.plot_widget.plot(
                timestamps, upper_band.values,
                pen=pg.mkPen('g', width=1, style=Qt.DashLine),
                name='BB Upper'
            )
            
            self.indicator_plots['bb_middle'] = self.plot_widget.plot(
                timestamps, ma20.values,
                pen=pg.mkPen('g', width=1),
                name='BB Middle'
            )
            
            self.indicator_plots['bb_lower'] = self.plot_widget.plot(
                timestamps, lower_band.values,
                pen=pg.mkPen('g', width=1, style=Qt.DashLine),
                name='BB Lower'
            )
            
        except Exception as e:
            logger.error(f"Error plotting Bollinger Bands: {str(e)}")
    
    def _plot_rsi(self):
        """Plot RSI indicator."""
        try:
            # Calculate RSI
            delta = self.data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # Create separate view box for RSI
            rsi_view = self.plot_widget.addViewBox()
            rsi_view.setXLink(self.plot_widget.plotItem)
            rsi_view.setYRange(0, 100)
            
            # Create line plot
            timestamps = [idx.timestamp() for idx in self.data.index]
            
            rsi_plot = pg.PlotDataItem(
                timestamps, rsi.values,
                pen=pg.mkPen('m', width=1),
                name='RSI'
            )
            
            rsi_view.addItem(rsi_plot)
            self.indicator_plots['rsi'] = rsi_plot
            
        except Exception as e:
            logger.error(f"Error plotting RSI: {str(e)}")
    
    def _plot_macd(self):
        """Plot MACD indicator."""
        try:
            # Calculate MACD
            exp1 = self.data['close'].ewm(span=12, adjust=False).mean()
            exp2 = self.data['close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            histogram = macd - signal
            
            # Create separate view box for MACD
            macd_view = self.plot_widget.addViewBox()
            macd_view.setXLink(self.plot_widget.plotItem)
            
            # Create line plots
            timestamps = [idx.timestamp() for idx in self.data.index]
            
            self.indicator_plots['macd'] = pg.PlotDataItem(
                timestamps, macd.values,
                pen=pg.mkPen('b', width=1),
                name='MACD'
            )
            
            self.indicator_plots['macd_signal'] = pg.PlotDataItem(
                timestamps, signal.values,
                pen=pg.mkPen('r', width=1),
                name='Signal'
            )
            
            # Create histogram
            self.indicator_plots['macd_histogram'] = pg.BarGraphItem(
                x=timestamps,
                height=histogram.values,
                width=0.8,
                brush='g'
            )
            
            macd_view.addItem(self.indicator_plots['macd'])
            macd_view.addItem(self.indicator_plots['macd_signal'])
            macd_view.addItem(self.indicator_plots['macd_histogram'])
            
        except Exception as e:
            logger.error(f"Error plotting MACD: {str(e)}")
    
    def add_trade_marker(self, trade_id: str, timestamp: float, price: float, 
                        trade_type: str):
        """Add a marker for a trade on the chart."""
        try:
            if trade_id in self.trade_markers:
                self.plot_widget.removeItem(self.trade_markers[trade_id])
            
            # Create arrow marker
            color = 'g' if trade_type == 'long' else 'r'
            symbol = '↑' if trade_type == 'long' else '↓'
            
            marker = pg.TextItem(
                text=symbol,
                color=color,
                anchor=(0.5, 0.5)
            )
            
            marker.setPos(timestamp, price)
            self.plot_widget.addItem(marker)
            self.trade_markers[trade_id] = marker
            
        except Exception as e:
            logger.error(f"Error adding trade marker: {str(e)}")
    
    def clear_trade_markers(self):
        """Clear all trade markers from the chart."""
        try:
            for marker in self.trade_markers.values():
                self.plot_widget.removeItem(marker)
            self.trade_markers.clear()
            
        except Exception as e:
            logger.error(f"Error clearing trade markers: {str(e)}")
    
    def show_trade(self, trade: Dict):
        """Show a specific trade on the chart."""
        try:
            # Center view on trade
            timestamp = pd.Timestamp(trade['open_time']).timestamp()
            price = float(trade['open_price'])
            
            self.plot_widget.setXRange(
                timestamp - 3600,  # 1 hour before
                timestamp + 3600   # 1 hour after
            )
            
            # Highlight trade
            self.add_trade_marker(
                trade['id'],
                timestamp,
                price,
                trade['type']
            )
            
        except Exception as e:
            logger.error(f"Error showing trade: {str(e)}")
    
    def start_drawing(self, tool_type: str):
        """Start drawing mode with specified tool."""
        self.drawing_mode = tool_type
        self.drawing_points = []
    
    def stop_drawing(self):
        """Stop drawing mode."""
        self.drawing_mode = None
        self.drawing_points = []
    
    def clear_drawings(self):
        """Clear all drawings from the chart."""
        try:
            for drawing in self.drawings.values():
                self.plot_widget.removeItem(drawing)
            self.drawings.clear()
            
        except Exception as e:
            logger.error(f"Error clearing drawings: {str(e)}")
    
    def set_indicator_visibility(self, indicator: str, visible: bool):
        """Set visibility of a technical indicator."""
        try:
            if indicator in self.indicator_plots:
                self.indicator_plots[indicator].setVisible(visible)
                
        except Exception as e:
            logger.error(f"Error setting indicator visibility: {str(e)}")
    
    def _on_mouse_clicked(self, event):
        """Handle mouse click events."""
        try:
            # Get click position in plot coordinates
            pos = event.scenePos()
            if self.plot_widget.sceneBoundingRect().contains(pos):
                mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)
                
                if self.drawing_mode:
                    self._handle_drawing_click(mouse_point)
                else:
                    # Emit price clicked signal
                    self.price_clicked.emit(
                        float(mouse_point.y()),
                        float(mouse_point.x())
                    )
                    
        except Exception as e:
            logger.error(f"Error handling mouse click: {str(e)}")
    
    def _handle_drawing_click(self, point: Tuple[float, float]):
        """Handle clicks during drawing mode."""
        try:
            self.drawing_points.append(point)
            
            if self.drawing_mode == "trend_line":
                if len(self.drawing_points) == 2:
                    self._draw_trend_line()
                    self.stop_drawing()
                    
            elif self.drawing_mode == "horizontal_line":
                self._draw_horizontal_line(point)
                self.stop_drawing()
                
            elif self.drawing_mode == "fibonacci":
                if len(self.drawing_points) == 2:
                    self._draw_fibonacci_levels()
                    self.stop_drawing()
                    
        except Exception as e:
            logger.error(f"Error handling drawing click: {str(e)}")
    
    def _draw_trend_line(self):
        """Draw a trend line between two points."""
        try:
            if len(self.drawing_points) != 2:
                return
                
            line = pg.LineSegmentROI(
                positions=[
                    (self.drawing_points[0].x(), self.drawing_points[0].y()),
                    (self.drawing_points[1].x(), self.drawing_points[1].y())
                ],
                pen=pg.mkPen('y', width=1)
            )
            
            self.plot_widget.addItem(line)
            self.drawings[f"trend_line_{len(self.drawings)}"] = line
            
        except Exception as e:
            logger.error(f"Error drawing trend line: {str(e)}")
    
    def _draw_horizontal_line(self, point: Tuple[float, float]):
        """Draw a horizontal line at specified price level."""
        try:
            # Get x-axis range
            x_range = self.plot_widget.plotItem.vb.viewRange()[0]
            
            line = pg.InfiniteLine(
                pos=point.y(),
                angle=0,
                pen=pg.mkPen('y', width=1)
            )
            
            self.plot_widget.addItem(line)
            self.drawings[f"horizontal_line_{len(self.drawings)}"] = line
            
        except Exception as e:
            logger.error(f"Error drawing horizontal line: {str(e)}")
    
    def _draw_fibonacci_levels(self):
        """Draw Fibonacci retracement levels."""
        try:
            if len(self.drawing_points) != 2:
                return
                
            # Calculate price range
            high = max(self.drawing_points[0].y(), self.drawing_points[1].y())
            low = min(self.drawing_points[0].y(), self.drawing_points[1].y())
            price_range = high - low
            
            # Fibonacci levels
            levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
            
            # Draw lines at each level
            for level in levels:
                price = high - (price_range * level)
                line = pg.InfiniteLine(
                    pos=price,
                    angle=0,
                    pen=pg.mkPen('y', width=1, style=Qt.DashLine),
                    label=f"{level*100:.1f}%"
                )
                
                self.plot_widget.addItem(line)
                self.drawings[f"fib_{level}"] = line
                
        except Exception as e:
            logger.error(f"Error drawing Fibonacci levels: {str(e)}") 