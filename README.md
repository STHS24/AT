# TraderBot - MetaTrader 5 Automated Trading System

Complete automated trading system with **FastAPI backend**, **React frontend**, and **SQLite database** for local trading workstation.

## 🚀 Quick Start

### Full Stack Mode (Recommended)

1. **Setup** (one-time):
   ```bash
   setup-all.bat
   ```

2. **Start Backend** (Terminal 1):
   ```bash
   start-backend.bat
   ```

3. **Start Frontend** (Terminal 2):
   ```bash
   start-frontend.bat
   ```

4. **Access Dashboard**: http://localhost:3000

### Standalone Bot Mode

```bash
python main.py
```

## 📋 Table of Contents
- [Architecture](#architecture)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Trading Strategies](#trading-strategies)
- [Running the Bot](#running-the-bot)
- [API & WebSocket](#api--websocket)
- [Trading Modes](#trading-modes)
- [Monitoring](#monitoring)
- [Safety Features](#safety-features)
- [Troubleshooting](#troubleshooting)

## 🏗️ Architecture

```
TraderBot/
├── backend/              # FastAPI REST + WebSocket API
├── frontend/             # React + Tailwind Dashboard
├── strategies/           # Trading strategies
├── config/               # Configuration
├── logs/                 # Logs + SQLite database
└── main.py              # Standalone bot
```

### Technology Stack

**Backend:**
- FastAPI (REST API + WebSocket)
- SQLAlchemy (Async ORM)
- SQLite (Database)
- MetaTrader5 (Trading API)

**Frontend:**
- React 18
- Tailwind CSS
- React Query (Data fetching)
- WebSocket (Real-time updates)
- Recharts (Charts)

## ✨ Features

### Web Dashboard
- 🎮 **Bot Control** - Start/stop bot with live status
- 📊 **Live Price Feed** - Real-time bid/ask prices via WebSocket
- 💰 **Account Stats** - Balance, equity, margin, profit
- 📈 **Open Positions** - Active trades with P&L
- 📜 **Trade History** - Paginated trade log with filters
- 🔔 **Live Logs** - Real-time event stream
- 📱 **Responsive Design** - Works on desktop and mobile

### Trading Features
- 🤖 **Multiple Strategies** - Simple, MA, RSI, MACD
- 🎯 **Strategy Combination** - Majority, unanimous, weighted, any
- 🛡️ **Risk Management** - Dynamic lot sizing, SL/TP, daily limits
- 📊 **Performance Analytics** - Win rate, profit factor, statistics
- 💾 **Persistent Storage** - SQLite database for trade history
- 🔄 **Continuous Trading** - Automated trading loop
- ⚡ **Real-time Updates** - WebSocket streaming

## Installation

### Prerequisites
- Python 3.12 or higher
- MetaTrader 5 terminal installed and logged in
- Demo or live trading account

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/STHS24/AT.git
   cd TraderBot
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Verify installation**
   ```bash
   pytest tests/ -v
   ```

## Configuration

### Configuration File: `config/settings.json`

The configuration file contains three main sections:
1. **Basic Trading Settings**: Symbol, volume, deviation, intervals
2. **Strategy Configuration**: Multiple strategies with weights and combination methods
3. **Risk Management**: Dynamic lot sizing, SL/TP calculation, daily limits

### Basic Trading Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `symbol` | string | "EURUSD" | Trading symbol (e.g., EURUSD, GBPUSD, USDJPY) |
| `volume` | float | 0.1 | Trade volume in lots (used if dynamic sizing disabled) |
| `deviation` | integer | 50 | Maximum price deviation in points |
| `trade_interval_seconds` | integer | 60 | Time between trading checks (seconds) |
| `max_concurrent_trades` | integer | 10 | Maximum number of open positions |
| `enable_continuous_trading` | boolean | true | Enable continuous trading mode |

### Risk Management Parameters

The bot includes comprehensive risk management features:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `risk_percentage` | float | 1.0 | Percentage of account balance to risk per trade |
| `max_risk_percentage` | float | 5.0 | Maximum allowed risk percentage |
| `min_lot_size` | float | 0.01 | Minimum lot size for trades |
| `max_lot_size` | float | 1.0 | Maximum lot size for trades |
| `sl_method` | string | "atr" | Stop-loss calculation method: "atr", "fixed_pips", "percentage" |
| `tp_method` | string | "atr" | Take-profit calculation method: "atr", "fixed_pips", "percentage" |
| `fixed_sl_pips` | integer | 100 | Fixed SL distance in pips (if sl_method="fixed_pips") |
| `fixed_tp_pips` | integer | 200 | Fixed TP distance in pips (if tp_method="fixed_pips") |
| `atr_period` | integer | 14 | ATR calculation period |
| `atr_sl_multiplier` | float | 2.0 | ATR multiplier for stop-loss |
| `atr_tp_multiplier` | float | 3.0 | ATR multiplier for take-profit |
| `sl_percentage` | float | 0.5 | SL as percentage of entry price (if sl_method="percentage") |
| `tp_percentage` | float | 1.0 | TP as percentage of entry price (if tp_method="percentage") |
| `daily_loss_limit` | float | 500.0 | Maximum daily loss before trading stops ($) |
| `daily_profit_target` | float | 1000.0 | Daily profit target before trading stops ($) |
| `enable_daily_limits` | boolean | true | Enable/disable daily limits |
| `enable_dynamic_lot_sizing` | boolean | true | Enable dynamic lot size calculation |

#### Risk Management Methods

**1. ATR-Based (Recommended)**
- Uses Average True Range to adapt to market volatility
- SL = Entry ± (ATR × atr_sl_multiplier)
- TP = Entry ± (ATR × atr_tp_multiplier)
- Example: ATR=0.0034, SL multiplier=2.0 → SL distance = 34 pips

**2. Fixed Pips**
- Uses fixed pip distances regardless of volatility
- SL = Entry ± (fixed_sl_pips × point × 10)
- TP = Entry ± (fixed_tp_pips × point × 10)
- Example: fixed_sl_pips=100 → SL distance = 100 pips

**3. Percentage**
- Uses percentage of entry price
- SL = Entry × (1 ± sl_percentage/100)
- TP = Entry × (1 ± tp_percentage/100)
- Example: Entry=1.16000, sl_percentage=0.5 → SL = 1.15420

#### Dynamic Lot Sizing

When `enable_dynamic_lot_sizing` is true, the bot calculates optimal lot size:

```
lot_size = risk_amount / (sl_pips × pip_value_per_lot)

where:
  risk_amount = account_balance × (risk_percentage / 100)
  pip_value_per_lot = point_value × contract_size
```

Example:
- Account balance: $10,000
- Risk percentage: 1% → Risk amount: $100
- SL distance: 34 pips
- Pip value: $1 per pip per lot
- **Calculated lot size: 100 / (34 × 1) = 2.94 lots** (capped at max_lot_size)

#### Daily Limits

The bot tracks daily profit/loss and stops trading when limits are reached:
- **Loss Limit**: Stops trading if daily loss reaches `daily_loss_limit`
- **Profit Target**: Stops trading if daily profit reaches `daily_profit_target`
- **P/L Tracking**: Stored in `logs/daily_pnl.json`
- **Reset**: Automatically resets at midnight

### Recommended Settings

#### Conservative (Demo/Learning)
- **Risk**: 0.5% per trade
- **Daily Limits**: $100 loss, $200 profit
- **SL/TP**: Fixed pips (100/200)
- **Lot Size**: Fixed 0.01 lots
- **Interval**: 10 minutes

```json
{
  "symbol": "EURUSD",
  "volume": 0.01,
  "deviation": 50,
  "trade_interval_seconds": 600,
  "max_concurrent_trades": 1,
  "enable_continuous_trading": false,
  "risk_management": {
    "risk_percentage": 0.5,
    "min_lot_size": 0.01,
    "max_lot_size": 0.1,
    "sl_method": "fixed_pips",
    "tp_method": "fixed_pips",
    "fixed_sl_pips": 100,
    "fixed_tp_pips": 200,
    "daily_loss_limit": 100.0,
    "daily_profit_target": 200.0,
    "enable_daily_limits": true,
    "enable_dynamic_lot_sizing": false
  }
}
```

#### Moderate (Experienced Traders)
- **Risk**: 1% per trade
- **Daily Limits**: $500 loss, $1000 profit
- **SL/TP**: ATR-based (2x/3x)
- **Lot Size**: Dynamic (0.01-1.0)
- **Interval**: 1 minute

```json
{
  "symbol": "EURUSD",
  "volume": 0.1,
  "deviation": 50,
  "trade_interval_seconds": 60,
  "max_concurrent_trades": 3,
  "enable_continuous_trading": true,
  "risk_management": {
    "risk_percentage": 1.0,
    "min_lot_size": 0.01,
    "max_lot_size": 1.0,
    "sl_method": "atr",
    "tp_method": "atr",
    "atr_period": 14,
    "atr_sl_multiplier": 2.0,
    "atr_tp_multiplier": 3.0,
    "daily_loss_limit": 500.0,
    "daily_profit_target": 1000.0,
    "enable_daily_limits": true,
    "enable_dynamic_lot_sizing": true
  }
}
```

#### Aggressive (Advanced Only - Use with Caution)
- **Risk**: 2% per trade
- **Daily Limits**: $1000 loss, $2000 profit
- **SL/TP**: ATR-based (1.5x/2.5x) - Tighter stops
- **Lot Size**: Dynamic (0.01-5.0)
- **Interval**: 30 seconds

```json
{
  "symbol": "EURUSD",
  "volume": 0.5,
  "deviation": 100,
  "trade_interval_seconds": 30,
  "max_concurrent_trades": 5,
  "enable_continuous_trading": true,
  "risk_management": {
    "risk_percentage": 2.0,
    "min_lot_size": 0.01,
    "max_lot_size": 5.0,
    "sl_method": "atr",
    "tp_method": "atr",
    "atr_period": 14,
    "atr_sl_multiplier": 1.5,
    "atr_tp_multiplier": 2.5,
    "daily_loss_limit": 1000.0,
    "daily_profit_target": 2000.0,
    "enable_daily_limits": true,
    "enable_dynamic_lot_sizing": true
  }
}
```

⚠️ **Warning**: Aggressive settings can lead to significant losses. Only use with proper risk management and on demo accounts first.

## Trading Strategies

The bot uses a **multi-strategy system** that combines signals from multiple technical analysis strategies.

### Available Strategies

| Strategy | Type | Description | Default Weight |
|----------|------|-------------|----------------|
| **SimpleStrategy** | Momentum | Compares last two candle closes | 1.0 |
| **MAStrategy** | Trend | Moving Average Crossover (Golden/Death Cross) | 1.5 |
| **RSIStrategy** | Oscillator | RSI Overbought/Oversold detection | 1.2 |
| **MACDStrategy** | Momentum | MACD crossover with signal line | 1.0 |

### Strategy Configuration

Add `strategy_config` section to `config/settings.json`:

```json
{
  "symbol": "EURUSD",
  "volume": 0.1,
  "trade_interval_seconds": 60,
  "max_concurrent_trades": 10,
  "enable_continuous_trading": true,

  "strategy_config": {
    "combination_method": "majority",
    "enabled_strategies": ["SimpleStrategy", "MAStrategy", "RSIStrategy"],

    "SimpleStrategy": {
      "enabled": true,
      "weight": 1.0,
      "params": {
        "timeframe": "M1",
        "lookback": 20
      }
    },

    "MAStrategy": {
      "enabled": true,
      "weight": 1.5,
      "params": {
        "timeframe": "M5",
        "fast_period": 10,
        "slow_period": 20,
        "ma_type": "EMA"
      }
    },

    "RSIStrategy": {
      "enabled": true,
      "weight": 1.2,
      "params": {
        "timeframe": "M5",
        "period": 14,
        "oversold": 30,
        "overbought": 70
      }
    },

    "MACDStrategy": {
      "enabled": false,
      "weight": 1.0,
      "params": {
        "timeframe": "M15",
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9
      }
    }
  }
}
```

### Combination Methods

The bot combines signals from multiple strategies using one of four methods:

| Method | Description | Use Case |
|--------|-------------|----------|
| **unanimous** | All strategies must agree | High confidence, low frequency |
| **majority** | Most common signal wins (>50%) | Balanced approach |
| **weighted** | Signals weighted by importance | Customizable, requires tuning |
| **any** | Any strategy signal triggers action | High frequency, aggressive |

**Example Output:**
```
[SimpleStrategy] Upward momentum detected → BUY signal
[MAStrategy] No crossover (fast above slow) → NONE
[RSIStrategy] RSI in neutral zone (57.40) → NONE

[StrategyManager] Individual signals: {'SimpleStrategy': 'BUY', 'MAStrategy': 'NONE', 'RSIStrategy': 'NONE'}
[StrategyManager] Combined signal (majority): BUY
```

### Strategy Details

For detailed information about each strategy, see [`strategies/README.md`](strategies/README.md).

## Running the Bot

### Full Stack Mode (Web Dashboard)

**1. Start Backend:**
```bash
start-backend.bat
```
Backend runs on http://localhost:5000

**2. Start Frontend:**
```bash
start-frontend.bat
```
Dashboard available at http://localhost:3000

**3. Control via Dashboard:**
- Click "Start Bot" to begin trading
- Monitor live prices, positions, and logs
- View trade history and statistics
- Stop bot when needed

### Standalone Mode

**Single Trade Mode:**
```bash
python main.py
```
Execute one trade and exit.

**Continuous Trading Mode:**
Enable in `config/settings.json`:
```json
{
  "enable_continuous_trading": true
}
```

Then run:
```bash
python main.py
```

## API & WebSocket

### REST API Endpoints

**Bot Control:**
- `POST /bot/start` - Start trading bot
- `POST /bot/stop` - Stop trading bot
- `GET /bot/status` - Get bot status

**Statistics:**
- `GET /stats/account` - Account information
- `GET /stats/positions` - Open positions
- `GET /stats/strategies` - Strategy configuration

**History:**
- `GET /history/trades?page=1&page_size=50` - Trade history

**System:**
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

### WebSocket Events

Connect to `ws://localhost:5000/ws` for real-time updates:

**Message Types:**
- `price_update` - Live price data
- `trade_execution` - Trade executions
- `log_event` - Log messages
- `bot_status` - Bot status changes

**Example Message:**
```json
{
  "type": "price_update",
  "data": {
    "symbol": "EURUSD",
    "bid": 1.08450,
    "ask": 1.08452,
    "last": 1.08451,
    "volume": 1000,
    "time": "2025-10-31T12:00:00"
  },
  "timestamp": "2025-10-31T12:00:00.123456"
}
```

### Stopping the Bot

Press `CTRL+C` to gracefully shutdown:
```
⚠️  Shutdown signal received. Closing positions and exiting gracefully...
🔚 Shutting down after 42 iterations...
   Closing MT5 connection...
✅ Shutdown complete.
```

## Trading Modes

### Mode 1: Single Trade Execution

**Behavior:**
1. Connect to MT5
2. Check strategy signal
3. Execute one trade (if signal present)
4. Disconnect and exit

**Configuration:**
```json
{
  "enable_continuous_trading": false
}
```

**Best for:**
- Testing strategies
- Manual control
- Scheduled execution (cron/Task Scheduler)

### Mode 2: Continuous Trading Loop

**Behavior:**
1. Connect to MT5
2. Loop indefinitely:
   - Check for existing positions
   - Get strategy signal
   - Execute trade if conditions met
   - Wait for configured interval
3. Graceful shutdown on CTRL+C

**Configuration:**
```json
{
  "enable_continuous_trading": true,
  "trade_interval_seconds": 300
}
```

**Best for:**
- Automated trading
- 24/7 operation
- Production environments

## Monitoring

### Console Output

The bot provides real-time feedback:

```
🔌 Initializing MetaTrader 5...
✅ Connected to account #12345678 | Balance: 10000.00

✅ Symbol EURUSD ready for trading.

============================================================
🔄 Trading iteration at 2025-10-29 18:45:30
============================================================
[Strategy] Detected upward momentum → BUY signal.
📤 Sending BUY trade request...

✅ BUY executed successfully!
   Ticket: 123456789
   Price:  1.16045
   SL:     1.15945
   TP:     1.16245

📊 Open positions: 1/3

⏳ Waiting 300 seconds until next check...
```

### Log Files

The bot maintains multiple log formats for comprehensive tracking:

**1. Text Log** (`logs/trades.log`)
```
2025-10-29 18:45:30 | BUY          | 123456789    | Price: 1.16045 | SL: 1.15945 | TP: 1.16245 | Retcode: 10009
2025-10-29 18:50:45 | SELL         | 123456790    | Price: 1.16025 | SL: 1.16125 | TP: 1.15825 | Retcode: 10009
2025-10-29 18:55:12 | BUY_FAILED   | 0            | Price: 1.16050 | SL: 1.15950 | TP: 1.16250 | Retcode: 10030
```

**2. CSV Export** (`logs/trades.csv`)
- Excel-compatible format
- All trade details in structured columns
- Easy import for data analysis

**3. SQLite Database** (`logs/trades.db`)
- Efficient storage and querying
- 20+ fields per trade
- Supports complex analytics queries

**4. Daily P/L Tracking** (`logs/daily_pnl.json`)
```json
{
  "2025-10-29": {
    "pnl": 156.90,
    "trades": 67
  }
}
```

### Performance Analytics

The bot includes comprehensive performance analytics:

**Generate Performance Report**
```python
from analytics import PerformanceAnalytics

analytics = PerformanceAnalytics()
analytics.print_summary_report(days=30)
```

**Report Includes:**
- **Basic Statistics**: Total trades, win rate, profit factor, average P/L
- **Strategy Performance**: Performance breakdown by strategy
- **Time Analysis**: Daily and hourly performance patterns
- **Risk Metrics**: Max drawdown, Sharpe ratio, consecutive wins/losses
- **Best/Worst Trades**: Top 5 best and worst performing trades

**Automatic Report on Shutdown**
When you stop the bot (CTRL+C), it automatically generates and displays a performance report:

```
================================================================================
📊 PERFORMANCE REPORT - Last 7 Days
================================================================================

📈 BASIC STATISTICS
   Total Trades: 45
   Winning Trades: 28 (62.22%)
   Losing Trades: 17
   Total P/L: $1,245.50
   Average P/L: $27.68
   Profit Factor: 2.15

⚠️  RISK METRICS
   Max Drawdown: $125.00 (1.25%)
   Sharpe Ratio: 1.85
   Max Consecutive Wins: 7
   Max Consecutive Losses: 3

🎯 STRATEGY PERFORMANCE
   MAJORITY:
      Trades: 45 | Win Rate: 62.22% | P/L: $1,245.50
================================================================================
```

**Saved Reports**
All reports are automatically saved to `logs/reports/` in JSON format for later analysis.

### Monitoring Checklist

- ✅ Check console for errors
- ✅ Monitor `logs/trades.log` for trade history
- ✅ Review `logs/trades.csv` for detailed analysis
- ✅ Check `logs/daily_pnl.json` for daily performance
- ✅ Generate performance reports weekly
- ✅ Verify MT5 terminal shows correct positions
- ✅ Check account balance regularly
- ✅ Review strategy performance metrics

## Safety Features

### 1. Position Tracking
- **Prevents duplicate trades** on the same symbol
- Checks for existing positions before opening new ones

### 2. Max Concurrent Trades
- **Limits total open positions** to configured maximum
- Prevents overexposure and excessive risk

### 3. Graceful Shutdown
- **CTRL+C handling** for clean exit
- Properly closes MT5 connection
- No orphaned processes

### 4. Error Handling
- **Connection validation** before trading
- **Symbol verification** before execution
- **Order result checking** with detailed logging

### 5. Trade Logging
- **Complete audit trail** of all trades
- **Success and failure logging**
- **Timestamp and price recording**

## Troubleshooting

### Issue: "MT5 initialization failed"

**Cause**: MetaTrader 5 not running or not logged in

**Solution**:
1. Open MetaTrader 5 terminal
2. Log in to your account
3. Ensure terminal is not minimized
4. Run the bot again

### Issue: "Could not select symbol EURUSD"

**Cause**: Symbol not available in your broker's market watch

**Solution**:
1. Open MT5 Market Watch (CTRL+M)
2. Right-click → "Show All"
3. Find your symbol and enable it
4. Or change symbol in `config/settings.json`

### Issue: "Already have an open position"

**Cause**: Position tracking preventing duplicate trades

**Solution**:
- This is **normal behavior** (safety feature)
- Close existing position in MT5 if you want to open new one
- Or wait for position to close automatically (SL/TP)

### Issue: "Max concurrent trades reached"

**Cause**: Hit the configured limit for open positions

**Solution**:
- Close some positions manually
- Or increase `max_concurrent_trades` in config
- Or wait for positions to close automatically

### Issue: Trade execution failed (Retcode: 10030)

**Cause**: Invalid stops (SL/TP too close to market price)

**Solution**:
- Check broker's minimum stop level
- Adjust SL/TP calculation in `main.py`
- Increase deviation in config

### Issue: "No trade signal from strategy"

**Cause**: Strategy conditions not met

**Solution**:
- This is **normal behavior**
- Strategy only trades when conditions are favorable
- Wait for next iteration in continuous mode

## Best Practices

### 1. Start with Demo Account
- Test thoroughly before using real money
- Verify strategy performance
- Understand bot behavior

### 2. Use Conservative Settings
- Start with small volume (0.01 lots)
- Limit concurrent trades (1-2)
- Longer intervals (5-10 minutes)

### 3. Monitor Regularly
- Check logs daily
- Review performance weekly
- Adjust settings based on results

### 4. Backup Configuration
- Keep backup of `config/settings.json`
- Document any custom changes
- Version control your modifications

### 5. Test After Updates
- Run test suite after any changes
- Verify on demo account first
- Monitor closely after deployment

## Advanced Usage

### Running as Windows Service

Use Task Scheduler to run bot automatically:

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., "At startup")
4. Action: Start a program
   - Program: `D:\Projects\TraderBot\venv\Scripts\python.exe`
   - Arguments: `main.py`
   - Start in: `D:\Projects\TraderBot`

### Running as Linux Service

Create systemd service file `/etc/systemd/system/traderbot.service`:

```ini
[Unit]
Description=TraderBot MT5 Trading Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/TraderBot
ExecStart=/home/youruser/TraderBot/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable traderbot
sudo systemctl start traderbot
sudo systemctl status traderbot
```

## Support

- **Issues**: https://github.com/STHS24/AT/issues
- **Documentation**: See ROADMAP.md for planned features
- **Tests**: Run `pytest tests/ -v` to verify functionality

## Disclaimer

**Trading involves risk. This bot is provided as-is without any guarantees. Always test on demo accounts first. Never trade with money you cannot afford to lose.**

