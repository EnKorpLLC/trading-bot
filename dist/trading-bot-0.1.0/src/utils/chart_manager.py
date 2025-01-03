import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import mplfinance as mpf
from PyQt6.QtWidgets import QWidget, QVBoxLayout

class ChartManager:
    def __init__(self):
        self.style = mpf.make_mpf_style(
            base_mpf_style='charles',
            gridstyle='',
            y_on_right=True,
            marketcolors=mpf.make_marketcolors(
                up='green',
                down='red',
                edge='inherit',
                wick='inherit',
                volume='in'
            )
        )
        
    def create_candlestick_chart(self, 
                                data: pd.DataFrame, 
                                indicators: Optional[Dict] = None,
                                support_resistance: Optional[Dict] = None) -> Figure:
        """Create a candlestick chart with optional indicators."""
        # Create figure
        fig = Figure(figsize=(12, 8))
        ax1 = fig.add_subplot(111)
        
        # Plot candlesticks
        mpf.plot(data,
                 type='candle',
                 style=self.style,
                 ax=ax1,
                 volume=True)
                 
        # Add indicators if provided
        if indicators:
            for name, values in indicators.items():
                ax1.plot(data.index, values, label=name)
                
        # Add support/resistance levels if provided
        if support_resistance:
            for level_type, levels in support_resistance.items():
                color = 'g' if level_type == 'support' else 'r'
                for level in levels:
                    ax1.axhline(y=level, color=color, linestyle='--', alpha=0.5)
                    
        ax1.legend()
        fig.tight_layout()
        return fig
        
    def create_indicator_chart(self, 
                             data: pd.DataFrame,
                             indicator_name: str,
                             indicator_values: pd.Series) -> Figure:
        """Create a chart for a specific indicator."""
        fig = Figure(figsize=(12, 4))
        ax = fig.add_subplot(111)
        
        ax.plot(data.index, indicator_values, label=indicator_name)
        ax.set_title(indicator_name)
        ax.legend()
        
        fig.tight_layout()
        return fig

class ChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart_manager = ChartManager()
        self.init_ui()
        
    def init_ui(self):
        """Initialize the chart widget UI."""
        layout = QVBoxLayout(self)
        self.canvas = None
        self.setLayout(layout)
        
    def update_chart(self, 
                    data: pd.DataFrame,
                    chart_type: str = 'candlestick',
                    **kwargs):
        """Update the displayed chart."""
        if self.canvas:
            self.layout().removeWidget(self.canvas)
            
        if chart_type == 'candlestick':
            fig = self.chart_manager.create_candlestick_chart(data, **kwargs)
        else:
            fig = self.chart_manager.create_indicator_chart(
                data, chart_type, kwargs.get('indicator_values')
            )
            
        self.canvas = FigureCanvas(fig)
        self.layout().addWidget(self.canvas) 