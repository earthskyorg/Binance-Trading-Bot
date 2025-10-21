"""
Configuration management for the trading bot.
"""

import os
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
import json

from pydantic import BaseSettings, Field, validator
from dotenv import load_dotenv

from .exceptions import ConfigurationError


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_key: str = Field(..., env="BINANCE_API_KEY")
    api_secret: str = Field(..., env="BINANCE_API_SECRET")
    
    # Trading Configuration
    trading_strategy: str = Field(default="tripleEMAStochasticRSIATR", env="TRADING_STRATEGY")
    leverage: int = Field(default=10, ge=1, le=125, env="LEVERAGE")
    order_size: float = Field(default=3.0, ge=0.1, le=100.0, env="ORDER_SIZE")
    interval: str = Field(default="1m", env="TRADING_INTERVAL")
    
    # Risk Management
    sl_mult: float = Field(default=1.5, ge=0.1, env="SL_MULT")
    tp_mult: float = Field(default=1.0, ge=0.1, env="TP_MULT")
    tp_sl_choice: str = Field(default="%", env="TP_SL_CHOICE")
    trading_threshold: float = Field(default=0.3, ge=0.1, le=10.0, env="TRADING_THRESHOLD")
    max_positions: int = Field(default=10, ge=1, le=100, env="MAX_POSITIONS")
    
    # Trading Options
    trade_all_symbols: bool = Field(default=True, env="TRADE_ALL_SYMBOLS")
    symbols_to_trade: List[str] = Field(default=["BTCUSDT"], env="SYMBOLS_TO_TRADE")
    coin_exclusion_list: List[str] = Field(default=["USDCUSDT", "BTCDOMUSDT"], env="COIN_EXCLUSION_LIST")
    
    # Advanced Options
    use_trailing_stop: bool = Field(default=False, env="USE_TRAILING_STOP")
    trailing_stop_callback: float = Field(default=0.1, ge=0.001, le=5.0, env="TRAILING_STOP_CALLBACK")
    use_market_orders: bool = Field(default=False, env="USE_MARKET_ORDERS")
    wait_for_candle_close: bool = Field(default=True, env="WAIT_FOR_CANDLE_CLOSE")
    use_multiprocessing: bool = Field(default=True, env="USE_MULTIPROCESSING")
    
    # Buffer Configuration
    auto_calculate_buffer: bool = Field(default=True, env="AUTO_CALCULATE_BUFFER")
    buffer: str = Field(default="3 hours ago", env="BUFFER")
    
    # Logging Configuration
    log_level: int = Field(default=20, env="LOG_LEVEL")  # INFO level
    log_to_file: bool = Field(default=False, env="LOG_TO_FILE")
    log_file_path: Optional[str] = Field(default=None, env="LOG_FILE_PATH")
    
    # Custom Functions
    custom_tp_sl_functions: List[str] = Field(default=["USDT"], env="CUSTOM_TP_SL_FUNCTIONS")
    make_decision_options: Dict[str, Any] = Field(default_factory=dict, env="MAKE_DECISION_OPTIONS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    @validator("symbols_to_trade", pre=True)
    def parse_symbols_to_trade(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",")]
        return v
        
    @validator("coin_exclusion_list", pre=True)
    def parse_coin_exclusion_list(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",")]
        return v
        
    @validator("custom_tp_sl_functions", pre=True)
    def parse_custom_tp_sl_functions(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",")]
        return v


@dataclass
class TradingConfig:
    """Trading configuration data class."""
    
    # Core trading settings
    strategy: str
    leverage: int
    order_size: float
    interval: str
    
    # Risk management
    sl_mult: float
    tp_mult: float
    tp_sl_choice: str
    trading_threshold: float
    max_positions: int
    
    # Trading options
    trade_all_symbols: bool
    symbols_to_trade: List[str] = field(default_factory=list)
    coin_exclusion_list: List[str] = field(default_factory=list)
    
    # Advanced options
    use_trailing_stop: bool = False
    trailing_stop_callback: float = 0.1
    use_market_orders: bool = False
    wait_for_candle_close: bool = True
    use_multiprocessing: bool = True
    
    # Buffer configuration
    auto_calculate_buffer: bool = True
    buffer: str = "3 hours ago"
    
    # Custom functions
    custom_tp_sl_functions: List[str] = field(default_factory=lambda: ["USDT"])
    make_decision_options: Dict[str, Any] = field(default_factory=dict)


