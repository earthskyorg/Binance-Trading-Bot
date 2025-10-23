"""
Professional logging configuration for the trading bot.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
import json
from datetime import datetime
import colorlog


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra'):
            log_entry.update(record.extra)
            
        return json.dumps(log_entry)


def setup_logging(
    level: int = logging.INFO,
    log_to_file: bool = False,
    log_file_path: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Setup professional logging configuration.
    
    Args:
        level: Logging level
        log_to_file: Whether to log to file
        log_file_path: Path to log file
        max_file_size: Maximum log file size in bytes
        backup_count: Number of backup files to keep
        
    Returns:
        Configured logger
    """
    # Create logger
    logger = logging.getLogger("trading_bot")
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Color formatter for console
    color_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(color_formatter)
    logger.addHandler(console_handler)
    
    # File handler if requested
    if log_to_file and log_file_path:
        log_path = Path(log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        file_handler.setLevel(level)
        
        # Structured formatter for file
        file_formatter = StructuredFormatter()
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"trading_bot.{name}")


class TradeLogger:
    """Specialized logger for trade events."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_trade_signal(
        self,
        symbol: str,
        direction: str,
        price: float,
        strategy: str,
        **kwargs
    ):
        """Log a trade signal."""
        self.logger.info(
            f"Trade signal generated",
            extra={
                'event_type': 'trade_signal',
                'symbol': symbol,
                'direction': direction,
                'price': price,
                'strategy': strategy,
                **kwargs
            }
        )
    
    def log_trade_execution(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        order_id: str,
        **kwargs
    ):
        """Log trade execution."""
        self.logger.info(
            f"Trade executed",
            extra={
                'event_type': 'trade_execution',
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'order_id': order_id,
                **kwargs
            }
        )
    
    def log_trade_close(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        pnl: float,
        **kwargs
    ):
        """Log trade closure."""
        self.logger.info(
            f"Trade closed",
            extra={
                'event_type': 'trade_close',
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'pnl': pnl,
                **kwargs
            }
        )
    
    def log_error(
        self,
        error: Exception,
        context: str,
        **kwargs
    ):
        """Log an error with context."""
        self.logger.error(
            f"Error in {context}: {str(error)}",
            extra={
                'event_type': 'error',
                'error_type': type(error).__name__,
                'context': context,
                'error_message': str(error),
                **kwargs
            },
            exc_info=True
        )