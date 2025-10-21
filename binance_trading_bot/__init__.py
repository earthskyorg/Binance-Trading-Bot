"""
Professional Binance Trading Bot

A sophisticated cryptocurrency trading bot for Binance Futures with advanced
technical analysis capabilities, professional error handling, and comprehensive
monitoring features.
"""

__version__ = "2.0.0"
__author__ = "Professional Trading Bot Team"
__email__ = "contact@tradingbot.com"

from .core.bot import TradingBot
from .core.config import Config
from .core.exceptions import TradingBotError, ConfigurationError, TradingError

__all__ = [
    "TradingBot",
    "Config", 
    "TradingBotError",
    "ConfigurationError",
    "TradingError",
]
