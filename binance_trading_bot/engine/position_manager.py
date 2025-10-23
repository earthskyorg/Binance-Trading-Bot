"""
Professional position management system.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

from ..core.exceptions import TradingError, OrderError
from ..core.logging import get_logger
from ..api.client import BinanceAPIClient
from .risk_manager import RiskManager, PositionRisk
from ..strategies.base import StrategyResult, SignalType


class PositionManager:
    """Professional position management system."""
    
    def __init__(
        self,
        api_client: BinanceAPIClient,
        risk_manager: RiskManager,
        dry_run: bool = False
    ):
        self.api_client = api_client
        self.risk_manager = risk_manager
        self.dry_run = dry_run
        
        self.logger = get_logger("position_manager")
        self.positions: Dict[str, Dict[str, Any]] = {}
    
    async def update_all_positions(self) -> None:
        """Update all tracked positions."""
        try:
            # Get current positions from API
            account_info = await self.api_client.get_account_info()
            
            for position_data in account_info.positions:
                symbol = position_data['symbol']
                position_size = float(position_data['positionAmt'])
                
                if abs(position_size) > 0:  # Only track non-zero positions
                    await self._update_position(symbol, position_data)
            
            # Check for positions that should be closed
            await self._check_position_closures()
            
        except Exception as e:
            self.logger.error(f"Error updating positions: {e}")
    
    async def _update_position(self, symbol: str, position_data: Dict[str, Any]) -> None:
        """Update a specific position."""
        try:
            position_size = float(position_data['positionAmt'])
            entry_price = float(position_data['entryPrice'])
            mark_price = float(position_data['markPrice'])
            unrealized_pnl = float(position_data['unRealizedProfit'])
            
            # Create or update position risk
            position_risk = PositionRisk(
                symbol=symbol,
                position_size=position_size,
                entry_price=entry_price,
                current_price=mark_price,
                unrealized_pnl=unrealized_pnl,
                risk_percentage=abs(unrealized_pnl) / self.risk_manager.account_balance,
                stop_loss_distance=0.0,  # Will be calculated based on strategy
                take_profit_distance=0.0
            )
            
            # Update in risk manager
            self.risk_manager.add_position(position_risk)
            
            # Update in position manager
            self.positions[symbol] = {
                'size': position_size,
                'entry_price': entry_price,
                'current_price': mark_price,
                'unrealized_pnl': unrealized_pnl,
                'side': 'LONG' if position_size > 0 else 'SHORT',
                'timestamp': datetime.utcnow()
            }
            
            self.logger.debug(
                f"Updated position for {symbol}",
                extra={
                    'symbol': symbol,
                    'size': position_size,
                    'entry_price': entry_price,
                    'current_price': mark_price,
                    'unrealized_pnl': unrealized_pnl
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error updating position for {symbol}: {e}")
    
    async def _check_position_closures(self) -> None:
        """Check if any positions should be closed."""
        try:
            for symbol in list(self.positions.keys()):
                should_close, reason = self.risk_manager.should_close_position(symbol)
                
                if should_close:
                    await self._close_position(symbol, reason)
            
        except Exception as e:
            self.logger.error(f"Error checking position closures: {e}")
    
    async def _close_position(self, symbol: str, reason: str) -> None:
        """Close a specific position."""
        try:
            if self.dry_run:
                self.logger.info(f"DRY RUN: Would close position for {symbol} - {reason}")
                return
            
            # Get current position size
            position = self.positions.get(symbol)
            if not position:
                self.logger.warning(f"Position not found for {symbol}")
                return
            
            position_size = position['size']
            side = 'SELL' if position_size > 0 else 'BUY'
            quantity = abs(position_size)
            
            # Place market order to close position
            order_result = await self.api_client.place_order(
                symbol=symbol,
                side=side,
                order_type='MARKET',
                quantity=quantity
            )
            
            # Remove from tracking
            if symbol in self.positions:
                del self.positions[symbol]
            
            self.risk_manager.remove_position(symbol)
            
            self.logger.info(
                f"Closed position for {symbol}",
                extra={
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                    'reason': reason,
                    'order_id': order_result.get('orderId')
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error closing position for {symbol}: {e}")
    
    async def open_position(
        self,
        symbol: str,
        signal_result: StrategyResult,
        market_data: Any
    ) -> Optional[Dict[str, Any]]:
        """Open a new position based on signal."""
        try:
            if self.dry_run:
                self.logger.info(f"DRY RUN: Would open position for {symbol}")
                return {'order_id': 'dry_run', 'status': 'FILLED'}
            
            # Calculate position size
            current_price = market_data.close[-1]
            stop_loss_price = self._calculate_stop_loss_price(
                signal_result, current_price
            )
            
            position_size = self.risk_manager.calculate_position_size(
                symbol=symbol,
                entry_price=current_price,
                stop_loss_price=stop_loss_price,
                risk_percentage=0.02  # 2% risk per trade
            )
            
            # Check risk limits
            is_valid, violations = self.risk_manager.check_risk_limits(
                position_size, symbol
            )
            
            if not is_valid:
                self.logger.warning(
                    f"Risk limits violated for {symbol}: {violations}"
                )
                return None
            
            # Determine order side
            side = 'BUY' if signal_result.signal == SignalType.BUY else 'SELL'
            
            # Place order
            order_result = await self.api_client.place_order(
                symbol=symbol,
                side=side,
                order_type='MARKET',
                quantity=position_size
            )
            
            # Track position
            self.positions[symbol] = {
                'size': position_size if side == 'BUY' else -position_size,
                'entry_price': current_price,
                'current_price': current_price,
                'unrealized_pnl': 0.0,
                'side': side,
                'timestamp': datetime.utcnow(),
                'order_id': order_result.get('orderId')
            }
            
            # Add to risk manager
            position_risk = PositionRisk(
                symbol=symbol,
                position_size=position_size if side == 'BUY' else -position_size,
                entry_price=current_price,
                current_price=current_price,
                unrealized_pnl=0.0,
                risk_percentage=0.0,
                stop_loss_distance=abs(current_price - stop_loss_price),
                take_profit_distance=0.0
            )
            self.risk_manager.add_position(position_risk)
            
            self.logger.info(
                f"Opened position for {symbol}",
                extra={
                    'symbol': symbol,
                    'side': side,
                    'size': position_size,
                    'entry_price': current_price,
                    'order_id': order_result.get('orderId'),
                    'confidence': signal_result.confidence
                }
            )
            
            return order_result
            
        except Exception as e:
            self.logger.error(f"Error opening position for {symbol}: {e}")
            return None
    
    def _calculate_stop_loss_price(
        self,
        signal_result: StrategyResult,
        current_price: float
    ) -> float:
        """Calculate stop loss price based on signal and strategy."""
        if signal_result.stop_loss:
            return signal_result.stop_loss
        
        # Default stop loss calculation (2% from entry)
        if signal_result.signal == SignalType.BUY:
            return current_price * 0.98  # 2% below entry
        else:
            return current_price * 1.02  # 2% above entry
    
    def get_position_summary(self) -> Dict[str, Any]:
        """Get summary of all positions."""
        total_pnl = sum(pos['unrealized_pnl'] for pos in self.positions.values())
        
        return {
            'total_positions': len(self.positions),
            'total_pnl': total_pnl,
            'positions': [
                {
                    'symbol': symbol,
                    'side': pos['side'],
                    'size': pos['size'],
                    'entry_price': pos['entry_price'],
                    'current_price': pos['current_price'],
                    'unrealized_pnl': pos['unrealized_pnl'],
                    'timestamp': pos['timestamp'].isoformat()
                }
                for symbol, pos in self.positions.items()
            ]
        }
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        try:
            # Get account info for current balance
            account_info = await self.api_client.get_account_info()
            
            # Calculate metrics
            total_pnl = sum(pos['unrealized_pnl'] for pos in self.positions.values())
            win_rate = self._calculate_win_rate()
            
            return {
                'current_balance': account_info.balance,
                'total_pnl': total_pnl,
                'win_rate': win_rate,
                'active_positions': len(self.positions),
                'risk_metrics': self.risk_manager.get_risk_report()
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {e}")
            return {}
    
    def _calculate_win_rate(self) -> float:
        """Calculate win rate based on position P&L."""
        if not self.positions:
            return 0.0
        
        profitable_positions = sum(
            1 for pos in self.positions.values()
            if pos['unrealized_pnl'] > 0
        )
        
        return profitable_positions / len(self.positions)
