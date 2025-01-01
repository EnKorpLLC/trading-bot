from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass
from pathlib import Path
import json
import threading
import time

logger = logging.getLogger(__name__)

@dataclass
class MetricPoint:
    timestamp: datetime
    value: float
    tags: Dict[str, str]

class MetricsCollector:
    def __init__(self):
        self.metrics_dir = Path("data/metrics")
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.metrics: Dict[str, List[MetricPoint]] = {}
        self.lock = threading.Lock()
        
        # Start metrics writer thread
        self.writer_thread = threading.Thread(
            target=self._metrics_writer_loop,
            daemon=True
        )
        self.writer_thread.start()
        
    def record_metric(self,
                     name: str,
                     value: float,
                     tags: Dict[str, str] = None):
        """Record a metric value."""
        try:
            with self.lock:
                if name not in self.metrics:
                    self.metrics[name] = []
                    
                metric = MetricPoint(
                    timestamp=datetime.now(),
                    value=value,
                    tags=tags or {}
                )
                
                self.metrics[name].append(metric)
                
        except Exception as e:
            logger.error(f"Error recording metric: {str(e)}")
            
    def get_metric_stats(self,
                        name: str,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> Dict:
        """Get statistics for a metric."""
        try:
            with self.lock:
                if name not in self.metrics:
                    return {}
                    
                # Filter metrics by time range
                metrics = self.metrics[name]
                if start_time:
                    metrics = [m for m in metrics if m.timestamp >= start_time]
                if end_time:
                    metrics = [m for m in metrics if m.timestamp <= end_time]
                    
                if not metrics:
                    return {}
                    
                values = [m.value for m in metrics]
                return {
                    'count': len(values),
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'last': values[-1]
                }
                
        except Exception as e:
            logger.error(f"Error getting metric stats: {str(e)}")
            return {}
            
    def get_performance_metrics(self) -> Dict:
        """Get trading performance metrics."""
        try:
            return {
                'win_rate': self.get_metric_stats('trade_win_rate'),
                'profit_factor': self.get_metric_stats('profit_factor'),
                'sharpe_ratio': self.get_metric_stats('sharpe_ratio'),
                'max_drawdown': self.get_metric_stats('max_drawdown'),
                'daily_pnl': self.get_metric_stats('daily_pnl')
            }
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {}
            
    def _metrics_writer_loop(self):
        """Periodically write metrics to disk."""
        while True:
            try:
                self._write_metrics()
            except Exception as e:
                logger.error(f"Error writing metrics: {str(e)}")
            time.sleep(60)  # Write every minute
            
    def _write_metrics(self):
        """Write metrics to disk."""
        with self.lock:
            for name, points in self.metrics.items():
                file_path = self.metrics_dir / f"{name}.json"
                
                # Convert to serializable format
                data = [
                    {
                        'timestamp': p.timestamp.isoformat(),
                        'value': p.value,
                        'tags': p.tags
                    }
                    for p in points
                ]
                
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2) 