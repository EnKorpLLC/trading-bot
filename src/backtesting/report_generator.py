from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from pathlib import Path
from jinja2 import Template

logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_report(self, 
                       backtest_results: Dict,
                       strategy_name: str,
                       include_trades: bool = True) -> str:
        """Generate a comprehensive backtest report."""
        try:
            # Create report directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_dir = self.output_dir / f"{strategy_name}_{timestamp}"
            report_dir.mkdir(exist_ok=True)
            
            # Generate report components
            performance_plots = self._create_performance_plots(backtest_results)
            trade_analysis = self._create_trade_analysis(backtest_results) if include_trades else None
            risk_metrics = self._create_risk_metrics_table(backtest_results)
            
            # Generate HTML report
            html_report = self._generate_html_report(
                strategy_name=strategy_name,
                results=backtest_results,
                plots=performance_plots,
                trade_analysis=trade_analysis,
                risk_metrics=risk_metrics
            )
            
            # Save report files
            report_path = report_dir / "report.html"
            with open(report_path, 'w') as f:
                f.write(html_report)
                
            # Save raw results
            results_path = report_dir / "results.json"
            with open(results_path, 'w') as f:
                json.dump(backtest_results, f, indent=2, default=str)
                
            return str(report_path)
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            raise
            
    def _create_performance_plots(self, results: Dict) -> Dict[str, go.Figure]:
        """Create performance visualization plots."""
        plots = {}
        
        # Equity curve
        equity_fig = self._create_equity_curve(results['equity_curve'])
        plots['equity_curve'] = equity_fig
        
        # Monthly returns heatmap
        monthly_returns_fig = self._create_monthly_returns_heatmap(results['monthly_returns'])
        plots['monthly_returns'] = monthly_returns_fig
        
        # Drawdown chart
        drawdown_fig = self._create_drawdown_chart(results['equity_curve'])
        plots['drawdowns'] = drawdown_fig
        
        # Trade distribution
        trade_dist_fig = self._create_trade_distribution(results['trades'])
        plots['trade_distribution'] = trade_dist_fig
        
        return plots
        
    def _create_equity_curve(self, equity_data: pd.DataFrame) -> go.Figure:
        """Create equity curve plot."""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=equity_data.index,
            y=equity_data['equity'],
            name='Equity',
            line=dict(color='blue')
        ))
        
        fig.update_layout(
            title='Equity Curve',
            xaxis_title='Date',
            yaxis_title='Equity',
            showlegend=True
        )
        
        return fig
        
    def _create_monthly_returns_heatmap(self, monthly_returns: pd.Series) -> go.Figure:
        """Create monthly returns heatmap."""
        # Reshape data into year x month format
        monthly_data = monthly_returns.to_frame()
        monthly_data['year'] = monthly_data.index.year
        monthly_data['month'] = monthly_data.index.month
        pivot_data = monthly_data.pivot(index='year', columns='month', values=0)
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot_data.values,
            x=pivot_data.columns,
            y=pivot_data.index,
            colorscale='RdYlGn',
            text=np.round(pivot_data.values * 100, 1),
            texttemplate='%{text}%'
        ))
        
        fig.update_layout(
            title='Monthly Returns Heatmap',
            xaxis_title='Month',
            yaxis_title='Year'
        )
        
        return fig
        
    def _create_trade_analysis(self, results: Dict) -> Dict:
        """Create trade analysis summary."""
        trades_df = pd.DataFrame(results['trades'])
        
        analysis = {
            'total_trades': len(trades_df),
            'winning_trades': len(trades_df[trades_df['pnl'] > 0]),
            'losing_trades': len(trades_df[trades_df['pnl'] < 0]),
            'avg_trade_duration': trades_df['duration'].mean(),
            'best_trade': trades_df['pnl'].max(),
            'worst_trade': trades_df['pnl'].min(),
            'avg_profit_per_trade': trades_df['pnl'].mean(),
            'profit_factor': self._calculate_profit_factor(trades_df),
            'win_rate': len(trades_df[trades_df['pnl'] > 0]) / len(trades_df),
            'risk_reward_ratio': results['summary']['risk_reward_ratio']
        }
        
        return analysis
        
    def _generate_html_report(self, **kwargs) -> str:
        """Generate HTML report using template."""
        template_path = Path(__file__).parent / "templates" / "report_template.html"
        with open(template_path) as f:
            template = Template(f.read())
            
        return template.render(**kwargs)
        
    def _calculate_profit_factor(self, trades_df: pd.DataFrame) -> float:
        """Calculate profit factor from trades."""
        gross_profit = trades_df[trades_df['pnl'] > 0]['pnl'].sum()
        gross_loss = abs(trades_df[trades_df['pnl'] < 0]['pnl'].sum())
        return gross_profit / gross_loss if gross_loss != 0 else float('inf') 