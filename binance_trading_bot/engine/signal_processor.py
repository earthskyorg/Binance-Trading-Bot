"""
Professional signal processing system.
"""

from typing import Dict, Any, Optional
import asyncio

from ..core.exceptions import TradingError
from ..core.logging import get_logger, TradeLogger
from ..core.config import TradingConfig
from ..strategies.base import StrategyResult, SignalType
from .risk_manager import RiskManager
from .position_manager import PositionManager


class SignalProcessor:
    """Professional signal processing system."""
    
    def __init__(
        self,
        config: TradingConfig,
        risk_manager: RiskManager
    ):
        self.config = config
        self.risk_manager = risk_manager
        
        self.logger = get_logger("signal_processor")
        self.trade_logger = TradeLogger(self.logger)
        
        # Signal processing state
        self.last_signals: Dict[str, StrategyResult] = {}
        self.signal_history: Dict[str, list] = {}
        
        # Performance tracking
        self.signals_processed = 0
        self.signals_acted_upon = 0
    
    async def process_signal(
        self,
        symbol: str,
        signal_result: StrategyResult,
        market_data: Any
    ) -> Optional[Dict[str, Any]]:
        """Process a trading signal."""
        try:
            self.signals_processed += 1
            
            # Log signal
            self.trade_logger.log_trade_signal(
                symbol=symbol,
                direction=signal_result.signal.value,
                price=market_data.close[-1],
                strategy=self.config.strategy,
                confidence=signal_result.confidence,
                metadata=signal_result.metadata
            )
            
            # Store signal history
            if symbol not in self.signal_history:
                self.signal_history[symbol] = []
            
            self.signal_history[symbol].append({
                'timestamp': market_data.timestamp[-1],
                'signal': signal_result.signal.value,
                'confidence': signal_result.confidence,
                'price': market_data.close[-1]
            })
            
            # Keep only last 100 signals per symbol
            if len(self.signal_history[symbol]) > 100:
                self.signal_history[symbol] = self.signal_history[symbol][-100:]
            
            # Check if we should act on this signal
            if await self._should_act_on_signal(symbol, signal_result):
                result = await self._execute_signal(symbol, signal_result, market_data)
                if result:
                    self.signals_acted_upon += 1
                return result
            
            # Store last signal for comparison
            self.last_signals[symbol] = signal_result
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error processing signal for {symbol}: {e}")
            return None
    
    async def _should_act_on_signal(
        self,
        symbol: str,
        signal_result: StrategyResult
    ) -> bool:
        """Determine if we should act on a signal."""
        try:
            # Check minimum confidence threshold
            if signal_result.confidence < self.config.trading_threshold:
                self.logger.debug(
                    f"Signal confidence {signal_result.confidence} below threshold {self.config.trading_threshold} for {symbol}"
                )
                return False
            
            # Check if signal is different from last signal
            if symbol in self.last_signals:
                last_signal = self.last_signals[symbol]
                if (last_signal.signal == signal_result.signal and
                    abs(last_signal.confidence - signal_result.confidence) < 0.1):
                    self.logger.debug(f"Signal unchanged for {symbol}")
                    return False
            
            # Check risk limits
            risk_report = self.risk_manager.get_risk_report()
            if risk_report['risk_level'] in ['high', 'critical']:
                self.logger.warning(f"Risk level too high to act on signal for {symbol}")
                return False
            
            # Check if we already have a position for this symbol
            if symbol in self.risk_manager.positions:
                self.logger.debug(f"Already have position for {symbol}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking if should act on signal: {e}")
            return False
    
    async def _execute_signal(
        self,
        symbol: str,
        signal_result: StrategyResult,
        market_data: Any
    ) -> Optional[Dict[str, Any]]:
        """Execute a trading signal."""
        try:
            # This would typically involve calling the position manager
            # For now, we'll just log the execution
            
            self.logger.info(
                f"Executing signal for {symbol}",
                extra={
                    'symbol': symbol,
                    'signal': signal_result.signal.value,
                    'confidence': signal_result.confidence,
                    'price': market_data.close[-1]
                }
            )
            
            # In a real implementation, this would:
            # 1. Calculate position size based on risk management
            # 2. Place order through position manager
            # 3. Track the position
            
            return {
                'symbol': symbol,
                'signal': signal_result.signal.value,
                'confidence': signal_result.confidence,
                'price': market_data.close[-1],
                'timestamp': market_data.timestamp[-1]
            }
            
        except Exception as e:
            self.logger.error(f"Error executing signal for {symbol}: {e}")
            return None
    
    def get_signal_statistics(self) -> Dict[str, Any]:
        """Get signal processing statistics."""
        total_signals = sum(len(signals) for signals in self.signal_history.values())
        
        return {
            'signals_processed': self.signals_processed,
            'signals_acted_upon': self.signals_acted_upon,
            'action_rate': (
                self.signals_acted_upon / self.signals_processed
                if self.signals_processed > 0 else 0
            ),
            'total_signals': total_signals,
            'symbols_tracked': len(self.signal_history),
            'signals_per_symbol': {
                symbol: len(signals)
                for symbol, signals in self.signal_history.items()
            }
        }
    
    def get_signal_history(self, symbol: str, limit: int = 50) -> list:
        """Get signal history for a symbol."""
        if symbol not in self.signal_history:
            return []
        
        return self.signal_history[symbol][-limit:]
    
    def get_last_signal(self, symbol: str) -> Optional[StrategyResult]:
        """Get the last signal for a symbol."""
        return self.last_signals.get(symbol)
    
    def clear_signal_history(self, symbol: Optional[str] = None) -> None:
        """Clear signal history."""
        if symbol:
            if symbol in self.signal_history:
                del self.signal_history[symbol]
            if symbol in self.last_signals:
                del self.last_signals[symbol]
        else:
            self.signal_history.clear()
            self.last_signals.clear()
        
        self.logger.info(f"Cleared signal history for {symbol or 'all symbols'}")
    
    def get_signal_quality_metrics(self) -> Dict[str, Any]:
        """Get signal quality metrics."""
        try:
            quality_metrics = {}
            
            for symbol, signals in self.signal_history.items():
                if not signals:
                    continue
                
                # Calculate average confidence
                avg_confidence = sum(s['confidence'] for s in signals) / len(signals)
                
                # Calculate signal frequency
                if len(signals) > 1:
                    time_span = signals[-1]['timestamp'] - signals[0]['timestamp']
                    frequency = len(signals) / (time_span / 3600)  # signals per hour
                else:
                    frequency = 0
                
                # Calculate signal consistency
                signal_types = [s['signal'] for s in signals]
                buy_signals = signal_types.count('buy')
                sell_signals = signal_types.count('sell')
                consistency = max(buy_signals, sell_signals) / len(signals)
                
                quality_metrics[symbol] = {
                    'avg_confidence': avg_confidence,
                    'frequency': frequency,
                    'consistency': consistency,
                    'total_signals': len(signals),
                    'buy_signals': buy_signals,
                    'sell_signals': sell_signals
                }
            
            return quality_metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating signal quality metrics: {e}")
            return {}