class Config:
    """Main configuration class."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            config_path: Path to configuration file. If None, loads from environment.
        """
        self.config_path = config_path
        self._settings: Optional[Settings] = None
        self._trading_config: Optional[TradingConfig] = None
        
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file or environment."""
        if self.config_path and Path(self.config_path).exists():
            self._load_from_file()
        else:
            self._load_from_environment()
    
    def _load_from_file(self) -> None:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)
            
            # Load environment variables first
            load_dotenv()
            
            # Override with file values
            for key, value in config_data.items():
                os.environ[key.upper()] = str(value)
                
            self._settings = Settings()
            
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration from file: {e}")
    
    def _load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        try:
            load_dotenv()
            self._settings = Settings()
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration from environment: {e}")
    
    @property
    def settings(self) -> Settings:
        """Get application settings."""
        if self._settings is None:
            raise ConfigurationError("Configuration not loaded")
        return self._settings
    
    @property
    def trading_config(self) -> TradingConfig:
        """Get trading configuration."""
        if self._trading_config is None:
            settings = self.settings
            self._trading_config = TradingConfig(
                strategy=settings.trading_strategy,
                leverage=settings.leverage,
                order_size=settings.order_size,
                interval=settings.interval,
                sl_mult=settings.sl_mult,
                tp_mult=settings.tp_mult,
                tp_sl_choice=settings.tp_sl_choice,
                trading_threshold=settings.trading_threshold,
                max_positions=settings.max_positions,
                trade_all_symbols=settings.trade_all_symbols,
                symbols_to_trade=settings.symbols_to_trade,
                coin_exclusion_list=settings.coin_exclusion_list,
                use_trailing_stop=settings.use_trailing_stop,
                trailing_stop_callback=settings.trailing_stop_callback,
                use_market_orders=settings.use_market_orders,
                wait_for_candle_close=settings.wait_for_candle_close,
                use_multiprocessing=settings.use_multiprocessing,
                auto_calculate_buffer=settings.auto_calculate_buffer,
                buffer=settings.buffer,
                custom_tp_sl_functions=settings.custom_tp_sl_functions,
                make_decision_options=settings.make_decision_options,
            )
        return self._trading_config
    
    def validate(self) -> None:
        """Validate configuration."""
        settings = self.settings
        
        # Validate API credentials
        if not settings.api_key or not settings.api_secret:
            raise ConfigurationError("API key and secret are required")
        
        # Validate trading parameters
        if settings.order_size <= 0:
            raise ConfigurationError("Order size must be positive")
        
        if settings.leverage < 1 or settings.leverage > 125:
            raise ConfigurationError("Leverage must be between 1 and 125")
        
        # Validate symbols
        if not settings.trade_all_symbols and not settings.symbols_to_trade:
            raise ConfigurationError("Must specify symbols to trade or enable trade_all_symbols")
    
    def save_config(self, file_path: str) -> None:
        """Save current configuration to file.
        
        Args:
            file_path: Path to save configuration file.
        """
        try:
            settings = self.settings
            config_data = {
                "api_key": settings.api_key,
                "api_secret": settings.api_secret,
                "trading_strategy": settings.trading_strategy,
                "leverage": settings.leverage,
                "order_size": settings.order_size,
                "interval": settings.interval,
                "sl_mult": settings.sl_mult,
                "tp_mult": settings.tp_mult,
                "tp_sl_choice": settings.tp_sl_choice,
                "trading_threshold": settings.trading_threshold,
                "max_positions": settings.max_positions,
                "trade_all_symbols": settings.trade_all_symbols,
                "symbols_to_trade": settings.symbols_to_trade,
                "coin_exclusion_list": settings.coin_exclusion_list,
                "use_trailing_stop": settings.use_trailing_stop,
                "trailing_stop_callback": settings.trailing_stop_callback,
                "use_market_orders": settings.use_market_orders,
                "wait_for_candle_close": settings.wait_for_candle_close,
                "use_multiprocessing": settings.use_multiprocessing,
                "auto_calculate_buffer": settings.auto_calculate_buffer,
                "buffer": settings.buffer,
                "custom_tp_sl_functions": settings.custom_tp_sl_functions,
                "make_decision_options": settings.make_decision_options,
                "log_level": settings.log_level,
                "log_to_file": settings.log_to_file,
                "log_file_path": settings.log_file_path,
            }
            
            with open(file_path, 'w') as f:
                json.dump(config_data, f, indent=2)
                
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {e}")
