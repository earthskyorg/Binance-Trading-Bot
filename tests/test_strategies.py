"""
Comprehensive tests for trading strategies.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch

from binance_trading_bot.strategies.base import MarketData, SignalType
from binance_trading_bot.strategies.triple_ema import TripleEMAStrategy
from binance_trading_bot.strategies.stoch_rsi_macd import StochRSIMACDStrategy


class TestTripleEMAStrategy:
    """Test cases for TripleEMAStrategy."""
    
    @pytest.fixture
    def strategy(self):
        """Create strategy instance for testing."""
        return TripleEMAStrategy()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample market data."""
        np.random.seed(42)
        n = 100
        prices = 100 + np.cumsum(np.random.randn(n) * 0.1)
        
        return MarketData(
            symbol="BTCUSDT",
            open=prices,
            high=prices * 1.01,
            low=prices * 0.99,
            close=prices,
            volume=np.random.randint(1000, 10000, n),
            timestamp=list(range(n))
        )
    
    def test_strategy_initialization(self, strategy):
        """Test strategy initialization."""
        assert strategy.name == "tripleEMA"
        assert strategy.get_parameter('fast_ema') == 5
        assert strategy.get_parameter('medium_ema') == 20
        assert strategy.get_parameter('slow_ema') == 50
    
    def test_parameter_validation(self):
        """Test parameter validation."""
        # Valid parameters
        strategy = TripleEMAStrategy(parameters={
            'fast_ema': 3,
            'medium_ema': 10,
            'slow_ema': 30
        })
        assert strategy.get_parameter('fast_ema') == 3
        
        # Invalid parameters - should raise ValueError
        with pytest.raises(ValueError):
            TripleEMAStrategy(parameters={
                'fast_ema': 20,
                'medium_ema': 10,
                'slow_ema': 5
            })
    
    def test_calculate_indicators(self, strategy, sample_data):
        """Test indicator calculation."""
        indicators = strategy.calculate_indicators(sample_data)
        
        assert 'ema_fast' in indicators
        assert 'ema_medium' in indicators
        assert 'ema_slow' in indicators
        
        # Check that indicators have correct length
        assert len(indicators['ema_fast']) == len(sample_data.close)
        assert len(indicators['ema_medium']) == len(sample_data.close)
        assert len(indicators['ema_slow']) == len(sample_data.close)
    
    def test_generate_signal_insufficient_data(self, strategy, sample_data):
        """Test signal generation with insufficient data."""
        result = strategy.generate_signal(sample_data, 2)
        
        assert result.signal == SignalType.HOLD
        assert result.confidence == 0.0
    
    def test_generate_signal_bullish_crossover(self, strategy, sample_data):
        """Test bullish crossover signal generation."""
        # Mock indicators to simulate bullish crossover
        strategy.indicators = {
            'ema_fast': np.array([10, 11, 12, 13, 14, 15]),
            'ema_medium': np.array([20, 19, 18, 17, 16, 15]),
            'ema_slow': np.array([30, 29, 28, 27, 26, 25])
        }
        
        result = strategy.generate_signal(sample_data, 5)
        
        assert result.signal == SignalType.BUY
        assert result.confidence == 0.8
        assert result.metadata['crossover_type'] == 'bullish'
    
    def test_generate_signal_bearish_crossover(self, strategy, sample_data):
        """Test bearish crossover signal generation."""
        # Mock indicators to simulate bearish crossover
        strategy.indicators = {
            'ema_fast': np.array([30, 29, 28, 27, 26, 25]),
            'ema_medium': np.array([20, 21, 22, 23, 24, 25]),
            'ema_slow': np.array([10, 11, 12, 13, 14, 15])
        }
        
        result = strategy.generate_signal(sample_data, 5)
        
        assert result.signal == SignalType.SELL
        assert result.confidence == 0.8
        assert result.metadata['crossover_type'] == 'bearish'
    
    def test_generate_signal_no_crossover(self, strategy, sample_data):
        """Test signal generation with no crossover."""
        # Mock indicators with no crossover
        strategy.indicators = {
            'ema_fast': np.array([15, 16, 17, 18, 19, 20]),
            'ema_medium': np.array([25, 26, 27, 28, 29, 30]),
            'ema_slow': np.array([35, 36, 37, 38, 39, 40])
        }
        
        result = strategy.generate_signal(sample_data, 5)
        
        assert result.signal == SignalType.HOLD
        assert result.confidence == 0.0
    
    def test_get_required_buffer_size(self, strategy):
        """Test buffer size calculation."""
        buffer_size = strategy.get_required_buffer_size()
        assert buffer_size > 0
        assert buffer_size >= strategy.get_parameter('slow_ema')


