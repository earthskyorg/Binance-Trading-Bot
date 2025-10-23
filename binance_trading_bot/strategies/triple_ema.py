"""
Triple EMA trading strategy.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from .base import BaseStrategy, StrategyResult, SignalType, MarketData, TechnicalIndicatorsMixin


class TripleEMAStrategy(BaseStrategy, TechnicalIndicatorsMixin):
    """Triple EMA crossover strategy."""
    
    def __init__(self, name: str = "tripleEMA", parameters: Optional[Dict[str, Any]] = None):
        default_params = {
            'fast_ema': 5,
            'medium_ema': 20,
            'slow_ema': 50,
            'min_candles': 4
        }
        if parameters:
            default_params.update(parameters)
        super().__init__(name, default_params)
    
    def _validate_parameters(self) -> None:
        """Validate strategy parameters."""
        fast = self.get_parameter('fast_ema')
        medium = self.get_parameter('medium_ema')
        slow = self.get_parameter('slow_ema')
        
        if not (fast < medium < slow):
            raise ValueError("EMA periods must be in ascending order: fast < medium < slow")
        
        if fast < 1 or medium < 1 or slow < 1:
            raise ValueError("EMA periods must be positive integers")
    
    def calculate_indicators(self, data: MarketData) -> Dict[str, np.ndarray]:
        """Calculate EMA indicators."""
        df = data.to_dataframe()
        close = df['close']
        
        fast_ema = self.get_parameter('fast_ema')
        medium_ema = self.get_parameter('medium_ema')
        slow_ema = self.get_parameter('slow_ema')
        
        return {
            'ema_fast': self.ema(close, fast_ema).values,
            'ema_medium': self.ema(close, medium_ema).values,
            'ema_slow': self.ema(close, slow_ema).values,
        }
    
    def generate_signal(self, data: MarketData, current_index: int) -> StrategyResult:
        """Generate trading signal based on triple EMA crossover."""
        if current_index < self.get_parameter('min_candles'):
            return StrategyResult(SignalType.HOLD, confidence=0.0)
        
        try:
            # Get current and previous values
            ema_fast = self.get_indicator_value('ema_fast', current_index)
            ema_medium = self.get_indicator_value('ema_medium', current_index)
            ema_slow = self.get_indicator_value('ema_slow', current_index)
            
            ema_fast_prev = self.get_indicator_value('ema_fast', current_index - 1)
            ema_medium_prev = self.get_indicator_value('ema_medium', current_index - 1)
            ema_slow_prev = self.get_indicator_value('ema_slow', current_index - 1)
            
            # Check for bearish crossover (sell signal)
            if (ema_fast_prev > ema_medium_prev and ema_fast_prev > ema_slow_prev and
                ema_fast < ema_medium and ema_fast < ema_slow):
                return StrategyResult(
                    SignalType.SELL,
                    confidence=0.8,
                    metadata={
                        'ema_fast': ema_fast,
                        'ema_medium': ema_medium,
                        'ema_slow': ema_slow,
                        'crossover_type': 'bearish'
                    }
                )
            
            # Check for bullish crossover (buy signal)
            elif (ema_fast_prev < ema_medium_prev and ema_fast_prev < ema_slow_prev and
                  ema_fast > ema_medium and ema_fast > ema_slow):
                return StrategyResult(
                    SignalType.BUY,
                    confidence=0.8,
                    metadata={
                        'ema_fast': ema_fast,
                        'ema_medium': ema_medium,
                        'ema_slow': ema_slow,
                        'crossover_type': 'bullish'
                    }
                )
            
            return StrategyResult(SignalType.HOLD, confidence=0.0)
            
        except (IndexError, ValueError) as e:
            return StrategyResult(SignalType.HOLD, confidence=0.0, metadata={'error': str(e)})
    
    def get_required_buffer_size(self) -> int:
        """Get required buffer size for this strategy."""
        return max(
            self.get_parameter('fast_ema'),
            self.get_parameter('medium_ema'),
            self.get_parameter('slow_ema')
        ) + 50
