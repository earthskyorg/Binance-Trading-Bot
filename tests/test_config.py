"""Tests for configuration management."""

import pytest
import os
import tempfile
import json
from unittest.mock import patch

from binance_trading_bot.core.config import Config, Settings, TradingConfig
from binance_trading_bot.core.exceptions import ConfigurationError


class TestSettings:
    """Test Settings class."""
    
    def test_settings_creation_with_env_vars(self):
        """Test creating settings from environment variables."""
        with patch.dict(os.environ, {
            'BINANCE_API_KEY': 'test_key',
            'BINANCE_API_SECRET': 'test_secret',
            'TRADING_STRATEGY': 'test_strategy',
            'LEVERAGE': '20',
            'ORDER_SIZE': '5.0'
        }):
            settings = Settings()
            assert settings.api_key == 'test_key'
            assert settings.api_secret == 'test_secret'
            assert settings.trading_strategy == 'test_strategy'
            assert settings.leverage == 20
            assert settings.order_size == 5.0
    
    def test_settings_default_values(self):
        """Test default values when environment variables are not set."""
        with patch.dict(os.environ, {
            'BINANCE_API_KEY': 'test_key',
            'BINANCE_API_SECRET': 'test_secret'
        }, clear=True):
            settings = Settings()
            assert settings.trading_strategy == 'tripleEMAStochasticRSIATR'
            assert settings.leverage == 10
            assert settings.order_size == 3.0
            assert settings.interval == '1m'
    
    def test_symbols_to_trade_parsing(self):
        """Test parsing of symbols_to_trade from string."""
        with patch.dict(os.environ, {
            'BINANCE_API_KEY': 'test_key',
            'BINANCE_API_SECRET': 'test_secret',
            'SYMBOLS_TO_TRADE': 'BTCUSDT,ETHUSDT,ADAUSDT'
        }, clear=True):
            settings = Settings()
            assert settings.symbols_to_trade == ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
    
    def test_coin_exclusion_list_parsing(self):
        """Test parsing of coin_exclusion_list from string."""
        with patch.dict(os.environ, {
            'BINANCE_API_KEY': 'test_key',
            'BINANCE_API_SECRET': 'test_secret',
            'COIN_EXCLUSION_LIST': 'USDCUSDT,BTCDOMUSDT'
        }, clear=True):
            settings = Settings()
            assert settings.coin_exclusion_list == ['USDCUSDT', 'BTCDOMUSDT']
    
    def test_custom_tp_sl_functions_parsing(self):
        """Test parsing of custom_tp_sl_functions from string."""
        with patch.dict(os.environ, {
            'BINANCE_API_KEY': 'test_key',
            'BINANCE_API_SECRET': 'test_secret',
            'CUSTOM_TP_SL_FUNCTIONS': 'USDT,PERCENTAGE'
        }, clear=True):
            settings = Settings()
            assert settings.custom_tp_sl_functions == ['USDT', 'PERCENTAGE']
    
    def test_leverage_validation(self):
        """Test leverage validation."""
        with patch.dict(os.environ, {
            'BINANCE_API_KEY': 'test_key',
            'BINANCE_API_SECRET': 'test_secret',
            'LEVERAGE': '200'  # Invalid leverage
        }, clear=True):
            with pytest.raises(ValueError):
                Settings()
    
    def test_order_size_validation(self):
        """Test order size validation."""
        with patch.dict(os.environ, {
            'BINANCE_API_KEY': 'test_key',
            'BINANCE_API_SECRET': 'test_secret',
            'ORDER_SIZE': '150.0'  # Invalid order size
        }, clear=True):
            with pytest.raises(ValueError):
                Settings()


class TestTradingConfig:
    """Test TradingConfig class."""
    
    def test_trading_config_creation(self):
        """Test creating TradingConfig."""
        config = TradingConfig(
            strategy='test_strategy',
            leverage=10,
            order_size=3.0,
            interval='1m',
            sl_mult=1.5,
            tp_mult=1.0,
            tp_sl_choice='%',
            trading_threshold=0.3,
            max_positions=10,
            trade_all_symbols=True
        )
        
        assert config.strategy == 'test_strategy'
        assert config.leverage == 10
        assert config.order_size == 3.0
        assert config.interval == '1m'
        assert config.sl_mult == 1.5
        assert config.tp_mult == 1.0
        assert config.tp_sl_choice == '%'
        assert config.trading_threshold == 0.3
        assert config.max_positions == 10
        assert config.trade_all_symbols is True


