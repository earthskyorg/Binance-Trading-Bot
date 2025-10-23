"""
Custom exceptions for the Binance Trading Bot.
"""


class TradingBotError(Exception):
    """Base exception for all trading bot errors."""
    pass


class ConfigurationError(TradingBotError):
    """Raised when there's a configuration error."""
    pass


class APIError(TradingBotError):
    """Raised when there's an API-related error."""
    pass


class TradingError(TradingBotError):
    """Raised when there's a trading-related error."""
    pass


class StrategyError(TradingBotError):
    """Raised when there's a strategy-related error."""
    pass


class DataError(TradingBotError):
    """Raised when there's a data-related error."""
    pass


class ValidationError(TradingBotError):
    """Raised when data validation fails."""
    pass


class ConnectionError(TradingBotError):
    """Raised when there's a connection error."""
    pass


class InsufficientFundsError(TradingError):
    """Raised when there are insufficient funds for a trade."""
    pass


class InvalidSymbolError(TradingError):
    """Raised when an invalid trading symbol is provided."""
    pass


class OrderError(TradingError):
    """Raised when there's an order-related error."""
    pass


class RiskManagementError(TradingError):
    """Raised when risk management rules are violated."""
    pass