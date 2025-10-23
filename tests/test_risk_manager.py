"""
Comprehensive tests for risk management system.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from binance_trading_bot.engine.risk_manager import (
    RiskManager, RiskLevel, RiskMetrics, PositionRisk
)
from binance_trading_bot.core.exceptions import RiskManagementError, InsufficientFundsError


class TestRiskManager:
    """Test cases for RiskManager."""
    
    @pytest.fixture
    def risk_manager(self):
        """Create risk manager instance for testing."""
        return RiskManager(
            max_position_size=0.1,
            max_total_exposure=0.5,
            max_daily_loss=0.05,
            max_drawdown=0.15,
            max_positions=5
        )
    
    @pytest.fixture
    def sample_position(self):
        """Create sample position for testing."""
        return PositionRisk(
            symbol="BTCUSDT",
            position_size=0.1,
            entry_price=50000.0,
            current_price=51000.0,
            unrealized_pnl=100.0,
            risk_percentage=0.02,
            stop_loss_distance=1000.0,
            take_profit_distance=2000.0
        )
    
    def test_risk_manager_initialization(self, risk_manager):
        """Test risk manager initialization."""
        assert risk_manager.max_position_size == 0.1
        assert risk_manager.max_total_exposure == 0.5
        assert risk_manager.max_daily_loss == 0.05
        assert risk_manager.max_drawdown == 0.15
        assert risk_manager.max_positions == 5
        assert risk_manager.account_balance == 0.0
    
    def test_set_account_balance(self, risk_manager):
        """Test setting account balance."""
        risk_manager.set_account_balance(10000.0)
        assert risk_manager.account_balance == 10000.0
        assert risk_manager.initial_balance == 10000.0
        
        # Test updating balance
        risk_manager.set_account_balance(11000.0)
        assert risk_manager.account_balance == 11000.0
        assert risk_manager.initial_balance == 10000.0  # Should not change
    
    def test_add_position(self, risk_manager, sample_position):
        """Test adding position to risk tracking."""
        risk_manager.add_position(sample_position)
        
        assert sample_position.symbol in risk_manager.positions
        assert risk_manager.positions[sample_position.symbol] == sample_position
    
    def test_remove_position(self, risk_manager, sample_position):
        """Test removing position from risk tracking."""
        risk_manager.add_position(sample_position)
        assert sample_position.symbol in risk_manager.positions
        
        risk_manager.remove_position(sample_position.symbol)
        assert sample_position.symbol not in risk_manager.positions
    
    def test_update_position(self, risk_manager, sample_position):
        """Test updating position with current price."""
        risk_manager.add_position(sample_position)
        
        # Update with new price
        new_price = 52000.0
        risk_manager.update_position(sample_position.symbol, new_price)
        
        updated_position = risk_manager.positions[sample_position.symbol]
        assert updated_position.current_price == new_price
        assert updated_position.unrealized_pnl == 200.0  # (52000 - 50000) * 0.1
    
    def test_calculate_position_size(self, risk_manager):
        """Test position size calculation."""
        risk_manager.set_account_balance(10000.0)
        
        # Test normal position size calculation
        position_size = risk_manager.calculate_position_size(
            symbol="BTCUSDT",
            entry_price=50000.0,
            stop_loss_price=49000.0,
            risk_percentage=0.02
        )
        
        expected_size = (10000.0 * 0.02) / 1000.0  # Risk amount / risk per share
        assert position_size == expected_size
    
    def test_calculate_position_size_invalid_prices(self, risk_manager):
        """Test position size calculation with invalid prices."""
        risk_manager.set_account_balance(10000.0)
        
        with pytest.raises(RiskManagementError):
            risk_manager.calculate_position_size(
                symbol="BTCUSDT",
                entry_price=0.0,
                stop_loss_price=49000.0,
                risk_percentage=0.02
            )
        
        with pytest.raises(RiskManagementError):
            risk_manager.calculate_position_size(
                symbol="BTCUSDT",
                entry_price=50000.0,
                stop_loss_price=50000.0,  # Same as entry price
                risk_percentage=0.02
            )
    
    def test_check_risk_limits_valid(self, risk_manager):
        """Test risk limit checking with valid position."""
        risk_manager.set_account_balance(10000.0)
        
        is_valid, violations = risk_manager.check_risk_limits(0.05, "BTCUSDT")
        
        assert is_valid
        assert len(violations) == 0
    
    def test_check_risk_limits_position_size_exceeded(self, risk_manager):
        """Test risk limit checking with position size exceeded."""
        risk_manager.set_account_balance(10000.0)
        
        # Try to add position that exceeds max position size
        large_position_size = 0.2  # 20% of account
        is_valid, violations = risk_manager.check_risk_limits(large_position_size, "BTCUSDT")
        
        assert not is_valid
        assert any("Position size exceeds maximum" in violation for violation in violations)
    
    def test_check_risk_limits_max_positions_exceeded(self, risk_manager):
        """Test risk limit checking with max positions exceeded."""
        risk_manager.set_account_balance(10000.0)
        
        # Add maximum number of positions
        for i in range(risk_manager.max_positions):
            position = PositionRisk(
                symbol=f"SYMBOL{i}",
                position_size=0.01,
                entry_price=100.0,
                current_price=100.0,
                unrealized_pnl=0.0,
                risk_percentage=0.001,
                stop_loss_distance=1.0,
                take_profit_distance=2.0
            )
            risk_manager.add_position(position)
        
        # Try to add one more position
        is_valid, violations = risk_manager.check_risk_limits(0.01, "NEWSYMBOL")
        
        assert not is_valid
        assert any("Maximum number of positions reached" in violation for violation in violations)
    
    def test_calculate_risk_metrics(self, risk_manager):
        """Test risk metrics calculation."""
        risk_manager.set_account_balance(10000.0)
        
        # Add some positions
        for i in range(3):
            position = PositionRisk(
                symbol=f"SYMBOL{i}",
                position_size=0.05,
                entry_price=100.0,
                current_price=105.0,
                unrealized_pnl=25.0,
                risk_percentage=0.0025,
                stop_loss_distance=5.0,
                take_profit_distance=10.0
            )
            risk_manager.add_position(position)
        
        metrics = risk_manager.calculate_risk_metrics()
        
        assert isinstance(metrics, RiskMetrics)
        assert metrics.position_count == 3
        assert metrics.total_exposure > 0
        assert 0 <= metrics.risk_score <= 100
        assert isinstance(metrics.risk_level, RiskLevel)
    
    def test_should_close_position_stop_loss(self, risk_manager, sample_position):
        """Test position closure due to stop loss."""
        risk_manager.set_account_balance(10000.0)
        risk_manager.add_position(sample_position)
        
        # Update position to trigger stop loss
        risk_manager.update_position(sample_position.symbol, 48000.0)  # Below entry price
        
        should_close, reason = risk_manager.should_close_position(sample_position.symbol)
        
        assert should_close
        assert "Stop loss triggered" in reason
    
    def test_should_close_position_take_profit(self, risk_manager, sample_position):
        """Test position closure due to take profit."""
        risk_manager.set_account_balance(10000.0)
        risk_manager.add_position(sample_position)
        
        # Update position to trigger take profit
        risk_manager.update_position(sample_position.symbol, 55000.0)  # Above entry price
        
        should_close, reason = risk_manager.should_close_position(sample_position.symbol)
        
        assert should_close
        assert "Take profit reached" in reason
    
    def test_should_close_position_within_limits(self, risk_manager, sample_position):
        """Test position that should not be closed."""
        risk_manager.set_account_balance(10000.0)
        risk_manager.add_position(sample_position)
        
        # Update position to small profit
        risk_manager.update_position(sample_position.symbol, 50100.0)
        
        should_close, reason = risk_manager.should_close_position(sample_position.symbol)
        
        assert not should_close
        assert "Position within risk limits" in reason
    
    def test_update_daily_pnl(self, risk_manager):
        """Test daily P&L history update."""
        risk_manager.update_daily_pnl(100.0)
        risk_manager.update_daily_pnl(-50.0)
        risk_manager.update_daily_pnl(75.0)
        
        assert len(risk_manager.daily_pnl_history) == 3
        assert risk_manager.daily_pnl_history == [100.0, -50.0, 75.0]
    
    def test_get_risk_report(self, risk_manager):
        """Test risk report generation."""
        risk_manager.set_account_balance(10000.0)
        
        # Add a position
        position = PositionRisk(
            symbol="BTCUSDT",
            position_size=0.1,
            entry_price=50000.0,
            current_price=51000.0,
            unrealized_pnl=100.0,
            risk_percentage=0.01,
            stop_loss_distance=1000.0,
            take_profit_distance=2000.0
        )
        risk_manager.add_position(position)
        
        report = risk_manager.get_risk_report()
        
        assert 'timestamp' in report
        assert 'account_balance' in report
        assert 'total_exposure' in report
        assert 'daily_pnl' in report
        assert 'max_drawdown' in report
        assert 'position_count' in report
        assert 'risk_score' in report
        assert 'risk_level' in report
        assert 'positions' in report
        
        assert report['account_balance'] == 10000.0
        assert report['position_count'] == 1
        assert len(report['positions']) == 1


class TestPositionRisk:
    """Test cases for PositionRisk."""
    
    def test_position_risk_creation(self):
        """Test PositionRisk creation."""
        position = PositionRisk(
            symbol="BTCUSDT",
            position_size=0.1,
            entry_price=50000.0,
            current_price=51000.0,
            unrealized_pnl=100.0,
            risk_percentage=0.01,
            stop_loss_distance=1000.0,
            take_profit_distance=2000.0
        )
        
        assert position.symbol == "BTCUSDT"
        assert position.position_size == 0.1
        assert position.entry_price == 50000.0
        assert position.current_price == 51000.0
        assert position.unrealized_pnl == 100.0
        assert position.risk_percentage == 0.01
        assert position.stop_loss_distance == 1000.0
        assert position.take_profit_distance == 2000.0


class TestRiskLevel:
    """Test cases for RiskLevel enum."""
    
    def test_risk_level_values(self):
        """Test RiskLevel enum values."""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"
    
    def test_risk_level_comparison(self):
        """Test RiskLevel comparison."""
        assert RiskLevel.LOW != RiskLevel.MEDIUM
        assert RiskLevel.HIGH != RiskLevel.CRITICAL


@pytest.mark.parametrize("max_position_size,max_total_exposure,max_daily_loss,max_drawdown,max_positions", [
    (0.05, 0.3, 0.02, 0.1, 3),
    (0.2, 0.8, 0.1, 0.25, 20),
    (0.01, 0.1, 0.005, 0.05, 1),
])
def test_risk_manager_parameter_combinations(max_position_size, max_total_exposure, max_daily_loss, max_drawdown, max_positions):
    """Test RiskManager with various parameter combinations."""
    risk_manager = RiskManager(
        max_position_size=max_position_size,
        max_total_exposure=max_total_exposure,
        max_daily_loss=max_daily_loss,
        max_drawdown=max_drawdown,
        max_positions=max_positions
    )
    
    assert risk_manager.max_position_size == max_position_size
    assert risk_manager.max_total_exposure == max_total_exposure
    assert risk_manager.max_daily_loss == max_daily_loss
    assert risk_manager.max_drawdown == max_drawdown
    assert risk_manager.max_positions == max_positions
