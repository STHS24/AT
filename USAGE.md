# TraderBot Usage Guide

Complete guide for using the TraderBot MetaTrader 5 automated trading system with real-time dashboard.

## Table of Contents
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Bot](#running-the-bot)
- [Dashboard Usage](#dashboard-usage)
- [Trading Strategies](#trading-strategies)
- [Risk Management](#risk-management)
- [Monitoring & Logs](#monitoring--logs)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Install Dependencies
```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install Python packages
pip install -r requirements.txt

# Install .NET 8 SDK for dashboard (if not installed)
# Download from: https://dotnet.microsoft.com/download/dotnet/8.0
```

### 2. Configure Settings
Edit `config/settings.json`:
```json
{
  "symbol": "EURUSD",
  "volume": 0.1,
  "enable_continuous_trading": true,
  "trade_interval_seconds": 60
}
```

### 3. Run the Bot
```bash
# Terminal 1: Start the trading bot
python main.py

# Terminal 2: Start the dashboard (optional)
cd TraderDashboard
dotnet run
```

---

## Installation

### Prerequisites
- **Python 3.12+** - [Download](https://www.python.org/downloads/)
- **MetaTrader 5** - [Download](https://www.metatrader5.com/en/download)
- **.NET 8 SDK** (for dashboard) - [Download](https://dotnet.microsoft.com/download/dotnet/8.0)
- **MT5 Account** - Demo or live trading account

### Setup Steps

#### 1. Clone Repository
```bash
git clone https://github.com/STHS24/AT.git
cd TraderBot
```

#### 2. Create Virtual Environment
```bash
python -m venv .venv
```

#### 3. Activate Virtual Environment
**Windows:**
```bash
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

#### 4. Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### 5. Verify Installation
```bash
python -c "import MetaTrader5 as mt5; print('MT5 version:', mt5.__version__)"
```

#### 6. Build Dashboard (Optional)
```bash
cd TraderDashboard
dotnet restore
dotnet build
cd ..
```

---

## Configuration

### Main Configuration File: `config/settings.json`

#### Basic Settings
```json
{
  "symbol": "EURUSD",              // Trading pair
  "volume": 0.1,                   // Default lot size (if not using dynamic sizing)
  "deviation": 50,                 // Max price deviation in points
  "trade_interval_seconds": 60,    // Time between trading iterations
  "max_concurrent_trades": 10,     // Maximum open positions
  "enable_continuous_trading": true // Enable continuous trading mode
}
```

#### Strategy Configuration
```json
{
  "strategy_config": {
    "combination_method": "majority",  // unanimous, majority, weighted, any
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
    }
  }
}
```

#### Risk Management Configuration
```json
{
  "risk_management": {
    "risk_percentage": 1.0,           // Risk per trade (% of balance)
    "max_risk_percentage": 5.0,       // Maximum risk allowed
    "min_lot_size": 0.01,             // Minimum position size
    "max_lot_size": 1.0,              // Maximum position size
    
    "sl_method": "atr",               // atr, fixed_pips, percentage
    "tp_method": "atr",               // atr, fixed_pips, percentage
    
    "fixed_sl_pips": 100,             // SL in pips (if using fixed_pips)
    "fixed_tp_pips": 200,             // TP in pips (if using fixed_pips)
    
    "atr_period": 14,                 // ATR calculation period
    "atr_sl_multiplier": 2.0,         // SL = ATR * multiplier
    "atr_tp_multiplier": 3.0,         // TP = ATR * multiplier
    
    "sl_percentage": 0.5,             // SL as % of price
    "tp_percentage": 1.0,             // TP as % of price
    
    "daily_loss_limit": 500.0,        // Stop trading after $500 loss
    "daily_profit_target": 1000.0,    // Stop trading after $1000 profit
    "enable_daily_limits": true,      // Enable daily limits
    
    "enable_dynamic_lot_sizing": true // Calculate lot size based on risk
  }
}
```

---

## Running the Bot

### Mode 1: Bot Only (No Dashboard)

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Run the bot
python main.py
```

**Expected Output:**
```
🔌 Initializing MetaTrader 5...
✅ Connected to account #5041936808 | Balance: 10000.00
✅ Symbol EURUSD ready for trading.
🔁 Starting continuous trading mode...
   Trade interval: 60 seconds
   Max concurrent trades: 10
   Press CTRL+C to stop gracefully
```

### Mode 2: Bot + Dashboard (Recommended)

**Terminal 1: Start Bot**
```bash
.venv\Scripts\python.exe main.py
```

**Terminal 2: Start Dashboard**
```bash
cd TraderDashboard
dotnet run
```

**Expected Output (Bot):**
```
🚀 Dashboard WebSocket server started
[Dashboard] Listening on ws://localhost:5000
🔁 Starting continuous trading mode...
```

**Expected Output (Dashboard):**
- Dashboard window opens
- Connects to `ws://localhost:5000`
- Displays real-time trading data

### Stopping the Bot

**Graceful Shutdown:**
- Press `CTRL+C` in the bot terminal
- Bot will close all positions and generate performance report

**Force Stop:**
- Close terminal window (not recommended - positions remain open)

---

## Dashboard Usage

### Dashboard Features

#### Header Section
- **🟢 Status Indicator** - Color-coded bot status
  - Green = Running
  - Orange = Paused
  - Red = Error
  - Gray = Disconnected
- **💰 Balance** - Current account balance
- **📈 Equity** - Current account equity
- **💵 Profit** - Current floating profit/loss

#### Main Content
- **📋 Positions Table** - All open positions
  - Symbol (e.g., EURUSD)
  - Side (Long/Short)
  - Profit/Loss
- **📈 Equity Chart** - Live equity curve
  - Updates every trading iteration
  - Shows equity over time

#### Bottom Section
- **🎮 Control Buttons**
  - ▶️ **START/RESUME** - Resume trading if paused
  - ⏸️ **PAUSE** - Pause trading (keeps positions open)
  - ⏹️ **STOP** - Stop trading (same as pause)
  - 🌙 **THEME** - Toggle dark/light mode
- **📝 Activity Log** - Recent actions and logs
  - Trade executions
  - Signal detections
  - System messages

### Dashboard Controls

#### Pause Trading
1. Click **⏸️ PAUSE** button
2. Bot stops opening new positions
3. Existing positions remain open
4. Status changes to "Paused"

#### Resume Trading
1. Click **▶️ START** button
2. Bot resumes normal trading
3. Status changes to "Running"

#### Change Theme
1. Click **🌙 THEME** button
2. Toggles between dark and light mode
3. Preference saved automatically

### Dashboard Connection

**WebSocket URL:** `ws://localhost:5000`

**Auto-Reconnect:**
- Dashboard automatically reconnects if connection is lost
- Reconnection attempts every 5 seconds
- No manual intervention required

**Data Update Frequency:**
- **Trading Iterations:** Every 60 seconds (configurable)
- **Dashboard Updates:** After each trading iteration
- **Chart Updates:** Real-time with each broadcast

---

## Trading Strategies

### Available Strategies

#### 1. Simple Strategy
- **Logic:** Compares current price to previous candles
- **Buy Signal:** Upward momentum (price > previous)
- **Sell Signal:** Downward momentum (price < previous)
- **Timeframe:** M1 (1 minute)
- **Parameters:** `lookback` (default: 20)

#### 2. Moving Average (MA) Strategy
- **Logic:** Fast MA crosses slow MA
- **Buy Signal:** Golden cross (fast crosses above slow)
- **Sell Signal:** Death cross (fast crosses below slow)
- **Timeframe:** M5 (5 minutes)
- **Parameters:**
  - `fast_period` (default: 10)
  - `slow_period` (default: 20)
  - `ma_type` (EMA or SMA)

#### 3. RSI Strategy
- **Logic:** Relative Strength Index overbought/oversold
- **Buy Signal:** RSI < oversold threshold (default: 30)
- **Sell Signal:** RSI > overbought threshold (default: 70)
- **Timeframe:** M5 (5 minutes)
- **Parameters:**
  - `period` (default: 14)
  - `oversold` (default: 30)
  - `overbought` (default: 70)

#### 4. MACD Strategy
- **Logic:** MACD line crosses signal line
- **Buy Signal:** Bullish crossover (MACD crosses above signal)
- **Sell Signal:** Bearish crossover (MACD crosses below signal)
- **Timeframe:** M15 (15 minutes)
- **Parameters:**
  - `fast_period` (default: 12)
  - `slow_period` (default: 26)
  - `signal_period` (default: 9)

### Strategy Combination Methods

#### Unanimous
- **All** enabled strategies must agree
- Most conservative approach
- Fewer trades, higher confidence

#### Majority
- **More than 50%** of strategies must agree
- Balanced approach (default)
- Moderate trade frequency

#### Weighted
- Each strategy has a weight
- Weighted sum determines signal
- Allows prioritizing certain strategies

#### Any
- **At least one** strategy signals
- Most aggressive approach
- Highest trade frequency

---

## Risk Management

### Dynamic Lot Sizing

**Formula:**
```
Lot Size = (Account Balance × Risk %) / (SL Distance in Pips × Pip Value)
```

**Example:**
- Balance: $10,000
- Risk: 1% = $100
- SL Distance: 50 pips
- Pip Value: $10 (for 1 lot EURUSD)
- **Lot Size = $100 / (50 × $10) = 0.2 lots**

### Stop Loss / Take Profit Methods

#### ATR Method (Recommended)
- **SL:** Current Price ± (ATR × SL Multiplier)
- **TP:** Current Price ± (ATR × TP Multiplier)
- **Advantage:** Adapts to market volatility

#### Fixed Pips Method
- **SL:** Fixed distance in pips (e.g., 100 pips)
- **TP:** Fixed distance in pips (e.g., 200 pips)
- **Advantage:** Simple and predictable

#### Percentage Method
- **SL:** Percentage of entry price (e.g., 0.5%)
- **TP:** Percentage of entry price (e.g., 1.0%)
- **Advantage:** Scales with price level

### Daily Limits

**Loss Limit:**
- Bot stops trading after reaching daily loss limit
- Default: $500
- Prevents catastrophic losses

**Profit Target:**
- Bot stops trading after reaching daily profit target
- Default: $1000
- Locks in profits

**Reset:**
- Limits reset at midnight (server time)
- Tracked in `logs/daily_pnl.json`

---

## Monitoring & Logs

### Log Files

#### `logs/trades.log`
- Human-readable text log
- All trading actions with timestamps
- Trade executions, closures, errors

#### `logs/trades.csv`
- CSV format for Excel/analysis
- All trade data in tabular format
- Easy to import into spreadsheets

#### `logs/trades.db`
- SQLite database
- Structured trade data
- Fast querying and analysis

#### `logs/daily_pnl.json`
- Daily profit/loss tracking
- Resets at midnight
- Used for daily limits

#### `logs/reports/`
- Performance reports
- Generated on bot shutdown
- JSON format with statistics

### Performance Reports

**Generated on shutdown (CTRL+C):**
```
📊 Performance Report:
   Total Trades: 150
   Win Rate: 62.5%
   Profit Factor: 1.85
   Total P/L: $1,250.00
   Average P/L: $8.33
   Max Profit: $150.00
   Max Loss: -$80.00
```

**Report includes:**
- Basic statistics (trades, win rate, profit factor)
- Strategy performance comparison
- Time-based analysis (daily, hourly)
- Risk metrics (max drawdown, Sharpe ratio)
- Best/worst trades

---

## Troubleshooting

### Bot Won't Start

**Issue:** `ModuleNotFoundError: No module named 'MetaTrader5'`
**Solution:**
```bash
# Activate virtual environment first
.venv\Scripts\activate
pip install -r requirements.txt
```

**Issue:** `MT5 initialization failed`
**Solution:**
- Ensure MetaTrader 5 is installed and running
- Log in to your MT5 account
- Check if MT5 terminal is not frozen

### Dashboard Won't Connect

**Issue:** Dashboard shows "Disconnected"
**Solution:**
1. Check if bot is running
2. Verify WebSocket server started: Look for "🚀 Dashboard WebSocket server started"
3. Check firewall settings
4. Restart both bot and dashboard

**Issue:** `Connection refused on ws://localhost:5000`
**Solution:**
```bash
# Check if port 5000 is in use
netstat -an | findstr 5000

# If port is busy, kill the process or change port in websocket_server.py
```

### Trading Issues

**Issue:** Bot not opening trades
**Solution:**
1. Check if daily limits reached: Look for "Daily limit reached" message
2. Verify strategies are enabled in `config/settings.json`
3. Check if max concurrent trades limit reached
4. Ensure sufficient account balance

**Issue:** Trades failing with error code
**Solution:**
- **10004:** Requote - Price changed, retry
- **10006:** Request rejected - Check account permissions
- **10013:** Invalid request - Check lot size and SL/TP
- **10014:** Invalid volume - Adjust lot size within limits
- **10015:** Invalid price - Check symbol specifications

### Performance Issues

**Issue:** Bot running slow
**Solution:**
- Increase `trade_interval_seconds` in config
- Disable unused strategies
- Reduce ATR calculation frequency

**Issue:** High memory usage
**Solution:**
- Clear old log files from `logs/` directory
- Reduce number of enabled strategies
- Restart bot periodically

---

## Additional Resources

- **GitHub Repository:** https://github.com/STHS24/AT
- **MT5 Documentation:** https://www.mql5.com/en/docs/integration/python_metatrader5
- **Support:** Open an issue on GitHub

---

**Happy Trading! 📈💹🚀**

