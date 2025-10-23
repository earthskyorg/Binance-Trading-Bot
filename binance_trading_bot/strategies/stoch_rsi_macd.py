"""
Stochastic RSI with MACD strategy.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from .base import BaseStrategy, StrategyResult, SignalType, MarketData, TechnicalIndicatorsMixin


class StochRSIMACDStrategy(BaseStrategy, TechnicalIndicatorsMixin):
    """Stochastic RSI with MACD confirmation strategy."""
    
    def __init__(self, name: str = "StochRSIMACD", parameters: Optional[Dict[str, Any]] = None):
        default_params = {
            'rsi_period': 14,
            'stoch_k_period': 14,
            'stoch_d_period': 3,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'stoch_oversold': 20,
            'stoch_overbought': 80
        }
        if parameters:
            default_params.update(parameters)
        super().__init__(name, default_params)
    
    def _validate_parameters(self) -> None:
        """Validate strategy parameters."""
        rsi_period = self.get_parameter('rsi_period')
        stoch_k = self.get_parameter('stoch_k_period')
        stoch_d = self.get_parameter('stoch_d_period')
        
        if rsi_period < 2 or stoch_k < 2 or stoch_d < 1:
            raise ValueError("Periods must be positive integers")
        
        if stoch_d > stoch_k:
            raise ValueError("Stochastic D period must be <= K period")
    
    def calculate_indicators(self, data: MarketData) -> Dict[str, np.ndarray]:
        """Calculate technical indicators."""
        df = data.to_dataframe()
        close = df['close']
        high = df['high']
        low = df['low']
        
        # RSI
        rsi = self.rsi(close, self.get_parameter('rsi_period'))
        
        # Stochastic
        stoch_k, stoch_d = self.stochastic(
            high, low, close,
            self.get_parameter('stoch_k_period'),
            self.get_parameter('stoch_d_period')
        )
        
        # MACD
        macd_line, signal_line, histogram = self.macd(
            close,
            self.get_parameter('macd_fast'),
            self.get_parameter('macd_slow'),
            self.get_parameter('macd_signal')
        )
        
        return {
            'rsi': rsi.values,
            'stoch_k': stoch_k.values,
            'stoch_d': stoch_d.values,
            'macd': macd_line.values,
            'macd_signal': signal_line.values,
            'macd_histogram': histogram.values
        }
    
    def generate_signal(self, data: MarketData, current_index: int) -> StrategyResult:
        """Generate trading signal based on Stochastic RSI and MACD."""
        if current_index < 50:  # Need enough data for indicators
            return StrategyResult(SignalType.HOLD, confidence=0.0)
        
        try:
            # Get current values
            rsi = self.get_indicator_value('rsi', current_index)
            stoch_k = self.get_indicator_value('stoch_k', current_index)
            stoch_d = self.get_indicator_value('stoch_d', current_index)
            macd = self.get_indicator_value('macd', current_index)
            macd_signal = self.get_indicator_value('macd_signal', current_index)
            
            # Get previous values for crossover detection
            stoch_k_prev = self.get_indicator_value('stoch_k', current_index - 1)
            stoch_d_prev = self.get_indicator_value('stoch_d', current_index - 1)
            macd_prev = self.get_indicator_value('macd', current_index - 1)
            macd_signal_prev = self.get_indicator_value('macd_signal', current_index - 1)
            
            # Parameters
            rsi_oversold = self.get_parameter('rsi_oversold')
            rsi_overbought = self.get_parameter('rsi_overbought')
            stoch_oversold = self.get_parameter('stoch_oversold')
            stoch_overbought = self.get_parameter('stoch_overbought')
            
            # Buy signal conditions
            buy_conditions = [
                stoch_k < stoch_oversold and stoch_d < stoch_oversold,
                rsi > 50,  # RSI above middle
                macd > macd_signal and macd_prev < macd_signal_prev,  # MACD bullish crossover
                stoch_k > stoch_d and stoch_k_prev < stoch_d_prev  # Stochastic bullish crossover
            ]
            
            # Sell signal conditions
            sell_conditions = [
                stoch_k > stoch_overbought and stoch_d > stoch_overbought,
                rsi < 50,  # RSI below middle
                macd < macd_signal and macd_prev > macd_signal_prev,  # MACD bearish crossover
                stoch_k < stoch_d and stoch_k_prev > stoch_d_prev  # Stochastic bearish crossover
            ]
            
            # Calculate confidence based on number of conditions met
            buy_score = sum(buy_conditions)
            sell_score = sum(sell_conditions)
            
            if buy_score >= 3:
                confidence = min(0.9, 0.5 + (buy_score * 0.1))
                return StrategyResult(
                    SignalType.BUY,
                    confidence=confidence,
                    metadata={
                        'rsi': rsi,
                        'stoch_k': stoch_k,
                        'stoch_d': stoch_d,
                        'macd': macd,
                        'macd_signal': macd_signal,
                        'buy_score': buy_score,
                        'conditions_met': buy_conditions
                    }
                )
            elif sell_score >= 3:
                confidence = min(0.9, 0.5 + (sell_score * 0.1))
                return StrategyResult(
                    SignalType.SELL,
                    confidence=confidence,
                    metadata={
                        'rsi': rsi,
                        'stoch_k': stoch_k,
                        'stoch_d': stoch_d,
                        'macd': macd,
                        'macd_signal': macd_signal,
                        'sell_score': sell_score,
                        'conditions_met': sell_conditions
                    }
                )
            
            return StrategyResult(SignalType.HOLD, confidence=0.0)
            
        except (IndexError, ValueError) as e:
            return StrategyResult(SignalType.HOLD, confidence=0.0, metadata={'error': str(e)})
    
    def get_required_buffer_size(self) -> int:
        """Get required buffer size for this strategy."""
        return max(
            self.get_parameter('rsi_period'),
            self.get_parameter('stoch_k_period'),
            self.get_parameter('macd_slow')
        ) + 50
