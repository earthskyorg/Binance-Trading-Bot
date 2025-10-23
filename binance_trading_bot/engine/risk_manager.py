"""
Professional risk management system.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime, timedelta

from ..core.exceptions import RiskManagementError, InsufficientFundsError
from ..core.logging import get_logger


class RiskLevel(Enum):
    """Risk level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskMetrics:
    """Risk metrics data structure."""
    total_exposure: float
    max_drawdown: float
    daily_pnl: float
    position_count: int
    risk_score: float
    risk_level: RiskLevel


@dataclass
class PositionRisk:
    """Individual position risk assessment."""
    symbol: str
    position_size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    risk_percentage: float
    stop_loss_distance: float
    take_profit_distance: float


class RiskManager:
    """Professional risk management system."""
    
    def __init__(
        self,
        max_position_size: float = 0.1,  # 10% of account per position
        max_total_exposure: float = 0.5,  # 50% of account total exposure
        max_daily_loss: float = 0.05,  # 5% daily loss limit
        max_drawdown: float = 0.15,  # 15% max drawdown
        max_positions: int = 10,
        risk_free_rate: float = 0.02  # 2% risk-free rate
    ):
        self.max_position_size = max_position_size
        self.max_total_exposure = max_total_exposure
        self.max_daily_loss = max_daily_loss
        self.max_drawdown = max_drawdown
        self.max_positions = max_positions
        self.risk_free_rate = risk_free_rate
        
        self.logger = get_logger("risk_manager")
        self.daily_pnl_history: List[float] = []
        self.positions: Dict[str, PositionRisk] = {}
        self.account_balance: float = 0.0
        self.initial_balance: float = 0.0
        
    def set_account_balance(self, balance: float) -> None:
        """Set account balance."""
        if self.initial_balance == 0.0:
            self.initial_balance = balance
        self.account_balance = balance
    
    def add_position(self, position: PositionRisk) -> None:
        """Add a position to risk tracking."""
        self.positions[position.symbol] = position
        self.logger.info(
            f"Position added to risk tracking",
            extra={
                'symbol': position.symbol,
                'size': position.position_size,
                'entry_price': position.entry_price
            }
        )
    
    def remove_position(self, symbol: str) -> None:
        """Remove position from risk tracking."""
        if symbol in self.positions:
            del self.positions[symbol]
            self.logger.info(f"Position removed from risk tracking: {symbol}")
    
    def update_position(self, symbol: str, current_price: float) -> None:
        """Update position with current price."""
        if symbol in self.positions:
            position = self.positions[symbol]
            position.current_price = current_price
            position.unrealized_pnl = self._calculate_pnl(position)
            position.risk_percentage = abs(position.unrealized_pnl) / self.account_balance
    
    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss_price: float,
        risk_percentage: float = 0.02
    ) -> float:
        """Calculate appropriate position size based on risk management rules."""
        if entry_price <= 0 or stop_loss_price <= 0:
            raise RiskManagementError("Invalid price values")
        
        # Calculate risk per share
        risk_per_share = abs(entry_price - stop_loss_price)
        if risk_per_share == 0:
            raise RiskManagementError("Stop loss too close to entry price")
        
        # Calculate maximum risk amount
        max_risk_amount = self.account_balance * risk_percentage
        
        # Calculate position size
        position_size = max_risk_amount / risk_per_share
        
        # Apply position size limits
        max_position_value = self.account_balance * self.max_position_size
        max_position_size_by_value = max_position_value / entry_price
        
        # Use the smaller of the two limits
        final_position_size = min(position_size, max_position_size_by_value)
        
        # Ensure minimum position size
        min_position_size = 0.001  # Minimum position size
        if final_position_size < min_position_size:
            raise InsufficientFundsError("Position size too small")
        
        return final_position_size
    
    def check_risk_limits(self, new_position_size: float, symbol: str) -> Tuple[bool, List[str]]:
        """Check if new position violates risk limits."""
        violations = []
        
        # Check maximum position size
        position_value = new_position_size * self._get_current_price(symbol)
        if position_value > self.account_balance * self.max_position_size:
            violations.append(f"Position size exceeds maximum allowed ({self.max_position_size * 100}%)")
        
        # Check maximum total exposure
        current_exposure = self._calculate_total_exposure()
        new_exposure = current_exposure + position_value
        if new_exposure > self.account_balance * self.max_total_exposure:
            violations.append(f"Total exposure would exceed maximum allowed ({self.max_total_exposure * 100}%)")
        
        # Check maximum number of positions
        if len(self.positions) >= self.max_positions:
            violations.append(f"Maximum number of positions reached ({self.max_positions})")
        
        # Check daily loss limit
        daily_pnl = self._calculate_daily_pnl()
        if daily_pnl < -self.account_balance * self.max_daily_loss:
            violations.append(f"Daily loss limit exceeded ({self.max_daily_loss * 100}%)")
        
        # Check maximum drawdown
        current_drawdown = self._calculate_drawdown()
        if current_drawdown > self.max_drawdown:
            violations.append(f"Maximum drawdown exceeded ({self.max_drawdown * 100}%)")
        
        return len(violations) == 0, violations
    
    def calculate_risk_metrics(self) -> RiskMetrics:
        """Calculate comprehensive risk metrics."""
        total_exposure = self._calculate_total_exposure()
        daily_pnl = self._calculate_daily_pnl()
        drawdown = self._calculate_drawdown()
        
        # Calculate risk score (0-100)
        risk_score = self._calculate_risk_score(total_exposure, daily_pnl, drawdown)
        
        # Determine risk level
        if risk_score < 30:
            risk_level = RiskLevel.LOW
        elif risk_score < 60:
            risk_level = RiskLevel.MEDIUM
        elif risk_score < 80:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL
        
        return RiskMetrics(
            total_exposure=total_exposure,
            max_drawdown=drawdown,
            daily_pnl=daily_pnl,
            position_count=len(self.positions),
            risk_score=risk_score,
            risk_level=risk_level
        )
    
    def should_close_position(self, symbol: str) -> Tuple[bool, str]:
        """Determine if a position should be closed due to risk management."""
        if symbol not in self.positions:
            return False, "Position not found"
        
        position = self.positions[symbol]
        
        # Check if position has exceeded stop loss
        if position.unrealized_pnl < -self.account_balance * 0.02:  # 2% stop loss
            return True, "Stop loss triggered"
        
        # Check if position has reached take profit
        if position.unrealized_pnl > self.account_balance * 0.04:  # 4% take profit
            return True, "Take profit reached"
        
        # Check if position is too risky
        if position.risk_percentage > 0.05:  # 5% risk per position
            return True, "Position risk too high"
        
        return False, "Position within risk limits"
    
    def _calculate_total_exposure(self) -> float:
        """Calculate total exposure across all positions."""
        total = 0.0
        for position in self.positions.values():
            total += position.position_size * position.current_price
        return total
    
    def _calculate_daily_pnl(self) -> float:
        """Calculate daily P&L."""
        if not self.daily_pnl_history:
            return 0.0
        return sum(self.daily_pnl_history[-24:])  # Last 24 hours
    
    def _calculate_drawdown(self) -> float:
        """Calculate maximum drawdown."""
        if self.initial_balance == 0:
            return 0.0
        
        current_balance = self.account_balance + sum(
            pos.unrealized_pnl for pos in self.positions.values()
        )
        
        if current_balance >= self.initial_balance:
            return 0.0
        
        return (self.initial_balance - current_balance) / self.initial_balance
    
    def _calculate_risk_score(
        self,
        total_exposure: float,
        daily_pnl: float,
        drawdown: float
    ) -> float:
        """Calculate overall risk score (0-100)."""
        score = 0.0
        
        # Exposure score (0-30 points)
        exposure_ratio = total_exposure / self.account_balance if self.account_balance > 0 else 0
        score += min(30, exposure_ratio * 100)
        
        # Daily P&L score (0-30 points)
        if daily_pnl < 0:
            pnl_ratio = abs(daily_pnl) / self.account_balance if self.account_balance > 0 else 0
            score += min(30, pnl_ratio * 100)
        
        # Drawdown score (0-40 points)
        score += min(40, drawdown * 100)
        
        return min(100, score)
    
    def _calculate_pnl(self, position: PositionRisk) -> float:
        """Calculate P&L for a position."""
        if position.position_size > 0:  # Long position
            return (position.current_price - position.entry_price) * position.position_size
        else:  # Short position
            return (position.entry_price - position.current_price) * abs(position.position_size)
    
    def _get_current_price(self, symbol: str) -> float:
        """Get current price for symbol (placeholder)."""
        # This should be implemented to get real-time prices
        return 0.0
    
    def update_daily_pnl(self, pnl: float) -> None:
        """Update daily P&L history."""
        self.daily_pnl_history.append(pnl)
        
        # Keep only last 30 days of history
        if len(self.daily_pnl_history) > 720:  # 30 days * 24 hours
            self.daily_pnl_history = self.daily_pnl_history[-720:]
    
    def get_risk_report(self) -> Dict[str, Any]:
        """Generate comprehensive risk report."""
        metrics = self.calculate_risk_metrics()
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'account_balance': self.account_balance,
            'initial_balance': self.initial_balance,
            'total_exposure': metrics.total_exposure,
            'exposure_percentage': (metrics.total_exposure / self.account_balance * 100) if self.account_balance > 0 else 0,
            'daily_pnl': metrics.daily_pnl,
            'max_drawdown': metrics.max_drawdown,
            'position_count': metrics.position_count,
            'risk_score': metrics.risk_score,
            'risk_level': metrics.risk_level.value,
            'positions': [
                {
                    'symbol': pos.symbol,
                    'size': pos.position_size,
                    'entry_price': pos.entry_price,
                    'current_price': pos.current_price,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'risk_percentage': pos.risk_percentage
                }
                for pos in self.positions.values()
            ]
        }
