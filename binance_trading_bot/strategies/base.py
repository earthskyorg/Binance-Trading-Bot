"""
Base strategy classes and interfaces.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import pandas as pd
import numpy as np


class SignalType(Enum):
    """Trading signal types."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class StrategyResult:
    """Result of a strategy calculation."""
    
    def __init__(
        self,
        signal: SignalType,
        confidence: float = 0.0,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.signal = signal
        self.confidence = confidence
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.metadata = metadata or {}
    
    def __repr__(self):
        return f"StrategyResult(signal={self.signal.value}, confidence={self.confidence})"


@dataclass
class MarketData:
    """Market data container."""
    symbol: str
    open: List[float]
    high: List[float]
    low: List[float]
    close: List[float]
    volume: List[float]
    timestamp: List[int]
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame."""
        return pd.DataFrame({
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'timestamp': self.timestamp
        })


class BaseStrategy(ABC):
    """Base class for all trading strategies."""
    
    def __init__(self, name: str, parameters: Optional[Dict[str, Any]] = None):
        self.name = name
        self.parameters = parameters or {}
        self.indicators = {}
        self._validate_parameters()
    
    @abstractmethod
    def calculate_indicators(self, data: MarketData) -> Dict[str, np.ndarray]:
        """Calculate technical indicators for the strategy."""
        pass
    
    @abstractmethod
    def generate_signal(self, data: MarketData, current_index: int) -> StrategyResult:
        """Generate trading signal based on current market data."""
        pass
    
    @abstractmethod
    def _validate_parameters(self) -> None:
        """Validate strategy parameters."""
        pass
    
    def get_required_buffer_size(self) -> int:
        """Get the required buffer size for this strategy."""
        return 200  # Default buffer size
    
    def update_indicators(self, data: MarketData) -> None:
        """Update indicators with new data."""
        self.indicators = self.calculate_indicators(data)
    
    def get_indicator_value(self, indicator_name: str, index: int) -> float:
        """Get indicator value at specific index."""
        if indicator_name not in self.indicators:
            raise ValueError(f"Indicator {indicator_name} not found")
        
        values = self.indicators[indicator_name]
        if index >= len(values) or index < 0:
            raise IndexError(f"Index {index} out of range for indicator {indicator_name}")
        
        return float(values[index])
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Get strategy parameter value."""
        return self.parameters.get(key, default)
    
    def set_parameter(self, key: str, value: Any) -> None:
        """Set strategy parameter value."""
        self.parameters[key] = value
        self._validate_parameters()


class RiskManagementMixin:
    """Mixin for risk management functionality."""
    
    def calculate_position_size(
        self,
        account_balance: float,
        risk_percentage: float,
        stop_loss_distance: float,
        price: float
    ) -> float:
        """Calculate position size based on risk management rules."""
        risk_amount = account_balance * (risk_percentage / 100)
        position_size = risk_amount / stop_loss_distance
        return min(position_size, account_balance * 0.1)  # Max 10% of account
    
    def calculate_stop_loss(
        self,
        entry_price: float,
        direction: SignalType,
        atr: float,
        multiplier: float = 2.0
    ) -> float:
        """Calculate stop loss based on ATR."""
        if direction == SignalType.BUY:
            return entry_price - (atr * multiplier)
        else:
            return entry_price + (atr * multiplier)
    
    def calculate_take_profit(
        self,
        entry_price: float,
        direction: SignalType,
        stop_loss: float,
        risk_reward_ratio: float = 2.0
    ) -> float:
        """Calculate take profit based on risk-reward ratio."""
        risk = abs(entry_price - stop_loss)
        reward = risk * risk_reward_ratio
        
        if direction == SignalType.BUY:
            return entry_price + reward
        else:
            return entry_price - reward


class TechnicalIndicatorsMixin:
    """Mixin for common technical indicators."""
    
    @staticmethod
    def sma(data: pd.Series, window: int) -> pd.Series:
        """Simple Moving Average."""
        return data.rolling(window=window).mean()
    
    @staticmethod
    def ema(data: pd.Series, window: int) -> pd.Series:
        """Exponential Moving Average."""
        return data.ewm(span=window).mean()
    
    @staticmethod
    def rsi(data: pd.Series, window: int = 14) -> pd.Series:
        """Relative Strength Index."""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACD indicator."""
        ema_fast = data.ewm(span=fast).mean()
        ema_slow = data.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def bollinger_bands(data: pd.Series, window: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Bollinger Bands."""
        sma = data.rolling(window=window).mean()
        std = data.rolling(window=window).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, sma, lower
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_window: int = 14, d_window: int = 3) -> Tuple[pd.Series, pd.Series]:
        """Stochastic Oscillator."""
        lowest_low = low.rolling(window=k_window).min()
        highest_high = high.rolling(window=k_window).max()
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_window).mean()
        return k_percent, d_percent
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
        """Average True Range."""
        high_low = high - low
        high_close_prev = (high - close.shift(1)).abs()
        low_close_prev = (low - close.shift(1)).abs()
        true_range = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
        return true_range.rolling(window=window).mean()
