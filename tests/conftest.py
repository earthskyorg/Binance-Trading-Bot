"""Test configuration and fixtures."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

from binance_trading_bot.core.config import Config
from binance_trading_bot.core.exceptions import TradingBotError


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = Mock(spec=Config)
    config.settings.api_key = "test_api_key"
    config.settings.api_secret = "test_api_secret"
    config.settings.trading_strategy = "test_strategy"
    config.settings.leverage = 10
    config.settings.order_size = 3.0
    config.settings.interval = "1m"
    config.settings.sl_mult = 1.5
    config.settings.tp_mult = 1.0
    config.settings.tp_sl_choice = "%"
    config.settings.trading_threshold = 0.3
    config.settings.max_positions = 10
    config.settings.trade_all_symbols = True
    config.settings.symbols_to_trade = ["BTCUSDT"]
    config.settings.coin_exclusion_list = ["USDCUSDT"]
    config.settings.use_trailing_stop = False
    config.settings.trailing_stop_callback = 0.1
    config.settings.use_market_orders = False
    config.settings.wait_for_candle_close = True
    config.settings.use_multiprocessing = True
    config.settings.auto_calculate_buffer = True
    config.settings.buffer = "3 hours ago"
    config.settings.custom_tp_sl_functions = ["USDT"]
    config.settings.make_decision_options = {}
    config.settings.log_level = 20
    config.settings.log_to_file = False
    config.settings.log_file_path = None
    
    # Mock trading config
    config.trading_config = Mock()
    config.trading_config.strategy = "test_strategy"
    config.trading_config.leverage = 10
    config.trading_config.order_size = 3.0
    config.trading_config.interval = "1m"
    config.trading_config.sl_mult = 1.5
    config.trading_config.tp_mult = 1.0
    config.trading_config.tp_sl_choice = "%"
    config.trading_config.trading_threshold = 0.3
    config.trading_config.max_positions = 10
    config.trading_config.trade_all_symbols = True
    config.trading_config.symbols_to_trade = ["BTCUSDT"]
    config.trading_config.coin_exclusion_list = ["USDCUSDT"]
    config.trading_config.use_trailing_stop = False
    config.trading_config.trailing_stop_callback = 0.1
    config.trading_config.use_market_orders = False
    config.trading_config.wait_for_candle_close = True
    config.trading_config.use_multiprocessing = True
    config.trading_config.auto_calculate_buffer = True
    config.trading_config.buffer = "3 hours ago"
    config.trading_config.custom_tp_sl_functions = ["USDT"]
    config.trading_config.make_decision_options = {}
    
    return config


@pytest.fixture
def mock_binance_client():
    """Create a mock Binance client for testing."""
    client = Mock()
    client.futures_account.return_value = {
        'totalMarginBalance': '1000.0',
        'totalWalletBalance': '1000.0'
    }
    client.futures_account_balance.return_value = [
        {'asset': 'USDT', 'balance': '1000.0'}
    ]
    client.futures_position_information.return_value = []
    client.futures_exchange_info.return_value = {
        'symbols': [
            {
                'pair': 'BTCUSDT',
                'pricePrecision': 2,
                'quantityPrecision': 3,
                'filters': [{'tickSize': '0.01'}]
            }
        ]
    }
    client.futures_symbol_ticker.return_value = {'price': '50000.0'}
    client.futures_order_book.return_value = {
        'bids': [['50000.0', '1.0']],
        'asks': [['50001.0', '1.0']]
    }
    client.futures_ping.return_value = {}
    client.futures_change_leverage.return_value = {'leverage': 10}
    client.futures_create_order.return_value = {'orderId': '12345'}
    client.futures_cancel_all_open_orders.return_value = {}
    client.futures_get_open_orders.return_value = []
    client.futures_historical_klines.return_value = []
    
    return client


@pytest.fixture
def sample_market_data():
    """Sample market data for testing."""
    return {
        'symbol': 'BTCUSDT',
        'open': 50000.0,
        'high': 51000.0,
        'low': 49000.0,
        'close': 50500.0,
        'volume': 1000.0,
        'timestamp': 1640995200000
    }


@pytest.fixture
def sample_indicators():
    """Sample technical indicators for testing."""
    return {
        'ema_20': 50200.0,
        'ema_50': 49800.0,
        'rsi': 65.5,
        'macd': 150.0,
        'macd_signal': 145.0,
        'stochastic_k': 75.0,
        'stochastic_d': 70.0
    }


@pytest.fixture
def mock_strategy():
    """Create a mock trading strategy for testing."""
    strategy = Mock()
    strategy.calculate_signals.return_value = (1, 100.0, 200.0)  # direction, sl, tp
    strategy.name = "test_strategy"
    return strategy


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket for testing."""
    ws = AsyncMock()
    ws.send = AsyncMock()
    ws.recv = AsyncMock()
    ws.close = AsyncMock()
    return ws


@pytest.fixture
def sample_trade_data():
    """Sample trade data for testing."""
    return {
        'symbol': 'BTCUSDT',
        'direction': 1,  # Long
        'entry_price': 50000.0,
        'quantity': 0.001,
        'stop_loss': 49000.0,
        'take_profit': 51000.0,
        'order_id': '12345',
        'timestamp': 1640995200000
    }


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = Mock()
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.critical = Mock()
    logger.exception = Mock()
    logger.trade_signal = Mock()
    logger.trade_opened = Mock()
    logger.trade_closed = Mock()
    logger.error_with_context = Mock()
    return logger


@pytest.fixture
def mock_queue():
    """Create a mock queue for testing."""
    queue = Mock()
    queue.put = Mock()
    queue.get = Mock()
    queue.empty = Mock(return_value=False)
    queue.qsize = Mock(return_value=1)
    return queue


@pytest.fixture
def mock_thread():
    """Create a mock thread for testing."""
    thread = Mock()
    thread.start = Mock()
    thread.join = Mock()
    thread.is_alive = Mock(return_value=True)
    thread.daemon = False
    return thread


@pytest.fixture
def mock_process():
    """Create a mock process for testing."""
    process = Mock()
    process.start = Mock()
    process.join = Mock()
    process.is_alive = Mock(return_value=True)
    process.terminate = Mock()
    process.kill = Mock()
    return process


# Pytest markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
