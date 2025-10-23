"""
Professional trading engine for the Binance Trading Bot.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from ..core.exceptions import TradingBotError, TradingError
from ..core.logging import get_logger, TradeLogger
from ..core.config import TradingConfig
from ..api.client import BinanceAPIClient
from ..strategies.registry import strategy_registry
from .risk_manager import RiskManager
from .position_manager import PositionManager
from .signal_processor import SignalProcessor


class TradingEngine:
    """Professional trading engine with comprehensive risk management."""
    
    def __init__(
        self,
        api_client: BinanceAPIClient,
        config: TradingConfig,
        dry_run: bool = False
    ):
        self.api_client = api_client
        self.config = config
        self.dry_run = dry_run
        
        # Initialize components
        self.risk_manager = RiskManager(
            max_position_size=config.order_size / 100,
            max_total_exposure=0.5,
            max_daily_loss=0.05,
            max_drawdown=0.15,
            max_positions=config.max_positions
        )
        
        self.position_manager = PositionManager(
            api_client=api_client,
            risk_manager=self.risk_manager,
            dry_run=dry_run
        )
        
        self.signal_processor = SignalProcessor(
            config=config,
            risk_manager=self.risk_manager
        )
        
        # Initialize strategy
        self.strategy = strategy_registry.get_strategy(
            config.strategy,
            self._get_strategy_parameters()
        )
        
        # State management
        self.is_running = False
        self.symbols_to_trade: List[str] = []
        self.market_data: Dict[str, Any] = {}
        
        # Logging
        self.logger = get_logger("trading_engine")
        self.trade_logger = TradeLogger(self.logger)
        
        # Performance metrics
        self.metrics = {
            'trades_executed': 0,
            'trades_profitable': 0,
            'total_pnl': 0.0,
            'start_time': None,
            'last_update': None
        }
    
    async def start(self) -> None:
        """Start the trading engine."""
        try:
            self.logger.info("Starting trading engine...")
            
            # Initialize account
            await self._initialize_account()
            
            # Get symbols to trade
            await self._initialize_symbols()
            
            # Start market data collection
            await self._start_market_data_collection()
            
            # Start signal processing
            await self._start_signal_processing()
            
            # Start position monitoring
            await self._start_position_monitoring()
            
            self.is_running = True
            self.metrics['start_time'] = datetime.utcnow()
            
            self.logger.info(
                "Trading engine started successfully",
                extra={
                    'strategy': self.config.strategy,
                    'symbols': self.symbols_to_trade,
                    'dry_run': self.dry_run
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to start trading engine: {e}")
            raise TradingBotError(f"Failed to start trading engine: {e}")
    
    async def stop(self) -> None:
        """Stop the trading engine."""
        try:
            self.logger.info("Stopping trading engine...")
            
            self.is_running = False
            
            # Close all positions if configured
            if self.config.use_market_orders:
                await self._close_all_positions()
            
            # Generate final report
            await self._generate_performance_report()
            
            self.logger.info("Trading engine stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping trading engine: {e}")
    
    async def _initialize_account(self) -> None:
        """Initialize account and set leverage."""
        try:
            # Get account information
            account_info = await self.api_client.get_account_info()
            self.risk_manager.set_account_balance(account_info.balance)
            
            self.logger.info(
                f"Account initialized",
                extra={
                    'balance': account_info.balance,
                    'available_balance': account_info.available_balance,
                    'margin_balance': account_info.margin_balance
                }
            )
            
            # Set leverage for all symbols
            for symbol in self.symbols_to_trade:
                try:
                    await self.api_client.set_leverage(symbol, self.config.leverage)
                    self.logger.info(f"Set leverage {self.config.leverage}x for {symbol}")
                except Exception as e:
                    self.logger.warning(f"Failed to set leverage for {symbol}: {e}")
            
        except Exception as e:
            raise TradingError(f"Failed to initialize account: {e}")
    
    async def _initialize_symbols(self) -> None:
        """Initialize symbols to trade."""
        try:
            if self.config.trade_all_symbols:
                # Get all available symbols
                exchange_info = await self.api_client.get_exchange_info()
                self.symbols_to_trade = [
                    symbol['symbol'] for symbol in exchange_info['symbols']
                    if symbol['status'] == 'TRADING'
                    and symbol['symbol'] not in self.config.coin_exclusion_list
                ]
            else:
                self.symbols_to_trade = self.config.symbols_to_trade
            
            self.logger.info(f"Initialized {len(self.symbols_to_trade)} symbols to trade")
            
        except Exception as e:
            raise TradingError(f"Failed to initialize symbols: {e}")
    
    async def _start_market_data_collection(self) -> None:
        """Start collecting market data for all symbols."""
        try:
            for symbol in self.symbols_to_trade:
                # Get historical data
                klines = await self.api_client.get_klines(
                    symbol=symbol,
                    interval=self.config.interval,
                    limit=200
                )
                
                # Convert to market data format
                market_data = self._convert_klines_to_market_data(symbol, klines)
                self.market_data[symbol] = market_data
                
                self.logger.info(f"Loaded market data for {symbol}")
            
        except Exception as e:
            raise TradingError(f"Failed to start market data collection: {e}")
    
    async def _start_signal_processing(self) -> None:
        """Start signal processing loop."""
        async def signal_loop():
            while self.is_running:
                try:
                    for symbol in self.symbols_to_trade:
                        if symbol in self.market_data:
                            # Update indicators
                            self.strategy.update_indicators(self.market_data[symbol])
                            
                            # Generate signal
                            signal_result = self.strategy.generate_signal(
                                self.market_data[symbol],
                                len(self.market_data[symbol].close) - 1
                            )
                            
                            # Process signal
                            if signal_result.signal.value != 'hold':
                                await self.signal_processor.process_signal(
                                    symbol=symbol,
                                    signal_result=signal_result,
                                    market_data=self.market_data[symbol]
                                )
                    
                    # Wait for next iteration
                    await asyncio.sleep(60)  # Process signals every minute
                    
                except Exception as e:
                    self.logger.error(f"Error in signal processing: {e}")
                    await asyncio.sleep(10)  # Wait before retrying
        
        # Start signal processing task
        asyncio.create_task(signal_loop())
    
    async def _start_position_monitoring(self) -> None:
        """Start position monitoring loop."""
        async def monitoring_loop():
            while self.is_running:
                try:
                    # Update all positions
                    await self.position_manager.update_all_positions()
                    
                    # Check risk limits
                    risk_report = self.risk_manager.get_risk_report()
                    if risk_report['risk_level'] == 'critical':
                        self.logger.warning("Critical risk level detected, closing positions")
                        await self._close_all_positions()
                    
                    # Wait for next update
                    await asyncio.sleep(30)  # Update every 30 seconds
                    
                except Exception as e:
                    self.logger.error(f"Error in position monitoring: {e}")
                    await asyncio.sleep(10)
        
        # Start monitoring task
        asyncio.create_task(monitoring_loop())
    
    async def _close_all_positions(self) -> None:
        """Close all open positions."""
        try:
            positions = await self.api_client.get_open_orders()
            for position in positions:
                await self.api_client.cancel_order(
                    symbol=position['symbol'],
                    order_id=position['orderId']
                )
            
            self.logger.info("Closed all positions")
            
        except Exception as e:
            self.logger.error(f"Error closing positions: {e}")
    
    async def _generate_performance_report(self) -> None:
        """Generate performance report."""
        try:
            runtime = datetime.utcnow() - self.metrics['start_time']
            
            report = {
                'runtime': str(runtime),
                'trades_executed': self.metrics['trades_executed'],
                'trades_profitable': self.metrics['trades_profitable'],
                'win_rate': (
                    self.metrics['trades_profitable'] / self.metrics['trades_executed']
                    if self.metrics['trades_executed'] > 0 else 0
                ),
                'total_pnl': self.metrics['total_pnl'],
                'strategy': self.config.strategy,
                'symbols_traded': self.symbols_to_trade
            }
            
            self.logger.info("Performance report generated", extra=report)
            
        except Exception as e:
            self.logger.error(f"Error generating performance report: {e}")
    
    def _convert_klines_to_market_data(self, symbol: str, klines: List[List]) -> Any:
        """Convert klines data to MarketData format."""
        from ..strategies.base import MarketData
        
        opens = [float(k[1]) for k in klines]
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]
        closes = [float(k[4]) for k in klines]
        volumes = [float(k[5]) for k in klines]
        timestamps = [int(k[0]) for k in klines]
        
        return MarketData(
            symbol=symbol,
            open=opens,
            high=highs,
            low=lows,
            close=closes,
            volume=volumes,
            timestamp=timestamps
        )
    
    def _get_strategy_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters from config."""
        return {
            'leverage': self.config.leverage,
            'order_size': self.config.order_size,
            'sl_mult': self.config.sl_mult,
            'tp_mult': self.config.tp_mult,
            'tp_sl_choice': self.config.tp_sl_choice
        }
