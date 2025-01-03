import logging
from typing import Dict, Optional
import json
from datetime import datetime
import os
from pathlib import Path

class TradeLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup trade logger
        self.trade_logger = logging.getLogger('trade_logger')
        self.trade_logger.setLevel(logging.INFO)
        
        # Create trade log file handler
        trade_log_file = self.log_dir / f"trades_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(trade_log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.trade_logger.addHandler(file_handler)
        
        # Setup performance logger
        self.performance_logger = logging.getLogger('performance_logger')
        self.performance_logger.setLevel(logging.INFO)
        
        # Create performance log file handler
        perf_log_file = self.log_dir / "performance.log"
        perf_handler = logging.FileHandler(perf_log_file)
        perf_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.performance_logger.addHandler(perf_handler)
        
        # Add system config logger
        self.config_logger = logging.getLogger('config_logger')
        self.config_logger.setLevel(logging.INFO)
        config_log_file = self.log_dir / "system_config.log"
        config_handler = logging.FileHandler(config_log_file)
        config_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.config_logger.addHandler(config_handler)
        
    def log_trade_signal(self, strategy_name: str, signal: Dict) -> None:
        """Log a trading signal."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'strategy': strategy_name,
            'signal': signal
        }
        self.trade_logger.info(f"Signal Generated: {json.dumps(log_entry)}")
        
    def log_trade_execution(self, strategy_name: str, trade_details: Dict) -> None:
        """Log trade execution details."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'strategy': strategy_name,
            'trade': trade_details
        }
        self.trade_logger.info(f"Trade Executed: {json.dumps(log_entry)}")
        
    def log_trade_result(self, strategy_name: str, result: Dict) -> None:
        """Log trade result."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'strategy': strategy_name,
            'result': result
        }
        self.trade_logger.info(f"Trade Result: {json.dumps(log_entry)}")
        self.performance_logger.info(f"Strategy Performance Update: {json.dumps(log_entry)}")
        
    def log_market_analysis(self, analysis: Dict) -> None:
        """Log market analysis results."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis
        }
        self.trade_logger.info(f"Market Analysis: {json.dumps(log_entry)}")
        
    def log_error(self, error_type: str, error_details: Dict) -> None:
        """Log error events."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'details': error_details
        }
        self.trade_logger.error(f"Error: {json.dumps(log_entry)}")
        
    def log_user_decision(self, decision_details: Dict) -> None:
        """Log user's trade confirmation decisions."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'user_decision',
            'details': decision_details
        }
        self.trade_logger.info(f"User Decision: {json.dumps(log_entry)}")
        
    def log_system_config(self, config: Dict) -> None:
        """Log system configuration changes."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'config_update',
            'config': config
        }
        self.config_logger.info(f"Config Update: {json.dumps(log_entry)}") 