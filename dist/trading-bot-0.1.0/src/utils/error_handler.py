from typing import Dict, Optional, Type
import logging
import traceback
from datetime import datetime
from pathlib import Path
import json
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class ErrorContext:
    error_type: str
    message: str
    stack_trace: str
    timestamp: str
    severity: str
    component: str
    additional_info: Dict

class TradingError(Exception):
    def __init__(self, message: str, error_type: str = "TRADING_ERROR"):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)

class StrategyError(TradingError):
    def __init__(self, message: str):
        super().__init__(message, "STRATEGY_ERROR")

class ConnectionError(TradingError):
    def __init__(self, message: str):
        super().__init__(message, "CONNECTION_ERROR")

class ErrorHandler:
    def __init__(self):
        self.error_log_dir = Path("logs/errors")
        self.error_log_dir.mkdir(parents=True, exist_ok=True)
        self.recovery_strategies = {}
        self.error_callbacks = {}
        
    def handle_error(self, 
                    error: Exception,
                    component: str,
                    severity: str = "ERROR",
                    additional_info: Dict = None) -> bool:
        """Handle an error with appropriate recovery strategy."""
        try:
            # Create error context
            context = ErrorContext(
                error_type=type(error).__name__,
                message=str(error),
                stack_trace=traceback.format_exc(),
                timestamp=datetime.now().isoformat(),
                severity=severity,
                component=component,
                additional_info=additional_info or {}
            )
            
            # Log error
            self._log_error(context)
            
            # Execute error callbacks
            self._execute_callbacks(context)
            
            # Attempt recovery
            return self._attempt_recovery(context)
            
        except Exception as e:
            logger.critical(f"Error in error handler: {str(e)}")
            return False
            
    def register_recovery_strategy(self,
                                 error_type: Type[Exception],
                                 strategy: callable):
        """Register a recovery strategy for an error type."""
        self.recovery_strategies[error_type.__name__] = strategy
        
    def register_error_callback(self,
                              callback: callable,
                              error_types: List[Type[Exception]] = None):
        """Register a callback for error notifications."""
        for error_type in (error_types or [Exception]):
            if error_type.__name__ not in self.error_callbacks:
                self.error_callbacks[error_type.__name__] = set()
            self.error_callbacks[error_type.__name__].add(callback)
            
    def _log_error(self, context: ErrorContext):
        """Log error to file."""
        try:
            log_file = self.error_log_dir / f"errors_{datetime.now():%Y%m%d}.json"
            
            errors = []
            if log_file.exists():
                with open(log_file) as f:
                    errors = json.load(f)
                    
            errors.append(asdict(context))
            
            with open(log_file, 'w') as f:
                json.dump(errors, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error logging to file: {str(e)}")
            
    def _execute_callbacks(self, context: ErrorContext):
        """Execute registered error callbacks."""
        callbacks = self.error_callbacks.get(context.error_type, set())
        callbacks.update(self.error_callbacks.get(Exception.__name__, set()))
        
        for callback in callbacks:
            try:
                callback(context)
            except Exception as e:
                logger.error(f"Error in callback: {str(e)}")
                
    def _attempt_recovery(self, context: ErrorContext) -> bool:
        """Attempt to recover from error."""
        if strategy := self.recovery_strategies.get(context.error_type):
            try:
                return strategy(context)
            except Exception as e:
                logger.error(f"Error in recovery strategy: {str(e)}")
                return False
        return False 