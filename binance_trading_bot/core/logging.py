"""
Professional logging system for the trading bot.
"""

import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json
import traceback

import colorlog
from colorlog import ColoredFormatter


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "getMessage"
            ]:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class TradingBotLogger:
    """Professional logger for the trading bot."""
    
    def __init__(self, 
                 name: str = "trading_bot",
                 level: int = logging.INFO,
                 log_to_file: bool = False,
                 log_file_path: Optional[str] = None,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5):
        """Initialize the logger.
        
        Args:
            name: Logger name
            level: Logging level
            log_to_file: Whether to log to file
            log_file_path: Path to log file
            max_file_size: Maximum file size before rotation
            backup_count: Number of backup files to keep
        """
        self.name = name
        self.level = level
        self.log_to_file = log_to_file
        self.log_file_path = log_file_path
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup the logger with handlers and formatters."""
        logger = logging.getLogger(self.name)
        logger.setLevel(self.level)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = ColoredFormatter(
            "%(log_color)s%(asctime)s %(levelname)-8s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "bold_white",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
            secondary_log_colors={
                "message": {
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red",
                }
            }
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler if enabled
        if self.log_to_file:
            file_handler = self._setup_file_handler()
            logger.addHandler(file_handler)
        
        return logger
    
    def _setup_file_handler(self) -> logging.Handler:
        """Setup file handler with rotation."""
        if self.log_file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = Path(f"trading_bot_{timestamp}.log")
        else:
            log_file = Path(self.log_file_path)
        
        # Create directory if it doesn't exist
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        
        # Use structured formatter for file logs
        file_formatter = StructuredFormatter()
        file_handler.setFormatter(file_formatter)
        
        return file_handler
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        self.logger.critical(message, extra=kwargs)
    
    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception with traceback."""
        self.logger.exception(message, extra=kwargs)
    
    def trade_signal(self, 
                     symbol: str, 
                     direction: str, 
                     price: float, 
                     **kwargs: Any) -> None:
        """Log trading signal."""
        self.info(
            f"Trading signal: {symbol} {direction} at {price}",
            symbol=symbol,
            direction=direction,
            price=price,
            event_type="trade_signal",
            **kwargs
        )
    
    def trade_opened(self,
                     symbol: str,
                     direction: str,
                     entry_price: float,
                     quantity: float,
                     order_id: str,
                     **kwargs: Any) -> None:
        """Log trade opening."""
        self.info(
            f"Trade opened: {symbol} {direction} {quantity} @ {entry_price}",
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            quantity=quantity,
            order_id=order_id,
            event_type="trade_opened",
            **kwargs
        )
    
    def trade_closed(self,
                     symbol: str,
                     direction: str,
                     exit_price: float,
                     pnl: float,
                     reason: str,
                     **kwargs: Any) -> None:
        """Log trade closing."""
        self.info(
            f"Trade closed: {symbol} {direction} @ {exit_price}, PnL: {pnl}, Reason: {reason}",
            symbol=symbol,
            direction=direction,
            exit_price=exit_price,
            pnl=pnl,
            reason=reason,
            event_type="trade_closed",
            **kwargs
        )
    
    def error_with_context(self,
                          message: str,
                          error: Exception,
                          context: Optional[Dict[str, Any]] = None,
                          **kwargs: Any) -> None:
        """Log error with additional context."""
        error_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
        }
        
        if context:
            error_context.update(context)
        
        self.error(message, **error_context, **kwargs)


def get_logger(name: str = "trading_bot") -> TradingBotLogger:
    """Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return TradingBotLogger(name)


# Global logger instance
logger = get_logger()
