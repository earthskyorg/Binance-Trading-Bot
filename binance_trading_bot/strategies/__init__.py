"""
Trading strategies module.
"""

from .base import BaseStrategy, StrategyResult
from .registry import StrategyRegistry
from .stoch_rsi_macd import StochRSIMACDStrategy
from .triple_ema import TripleEMAStrategy
from .breakout import BreakoutStrategy
from .golden_cross import GoldenCrossStrategy
from .fibonacci_macd import FibonacciMACDStrategy

__all__ = [
    'BaseStrategy',
    'StrategyResult',
    'StrategyRegistry',
    'StochRSIMACDStrategy',
    'TripleEMAStrategy',
    'BreakoutStrategy',
    'GoldenCrossStrategy',
    'FibonacciMACDStrategy',
]
