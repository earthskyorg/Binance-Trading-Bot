"""
Main entry point for the Binance Trading Bot.
"""

import asyncio
import sys
import signal
from typing import Optional
import argparse
from pathlib import Path

from .core.config import Config
from .core.exceptions import ConfigurationError, TradingBotError
from .core.logging import get_logger


def setup_signal_handlers(logger) -> None:
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Professional Binance Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  trading-bot                          # Run with default configuration
  trading-bot --config config.json     # Run with custom configuration file
  trading-bot --validate-config        # Validate configuration without running
  trading-bot --dry-run                # Run in dry-run mode (no actual trades)
        """
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="Validate configuration and exit"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (no actual trades)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level"
    )
    
    parser.add_argument(
        "--log-file",
        type=str,
        help="Path to log file"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 2.0.0"
    )
    
    return parser.parse_args()


def validate_configuration(config_path: Optional[str]) -> None:
    """Validate configuration.
    
    Args:
        config_path: Path to configuration file
    """
    try:
        config = Config(config_path)
        config.validate()
        print("✓ Configuration is valid")
        
        # Print key configuration details
        trading_config = config.trading_config
        print(f"✓ Trading strategy: {trading_config.strategy}")
        print(f"✓ Leverage: {trading_config.leverage}x")
        print(f"✓ Order size: {trading_config.order_size}%")
        print(f"✓ Max positions: {trading_config.max_positions}")
        print(f"✓ Symbols to trade: {trading_config.symbols_to_trade}")
        
    except ConfigurationError as e:
        print(f"✗ Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        sys.exit(1)


async def run_bot(config_path: Optional[str], dry_run: bool = False) -> None:
    """Run the trading bot.
    
    Args:
        config_path: Path to configuration file
        dry_run: Whether to run in dry-run mode
    """
    logger = get_logger("trading_bot")
    
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = Config(config_path)
        config.validate()
        
        # Setup signal handlers
        setup_signal_handlers(logger)
        
        # Log startup information
        trading_config = config.trading_config
        logger.info("Starting Binance Trading Bot", 
                   strategy=trading_config.strategy,
                   leverage=trading_config.leverage,
                   order_size=trading_config.order_size,
                   dry_run=dry_run)
        
        if dry_run:
            logger.info("Running in DRY-RUN mode - no actual trades will be executed")
        
        # TODO: Initialize and run the actual trading bot
        # This will be implemented when we refactor the existing bot code
        
        logger.info("Trading bot started successfully")
        
        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
            
    except ConfigurationError as e:
        logger.error("Configuration error", error=str(e))
        sys.exit(1)
    except TradingBotError as e:
        logger.error("Trading bot error", error=str(e))
        sys.exit(1)
    except Exception as e:
        logger.error("Unexpected error", error=str(e))
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    args = parse_arguments()
    
    # Handle configuration validation
    if args.validate_config:
        validate_configuration(args.config)
        return
    
    # Set up Windows event loop policy if on Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Run the bot
    try:
        asyncio.run(run_bot(args.config, args.dry_run))
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