class TestStochRSIMACDStrategy:
    """Test cases for StochRSIMACDStrategy."""
    
    @pytest.fixture
    def strategy(self):
        """Create strategy instance for testing."""
        return StochRSIMACDStrategy()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample market data."""
        np.random.seed(42)
        n = 100
        prices = 100 + np.cumsum(np.random.randn(n) * 0.1)
        
        return MarketData(
            symbol="ETHUSDT",
            open=prices,
            high=prices * 1.01,
            low=prices * 0.99,
            close=prices,
            volume=np.random.randint(1000, 10000, n),
            timestamp=list(range(n))
        )
    
    def test_strategy_initialization(self, strategy):
        """Test strategy initialization."""
        assert strategy.name == "StochRSIMACD"
        assert strategy.get_parameter('rsi_period') == 14
        assert strategy.get_parameter('stoch_k_period') == 14
        assert strategy.get_parameter('macd_fast') == 12
    
    def test_calculate_indicators(self, strategy, sample_data):
        """Test indicator calculation."""
        indicators = strategy.calculate_indicators(sample_data)
        
        required_indicators = ['rsi', 'stoch_k', 'stoch_d', 'macd', 'macd_signal', 'macd_histogram']
        for indicator in required_indicators:
            assert indicator in indicators
            assert len(indicators[indicator]) == len(sample_data.close)
    
    def test_generate_signal_insufficient_data(self, strategy, sample_data):
        """Test signal generation with insufficient data."""
        result = strategy.generate_signal(sample_data, 10)
        
        assert result.signal == SignalType.HOLD
        assert result.confidence == 0.0
    
    def test_generate_signal_buy_conditions(self, strategy, sample_data):
        """Test buy signal generation."""
        # Mock indicators to simulate buy conditions
        strategy.indicators = {
            'rsi': np.array([60] * 100),
            'stoch_k': np.array([15] * 100),
            'stoch_d': np.array([10] * 100),
            'macd': np.array([0.1] * 100),
            'macd_signal': np.array([0.05] * 100),
            'macd_histogram': np.array([0.05] * 100)
        }
        
        result = strategy.generate_signal(sample_data, 50)
        
        # Should generate buy signal with high confidence
        assert result.signal == SignalType.BUY
        assert result.confidence > 0.5
    
    def test_generate_signal_sell_conditions(self, strategy, sample_data):
        """Test sell signal generation."""
        # Mock indicators to simulate sell conditions
        strategy.indicators = {
            'rsi': np.array([40] * 100),
            'stoch_k': np.array([85] * 100),
            'stoch_d': np.array([90] * 100),
            'macd': np.array([-0.1] * 100),
            'macd_signal': np.array([-0.05] * 100),
            'macd_histogram': np.array([-0.05] * 100)
        }
        
        result = strategy.generate_signal(sample_data, 50)
        
        # Should generate sell signal with high confidence
        assert result.signal == SignalType.SELL
        assert result.confidence > 0.5


class TestMarketData:
    """Test cases for MarketData."""
    
    def test_market_data_creation(self):
        """Test MarketData creation."""
        data = MarketData(
            symbol="BTCUSDT",
            open=[100, 101, 102],
            high=[101, 102, 103],
            low=[99, 100, 101],
            close=[100.5, 101.5, 102.5],
            volume=[1000, 1100, 1200],
            timestamp=[1, 2, 3]
        )
        
        assert data.symbol == "BTCUSDT"
        assert len(data.open) == 3
        assert len(data.high) == 3
        assert len(data.low) == 3
        assert len(data.close) == 3
        assert len(data.volume) == 3
        assert len(data.timestamp) == 3
    
    def test_to_dataframe(self):
        """Test conversion to DataFrame."""
        data = MarketData(
            symbol="BTCUSDT",
            open=[100, 101, 102],
            high=[101, 102, 103],
            low=[99, 100, 101],
            close=[100.5, 101.5, 102.5],
            volume=[1000, 1100, 1200],
            timestamp=[1, 2, 3]
        )
        
        df = data.to_dataframe()
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert 'open' in df.columns
        assert 'high' in df.columns
        assert 'low' in df.columns
        assert 'close' in df.columns
        assert 'volume' in df.columns
        assert 'timestamp' in df.columns


@pytest.mark.parametrize("strategy_class,expected_name", [
    (TripleEMAStrategy, "tripleEMA"),
    (StochRSIMACDStrategy, "StochRSIMACD"),
])
def test_strategy_names(strategy_class, expected_name):
    """Test strategy names."""
    strategy = strategy_class()
    assert strategy.name == expected_name


@pytest.mark.parametrize("strategy_class", [
    TripleEMAStrategy,
    StochRSIMACDStrategy,
])
def test_strategy_buffer_sizes(strategy_class):
    """Test that all strategies return positive buffer sizes."""
    strategy = strategy_class()
    buffer_size = strategy.get_required_buffer_size()
    assert buffer_size > 0
    assert isinstance(buffer_size, int)