class TestConfig:
    """Test Config class."""
    
    def test_config_creation_from_environment(self):
        """Test creating config from environment variables."""
        with patch.dict(os.environ, {
            'BINANCE_API_KEY': 'test_key',
            'BINANCE_API_SECRET': 'test_secret'
        }, clear=True):
            config = Config()
            assert config.settings.api_key == 'test_key'
            assert config.settings.api_secret == 'test_secret'
    
    def test_config_creation_from_file(self):
        """Test creating config from file."""
        config_data = {
            'api_key': 'file_key',
            'api_secret': 'file_secret',
            'trading_strategy': 'file_strategy',
            'leverage': 20,
            'order_size': 5.0
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name
        
        try:
            with patch.dict(os.environ, {
                'BINANCE_API_KEY': 'env_key',
                'BINANCE_API_SECRET': 'env_secret'
            }, clear=True):
                config = Config(temp_file)
                # File values should override environment values
                assert config.settings.api_key == 'file_key'
                assert config.settings.api_secret == 'file_secret'
                assert config.settings.trading_strategy == 'file_strategy'
                assert config.settings.leverage == 20
                assert config.settings.order_size == 5.0
        finally:
            os.unlink(temp_file)
    
    def test_config_validation_success(self):
        """Test successful configuration validation."""
        with patch.dict(os.environ, {
            'BINANCE_API_KEY': 'test_key',
            'BINANCE_API_SECRET': 'test_secret'
        }, clear=True):
            config = Config()
            # Should not raise an exception
            config.validate()
    
    def test_config_validation_missing_api_key(self):
        """Test configuration validation with missing API key."""
        with patch.dict(os.environ, {
            'BINANCE_API_SECRET': 'test_secret'
        }, clear=True):
            config = Config()
            with pytest.raises(ConfigurationError, match="API key and secret are required"):
                config.validate()
    
    def test_config_validation_missing_api_secret(self):
        """Test configuration validation with missing API secret."""
        with patch.dict(os.environ, {
            'BINANCE_API_KEY': 'test_key'
        }, clear=True):
            config = Config()
            with pytest.raises(ConfigurationError, match="API key and secret are required"):
                config.validate()
    
    def test_config_validation_invalid_order_size(self):
        """Test configuration validation with invalid order size."""
        with patch.dict(os.environ, {
            'BINANCE_API_KEY': 'test_key',
            'BINANCE_API_SECRET': 'test_secret',
            'ORDER_SIZE': '0'  # Invalid order size
        }, clear=True):
            config = Config()
            with pytest.raises(ConfigurationError, match="Order size must be positive"):
                config.validate()
    
    def test_config_validation_invalid_leverage(self):
        """Test configuration validation with invalid leverage."""
        with patch.dict(os.environ, {
            'BINANCE_API_KEY': 'test_key',
            'BINANCE_API_SECRET': 'test_secret',
            'LEVERAGE': '200'  # Invalid leverage
        }, clear=True):
            config = Config()
            with pytest.raises(ConfigurationError, match="Leverage must be between 1 and 125"):
                config.validate()
    
    def test_config_validation_no_symbols(self):
        """Test configuration validation with no symbols to trade."""
        with patch.dict(os.environ, {
            'BINANCE_API_KEY': 'test_key',
            'BINANCE_API_SECRET': 'test_secret',
            'TRADE_ALL_SYMBOLS': 'false',
            'SYMBOLS_TO_TRADE': ''
        }, clear=True):
            config = Config()
            with pytest.raises(ConfigurationError, match="Must specify symbols to trade"):
                config.validate()
    
    def test_save_config(self):
        """Test saving configuration to file."""
        with patch.dict(os.environ, {
            'BINANCE_API_KEY': 'test_key',
            'BINANCE_API_SECRET': 'test_secret'
        }, clear=True):
            config = Config()
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                temp_file = f.name
            
            try:
                config.save_config(temp_file)
                
                # Verify the file was created and contains correct data
                assert os.path.exists(temp_file)
                with open(temp_file, 'r') as f:
                    saved_data = json.load(f)
                    assert saved_data['api_key'] == 'test_key'
                    assert saved_data['api_secret'] == 'test_secret'
            finally:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
    
    def test_trading_config_property(self):
        """Test trading_config property."""
        with patch.dict(os.environ, {
            'BINANCE_API_KEY': 'test_key',
            'BINANCE_API_SECRET': 'test_secret',
            'TRADING_STRATEGY': 'test_strategy',
            'LEVERAGE': '15',
            'ORDER_SIZE': '4.0'
        }, clear=True):
            config = Config()
            trading_config = config.trading_config
            
            assert trading_config.strategy == 'test_strategy'
            assert trading_config.leverage == 15
            assert trading_config.order_size == 4.0
            assert isinstance(trading_config, TradingConfig)
