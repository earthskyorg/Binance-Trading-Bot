# Professional Binance Trading Bot

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests](https://github.com/earthskyorg/binance-trading-bot/workflows/Tests/badge.svg)](https://github.com/earthskyorg/binance-trading-bot/actions)

A professional, feature-rich cryptocurrency trading bot for Binance Futures with advanced technical analysis capabilities, comprehensive risk management, and enterprise-grade monitoring.

## 🚀 Features

- **Advanced Technical Analysis**: 11+ pre-built trading strategies with customizable parameters
- **Professional Risk Management**: Configurable stop-loss, take-profit, and position sizing
- **Multi-Symbol Trading**: Trade multiple cryptocurrencies simultaneously
- **Real-time Monitoring**: Comprehensive logging and trade monitoring
- **High Performance**: Asynchronous architecture with WebSocket connections
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Professional Configuration**: Environment-based configuration with validation
- **Comprehensive Testing**: Unit tests and integration tests included
- **Docker Support**: Easy deployment with Docker containers

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Trading Strategies](#trading-strategies)
- [Risk Management](#risk-management)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [License](#license)

## 🛠 Installation

### Prerequisites

- Python 3.8 or higher
- Binance account with Futures trading enabled
- Binance API key with Futures trading permissions

### Install from Source

```bash
# Clone the repository
git clone https://github.com/earthskyorg/binance-trading-bot.git
cd binance-trading-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Docker Installation

```bash
# Build the Docker image
docker build -t binance-trading-bot .

# Run with environment variables
docker run -d \
  --name trading-bot \
  -e BINANCE_API_KEY=your_api_key \
  -e BINANCE_API_SECRET=your_api_secret \
  binance-trading-bot
```

## 🚀 Quick Start

### 1. Setup Binance API

1. Create a [Binance account](https://accounts.binance.com/en/register)
2. Enable Two-Factor Authentication
3. Create an API key in API Management
4. Enable "Enable Trading" and "Enable Futures" permissions
5. **Do NOT enable "Enable Withdrawals"**

### 2. Configuration

Copy the example environment file and configure your settings:

```bash
cp env.example .env
```

Edit `.env` with your API credentials and trading preferences:

```env
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
TRADING_STRATEGY=tripleEMAStochasticRSIATR
LEVERAGE=10
ORDER_SIZE=3.0
```

### 3. Validate Configuration

```bash
trading-bot --validate-config
```

### 4. Run the Bot

```bash
# Run with default configuration
trading-bot

# Run with custom configuration file
trading-bot --config config.json

# Run in dry-run mode (no actual trades)
trading-bot --dry-run
```

## ⚙️ Configuration

The bot supports multiple configuration methods:

### Environment Variables

All configuration can be set via environment variables. See `env.example` for all available options.

### Configuration File

Create a JSON configuration file:

```json
{
  "api_key": "your_api_key",
  "api_secret": "your_api_secret",
  "trading_strategy": "tripleEMAStochasticRSIATR",
  "leverage": 10,
  "order_size": 3.0,
  "interval": "1m",
  "sl_mult": 1.5,
  "tp_mult": 1.0,
  "max_positions": 10
}
```

### Key Configuration Options

| Option | Description | Default | Range |
|--------|-------------|---------|-------|
| `TRADING_STRATEGY` | Trading strategy to use | `tripleEMAStochasticRSIATR` | See strategies list |
| `LEVERAGE` | Trading leverage | `10` | 1-125 |
| `ORDER_SIZE` | Position size as % of account | `3.0` | 0.1-100 |
| `INTERVAL` | Trading time frame | `1m` | 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d |
| `MAX_POSITIONS` | Maximum concurrent positions | `10` | 1-100 |
| `SL_MULT` | Stop-loss multiplier | `1.5` | 0.1+ |
| `TP_MULT` | Take-profit multiplier | `1.0` | 0.1+ |

## 📈 Trading Strategies

The bot includes 11 pre-built trading strategies:

1. **StochRSIMACD** - Stochastic RSI with MACD confirmation
2. **tripleEMAStochasticRSIATR** - Triple EMA with Stochastic RSI and ATR
3. **tripleEMA** - Triple Exponential Moving Average crossover
4. **breakout** - Volume-based breakout strategy
5. **stochBB** - Stochastic with Bollinger Bands
6. **goldenCross** - Golden Cross strategy with RSI filter
7. **candle_wick** - Candlestick wick analysis
8. **fibMACD** - Fibonacci retracement with MACD
9. **EMA_cross** - Simple EMA crossover
10. **heikin_ashi_ema2** - Heikin Ashi with EMA
11. **heikin_ashi_ema** - Heikin Ashi with EMA (variant)

### Creating Custom Strategies

Custom strategies can be implemented by extending the base strategy class:

```python
from binance_trading_bot.strategies.base import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def calculate_signals(self, data):
        # Your strategy logic here
        return trade_direction, stop_loss, take_profit
```

## 🛡️ Risk Management

### Stop-Loss and Take-Profit Options

- **USDT**: Fixed dollar amounts
- **%**: Percentage-based
- **ATR**: Average True Range based
- **Swing Levels**: Based on swing highs/lows

### Position Sizing

- Percentage-based position sizing
- Maximum position limits
- Margin requirement checking
- Trailing stop functionality

### Risk Controls

- Maximum concurrent positions
- Trading threshold limits
- Automatic position monitoring
- Emergency stop functionality

## 📊 Monitoring and Logging

### Logging Features

- Structured JSON logging
- Color-coded console output
- File rotation
- Trade event logging
- Error tracking with context

### Monitoring

- Real-time trade monitoring
- Performance metrics
- Win/loss tracking
- PnL reporting

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=binance_trading_bot

# Run specific test categories
pytest -m unit
pytest -m integration
```

## 🐳 Docker Deployment

### Docker Compose

```yaml
version: '3.8'
services:
  trading-bot:
    build: .
    environment:
      - BINANCE_API_KEY=${BINANCE_API_KEY}
      - BINANCE_API_SECRET=${BINANCE_API_SECRET}
      - TRADING_STRATEGY=tripleEMAStochasticRSIATR
      - LEVERAGE=10
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## ⚠️ Disclaimer

**This software is for educational purposes only. Trading cryptocurrencies involves substantial risk of loss. The authors are not responsible for any financial losses incurred through the use of this software. Always test thoroughly with small amounts before live trading.**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support & Contact

### Contact Information

Telegram: https://t.me/opensea712

<div style={{display : flex ; justify-content : space-evenly}}> 
    <a href="https://t.me/opensea712" target="_blank"><img alt="Telegram"
        src="https://img.shields.io/badge/Telegram-26A5E4?style=for-the-badge&logo=telegram&logoColor=white"/></a>
    <a href="https://discordapp.com/users/343286332446998530" target="_blank"><img alt="Discord"
        src="https://img.shields.io/badge/Discord-7289DA?style=for-the-badge&logo=discord&logoColor=white"/></a>
</div>

### Response Times

- 🚨 **Critical Issues**: Within 24 hours
- 🐛 **Bug Reports**: Within 2-3 business days
- 💡 **Feature Requests**: Within 1 week
- 📚 **Documentation Questions**: Within 2-3 business days
- 💼 **Enterprise Support**: Within 4 hours (business days)

## 🙏 Acknowledgments

- [python-binance](https://python-binance.readthedocs.io/) for Binance API integration
- [ta](https://technical-analysis-library-in-python.readthedocs.io/) for technical indicators
- [plotly](https://plotly.com/) for visualization capabilities

