"""
Custom exceptions for the trading bot.
"""

from typing import Optional


class TradingBotError(Exception):
    """Base exception for all trading bot errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class ConfigurationError(TradingBotError):
    """Raised when there's a configuration error."""
    pass


class TradingError(TradingBotError):
    """Raised when there's a trading-related error."""
    
    def __init__(self, message: str, symbol: Optional[str] = None, error_code: Optional[str] = None):
        super().__init__(message, error_code)
        self.symbol = symbol


class ConnectionError(TradingBotError):
    """Raised when there's a connection error with Binance API."""
    pass


class AuthenticationError(TradingBotError):
    """Raised when there's an authentication error with Binance API."""
    pass


class InsufficientBalanceError(TradingError):
    """Raised when there's insufficient balance for a trade."""
    pass


class OrderError(TradingError):
    """Raised when there's an error with order placement or management."""
    
    def __init__(self, message: str, symbol: Optional[str] = None, 
                 order_id: Optional[str] = None, error_code: Optional[str] = None):
        super().__init__(message, symbol, error_code)
        self.order_id = order_id


class StrategyError(TradingBotError):
    """Raised when there's an error in strategy execution."""
    
    def __init__(self, message: str, strategy_name: Optional[str] = None):
        super().__init__(message)
        self.strategy_name = strategy_name
