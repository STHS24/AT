# TraderBot - Automated Trading System

Professional MetaTrader 5 automated trading bot with real-time dashboard, multiple strategies, risk management, and comprehensive analytics.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![.NET](https://img.shields.io/badge/.NET-8.0-purple.svg)](https://dotnet.microsoft.com/download/dotnet/8.0)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-86%20passing-brightgreen.svg)](tests/)

---

## 🚀 Features

### ✅ Core Trading
- **MetaTrader 5 Integration** - Seamless connection to MT5 platform
- **Multiple Trading Strategies** - MA, RSI, MACD, and custom strategies
- **Strategy Manager** - Combine strategies with 4 methods (unanimous, majority, weighted, any)
- **Continuous Trading** - Automated trading with configurable intervals
- **Position Management** - Track and manage multiple open positions

### 💰 Risk Management
- **Dynamic Lot Sizing** - Calculate position size based on risk percentage
- **Automatic SL/TP** - Three methods: ATR, fixed pips, percentage
- **Daily Limits** - Auto-stop trading after loss/profit limits
- **Trade Validation** - Validate trades before execution
- **ATR Calculation** - Volatility-based risk management

### 📊 Logging & Analytics
- **Multi-Format Logging** - Text, CSV, and SQLite database
- **Performance Reports** - Win rate, profit factor, Sharpe ratio
- **Strategy Analysis** - Compare performance across strategies
- **Time-Based Analysis** - Daily and hourly performance breakdown
- **Risk Metrics** - Max drawdown, consecutive wins/losses

### 🖥️ Real-Time Dashboard
- **Live Monitoring** - Real-time balance, equity, profit display
- **Interactive Controls** - Pause, resume, stop trading from dashboard
- **Equity Chart** - Live equity curve visualization
- **Position Table** - View all open positions with P/L
- **Activity Log** - Recent actions and system messages
- **Auto-Reconnect** - Automatic reconnection on connection loss

---

## 📋 Quick Start

### Prerequisites
- **Python 3.12+** - [Download](https://www.python.org/downloads/)
- **MetaTrader 5** - [Download](https://www.metatrader5.com/en/download)
- **.NET 8 SDK** (for dashboard) - [Download](https://dotnet.microsoft.com/download/dotnet/8.0)
- **MT5 Account** - Demo or live trading account

### Installation

```bash
# Clone repository
git clone https://github.com/STHS24/AT.git
cd TraderBot

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Build dashboard (optional)
cd TraderDashboard
dotnet restore
dotnet build
cd ..
```

### Configuration

Edit `config/settings.json`:
```json
{
  "symbol": "EURUSD",
  "volume": 0.1,
  "enable_continuous_trading": true,
  "trade_interval_seconds": 60
}
```

### Run

```bash
# Terminal 1: Start bot
python main.py

# Terminal 2: Start dashboard (optional)
cd TraderDashboard
dotnet run
```

---

## 📖 Documentation

- **[USAGE.md](USAGE.md)** - Complete usage guide with all features
- **[CHANGELOG.md](CHANGELOG.md)** - Version history
- **[ROADMAP.md](ROADMAP.md)** - Development roadmap
- **[INTEGRATION_HISTORY.md](INTEGRATION_HISTORY.md)** - Detailed milestone history

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Test results: 86 passing, 17 skipped
```

---

## 📁 Project Structure

```
TraderBot/
├── main.py                    # Main bot entry point
├── websocket_server.py        # WebSocket server
├── risk_manager.py            # Risk management
├── trade_logger.py            # Multi-format logging
├── analytics.py               # Performance analytics
├── strategies/                # Trading strategies
│   ├── simple_strategy.py
│   ├── ma_strategy.py
│   ├── rsi_strategy.py
│   ├── macd_strategy.py
│   └── strategy_manager.py
├── config/settings.json       # Configuration
├── logs/                      # Logs and reports
├── tests/                     # Test suite
└── TraderDashboard/           # .NET 8 dashboard
```

---

## 🎯 Key Features Explained

### Multiple Strategies
- **Simple Strategy** - Price momentum
- **MA Strategy** - Moving average crossover
- **RSI Strategy** - Overbought/oversold
- **MACD Strategy** - MACD crossover

### Strategy Combination
- **Unanimous** - All strategies agree
- **Majority** - >50% agree (default)
- **Weighted** - Weighted voting
- **Any** - At least one signals

### Risk Management
- **Dynamic Lot Sizing** - Based on risk %
- **ATR-Based SL/TP** - Adapts to volatility
- **Daily Limits** - Auto-stop after limits
- **Trade Validation** - Pre-execution checks

### Dashboard
- **Real-Time Monitoring** - Live updates
- **Interactive Controls** - Pause/resume
- **Equity Chart** - Live visualization
- **Auto-Reconnect** - Connection resilience

---

## 🚀 Quick Examples

### Example 1: Conservative Trading
```json
{
  "strategy_config": {
    "combination_method": "unanimous"
  },
  "risk_management": {
    "risk_percentage": 0.5,
    "daily_loss_limit": 200.0
  }
}
```

### Example 2: Aggressive Trading
```json
{
  "strategy_config": {
    "combination_method": "any"
  },
  "risk_management": {
    "risk_percentage": 2.0,
    "daily_loss_limit": 1000.0
  }
}
```

---

## 📊 Performance

**Test Results:**
- 86 passing tests
- 17 skipped tests
- ~3000+ lines of code
- Comprehensive test coverage

**Resource Usage:**
- CPU: <5% during trading
- Memory: ~100 MB
- Network: Minimal (MT5 API only)

---

## 🛡️ Safety

- ✅ Always test on demo account first
- ✅ Start with small lot sizes
- ✅ Use stop-loss on all trades
- ✅ Monitor bot regularly
- ✅ Set appropriate daily limits

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

## ⚠️ Disclaimer

This bot is for educational purposes. Always test on a demo account first. Trading involves risk. Use at your own risk.

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/STHS24/AT/issues)
- **Documentation:** [USAGE.md](USAGE.md)
- **Tests:** `pytest tests/ -v`

---

**Made with ❤️ for automated trading**

