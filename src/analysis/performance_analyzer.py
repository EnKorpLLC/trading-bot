from __future__ import annotations  # For Python 3.7+ forward compatibility
from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from dataclasses import dataclass
from pathlib import Path
import json
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_score, recall_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. Machine learning features disabled.")

logger = logging.getLogger(__name__)

@dataclass
class StrategyPerformance:
    """Data class for storing strategy performance metrics."""
    strategy_name: str
    win_rate: float
    profit_factor: float
    avg_return: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int

    @classmethod
    def from_dict(cls, data: Dict) -> StrategyPerformance:
        """Create instance from dictionary."""
        return cls(**data)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'strategy_name': self.strategy_name,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'avg_return': self.avg_return,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'total_trades': self.total_trades
        }

class SelfLearningAnalyzer:
    """Analyzer for self-learning trading system optimization."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize the analyzer.
        
        Args:
            data_dir: Directory for storing trading history and analysis data
        """
        self.data_dir = data_dir or Path("data/trading_history")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
    def analyze_performance(self, 
                          strategy_name: str,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> StrategyPerformance:
        """Analyze strategy performance.
        
        Args:
            strategy_name: Name of the strategy to analyze
            start_date: Start date for analysis period
            end_date: End date for analysis period
            
        Returns:
            StrategyPerformance metrics
        """
        try:
            # Load trading history
            df = self._load_trading_history()
            if df.empty:
                return None
                
            # Filter by date range if provided
            if start_date:
                df = df[df['entry_time'] >= start_date]
            if end_date:
                df = df[df['exit_time'] <= end_date]
                
            # Calculate metrics
            win_rate = len(df[df['pnl'] > 0]) / len(df)
            profit_factor = abs(df[df['pnl'] > 0]['pnl'].sum() / 
                              df[df['pnl'] < 0]['pnl'].sum())
            avg_return = df['pnl'].mean()
            
            # Calculate Sharpe ratio
            returns = df['pnl'] / df['position_size']
            sharpe_ratio = np.sqrt(252) * (returns.mean() / returns.std())
            
            # Calculate max drawdown
            cumulative = (1 + returns).cumprod()
            rolling_max = cumulative.expanding().max()
            drawdowns = (cumulative - rolling_max) / rolling_max
            max_drawdown = drawdowns.min()
            
            return StrategyPerformance(
                strategy_name=strategy_name,
                win_rate=win_rate,
                profit_factor=profit_factor,
                avg_return=avg_return,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                total_trades=len(df)
            )
            
        except Exception as e:
            logger.error(f"Error analyzing performance: {str(e)}")
            return None
            
    def train_model(self) -> bool:
        """Train the machine learning model on historical data."""
        try:
            df = self._load_trading_history()
            if df.empty:
                return False
                
            # Prepare features and target
            X = self._prepare_features(df)
            y = (df['pnl'] > 0).astype(int)  # 1 for profitable trades
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Train model
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)
            recall = recall_score(y_test, y_pred)
            
            logger.info(f"Model performance - Accuracy: {accuracy:.2f}, "
                       f"Precision: {precision:.2f}, Recall: {recall:.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            return False
            
    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for machine learning."""
        try:
            features = pd.DataFrame()
            
            # Market conditions
            features['volatility'] = df['entry_price'].rolling(20).std()
            features['trend'] = df['entry_price'].rolling(50).mean()
            
            # Trade characteristics
            features['position_size'] = df['position_size']
            features['holding_time'] = (df['exit_time'] - 
                                      df['entry_time']).dt.total_seconds()
            
            # Fill missing values
            features = features.fillna(method='ffill')
            
            return features
            
        except Exception as e:
            logger.error(f"Error preparing features: {str(e)}")
            return pd.DataFrame()
            
    def _load_trading_history(self) -> pd.DataFrame:
        """Load trading history from files."""
        try:
            history_files = list(self.data_dir.glob("trades_*.csv"))
            if not history_files:
                return pd.DataFrame()
                
            dfs = []
            for file in history_files:
                df = pd.read_csv(file, parse_dates=['entry_time', 'exit_time'])
                dfs.append(df)
                
            return pd.concat(dfs, ignore_index=True)
            
        except Exception as e:
            logger.error(f"Error loading trading history: {str(e)}")
            return pd.DataFrame() 