from typing import Optional
import logging
import logging.handlers
from pathlib import Path
import json
from datetime import datetime
import sys
import threading
from queue import Queue
import traceback
from dataclasses import dataclass, asdict

@dataclass
class LogRecord:
    timestamp: str
    level: str
    message: str
    module: str
    function: str
    line: int
    exception: Optional[str] = None
    extra: Optional[dict] = None

class AsyncLogHandler(logging.Handler):
    def __init__(self, log_dir: Path):
        super().__init__()
        self.log_dir = log_dir
        self.queue = Queue()
        self.worker = threading.Thread(target=self._process_logs, daemon=True)
        self.worker.start()
        
    def emit(self, record):
        try:
            # Convert to our log record format
            log_record = LogRecord(
                timestamp=datetime.fromtimestamp(record.created).isoformat(),
                level=record.levelname,
                message=record.getMessage(),
                module=record.module,
                function=record.funcName,
                line=record.lineno,
                exception=self._format_exception(record),
                extra=getattr(record, 'extra', None)
            )
            
            self.queue.put(log_record)
            
        except Exception:
            self.handleError(record)
            
    def _process_logs(self):
        while True:
            record = self.queue.get()
            self._write_log(record)
            
    def _write_log(self, record: LogRecord):
        try:
            # Determine log file based on date
            date_str = datetime.fromisoformat(record.timestamp).strftime('%Y%m%d')
            log_file = self.log_dir / f"trading_bot_{date_str}.json"
            
            # Append to log file
            with open(log_file, 'a') as f:
                json.dump(asdict(record), f)
                f.write('\n')
                
        except Exception as e:
            sys.stderr.write(f"Error writing log: {str(e)}\n")
            
    def _format_exception(self, record) -> Optional[str]:
        if record.exc_info:
            return ''.join(traceback.format_exception(*record.exc_info))
        return None

def setup_logging(log_dir: Optional[Path] = None):
    """Configure application logging."""
    log_dir = log_dir or Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)
    
    # File handler for JSON logs
    json_handler = AsyncLogHandler(log_dir)
    json_handler.setLevel(logging.DEBUG)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / "errors.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(console_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(json_handler)
    root_logger.addHandler(error_handler)
    
    # Log startup
    logging.info("Logging system initialized") 