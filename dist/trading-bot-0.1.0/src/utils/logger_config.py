import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import json
import sys
import traceback
from typing import Dict
import os

class ErrorTracker:
    def __init__(self):
        self.errors_dir = Path("logs/errors")
        self.errors_dir.mkdir(parents=True, exist_ok=True)
        self.current_errors: Dict[str, int] = {}  # Track error frequency
        
    def track_error(self, error_type: str, error_msg: str, stack_trace: str):
        """Track an error occurrence and save to file."""
        timestamp = datetime.now().isoformat()
        error_data = {
            'timestamp': timestamp,
            'type': error_type,
            'message': error_msg,
            'stack_trace': stack_trace
        }
        
        # Update error frequency
        self.current_errors[error_type] = self.current_errors.get(error_type, 0) + 1
        
        # Save error to file
        date_str = datetime.now().strftime('%Y%m%d')
        error_file = self.errors_dir / f"errors_{date_str}.json"
        
        try:
            if error_file.exists():
                with open(error_file, 'r') as f:
                    errors = json.load(f)
            else:
                errors = []
                
            errors.append(error_data)
            
            with open(error_file, 'w') as f:
                json.dump(errors, f, indent=2)
                
        except Exception as e:
            logging.error(f"Failed to save error data: {str(e)}")
            
    def get_error_summary(self) -> Dict:
        """Get summary of current errors."""
        return {
            'total_errors': sum(self.current_errors.values()),
            'error_types': self.current_errors,
            'last_check': datetime.now().isoformat()
        }

def setup_logging():
    """Configure logging system."""
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler for all logs
    general_log = logs_dir / "trade_locker.log"
    file_handler = logging.handlers.RotatingFileHandler(
        general_log,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    # File handler for errors only
    error_log = logs_dir / "errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log,
        maxBytes=10*1024*1024,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)
    
    # Create error tracker
    error_tracker = ErrorTracker()
    
    # Override excepthook to track uncaught exceptions
    def exception_handler(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions."""
        error_msg = str(exc_value)
        stack_trace = ''.join(traceback.format_tb(exc_traceback))
        
        # Track error
        error_tracker.track_error(
            exc_type.__name__,
            error_msg,
            stack_trace
        )
        
        # Log error
        logging.error(
            f"Uncaught {exc_type.__name__}: {error_msg}\n{stack_trace}"
        )
        
    sys.excepthook = exception_handler
    
    return error_tracker 