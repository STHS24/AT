# TraderBot Usage Guide

Complete guide for using the TraderBot MetaTrader 5 automated trading system with **AI-Powered Decision Making**.

## 🤖 AI-Powered Trading

**NEW in v0.7.0**: TraderBot now uses Large Language Models (LLMs) to make intelligent trading decisions based on comprehensive market analysis, replacing traditional signal-based strategies.

### Key Features
- **Holistic Analysis**: AI considers all market factors simultaneously
- **Explainable Decisions**: Every trade includes detailed reasoning
- **Adaptive**: No manual strategy tuning required
- **Risk-Aware**: AI respects all risk management rules
- **Multi-Timeframe**: Analyzes M1, M5, M15, and H1 data together

## Table of Contents
- [Installation](#installation)
- [AI Strategy Configuration](#ai-strategy-configuration)
- [Configuration](#configuration)
- [Trading Strategies](#trading-strategies)
- [Running the Bot](#running-the-bot)
- [Trading Modes](#trading-modes)
- [Monitoring](#monitoring)
- [Safety Features](#safety-features)
- [Troubleshooting](#troubleshooting)

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

## AI Strategy Configuration

### Overview

The AI Strategy uses OpenRouter API to access Large Language Models (LLMs) for trading decisions. The AI analyzes comprehensive market data including:

- **Current Price**: Bid, ask, spread
- **Technical Indicators**: RSI, MACD, Moving Averages, ATR, Bollinger Bands
- **Multi-Timeframe Analysis**: M1, M5, M15, H1 price action and trends
- **Current Positions**: Open trades, P/L, pip calculations
- **Account Status**: Balance, equity, margin, daily P/L
- **Risk Constraints**: Risk limits, exposure, remaining capacity

### Configuration Parameters

The AI strategy is configured in `config/settings.json` under `strategy_config.AIStrategy`:

```json
{
  "strategy_config": {
    "combination_method": "majority",
    "enabled_strategies": ["AIStrategy"],

    "AIStrategy": {
      "enabled": true,
      "weight": 1.0,
      "params": {
        "api_key": "your-openrouter-api-key",
        "model": "deepseek/deepseek-chat-v3.1:free",
        "confidence_threshold": 0.7,
        "temperature": 0.7,
        "timeout": 30,
        "max_retries": 3
      }
    }
  }
}
```

### AI Strategy Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | string | Required | OpenRouter API key for LLM access |
| `model` | string | "deepseek/deepseek-chat-v3.1:free" | LLM model to use (free tier available) |
| `confidence_threshold` | float | 0.7 | Minimum confidence (0.0-1.0) required to execute trade |
| `temperature` | float | 0.7 | LLM creativity parameter (0.0=deterministic, 1.0=creative) |
| `timeout` | integer | 30 | API request timeout in seconds |
| `max_retries` | integer | 3 | Maximum retry attempts for failed API calls |
| `enable_position_management` | boolean | true | Enable AI-powered position management |
| `min_hold_time_minutes` | integer | 5 | Minimum time to hold position before AI can close it |
| `position_check_interval` | integer | 1 | How often to analyze positions (every N iterations) |

### Token Usage Optimization

The AI strategy uses **highly optimized prompts** to minimize token usage and API costs:

**Token Savings:**
- System prompt: ~100 tokens (60% reduction from verbose format)
- User prompt: ~66 tokens (87% reduction from verbose format)
- Position prompt: ~87 tokens (78% reduction from verbose format)
- **Total savings: 78% fewer tokens per request**

**Impact at 5-second analysis interval (12 requests/minute):**
- Old: 9,000 tokens/minute
- New: 1,992 tokens/minute
- **Savings: 7,008 tokens/minute**
- **Daily savings: ~10M tokens** (~$1.00/day at typical pricing)

**Benefits:**
- ✅ 78% lower API costs
- ✅ Fewer rate limit errors
- ✅ Faster response times
- ✅ Can analyze market more frequently
- ✅ Better reliability

**Example Compact Format:**
```
EURUSD
Price: 1.0845/1.08452 (spread 0.2p)
Indicators: RSI:55.5(Neutral), MACD:0.00002(Bullish), MA20:Above, ATR:1.5p(Low)
Trends: M5:Uptrend(+0.12%), M15:Uptrend(+0.18%)
Positions: None
Account: Bal $10000, Eq $10000, DayPL $125.50
Risk: 1.0%/trade, 0/10 trades, $374 remaining

Decide: BUY/SELL/NONE? Respond JSON.
```

### Getting an API Key

1. **Sign up at OpenRouter**: Visit [https://openrouter.ai/](https://openrouter.ai/)
2. **Create API Key**: Go to Keys section and generate a new API key
3. **Free Tier Available**: DeepSeek model is free to use (with rate limits)
4. **Add to Config**: Copy the API key to `config/settings.json`
5. **Monitor Usage**: Check OpenRouter dashboard for token usage and costs

**Current API Key** (included in config):
```
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
```

### How AI Makes Decisions

1. **Data Collection**: Market Analyzer gathers comprehensive market context
2. **Prompt Building**: LLM Client formats data into structured prompt
3. **AI Analysis**: LLM analyzes all factors and provides decision
4. **Confidence Check**: Decision filtered based on confidence threshold
5. **Execution**: High-confidence decisions passed to trading system
6. **Logging**: All decisions and reasoning logged to `logs/ai_decisions.jsonl`

### AI Response Format

The AI returns structured decisions:

```json
{
  "decision": "BUY",
  "reasoning": "Strong bullish momentum with RSI oversold at 28, MACD showing bullish crossover, and uptrend confirmed across M5 and M15 timeframes. Price bounced off lower Bollinger Band indicating potential reversal.",
  "confidence": 0.85,
  "key_factors": [
    "RSI oversold (28) indicating potential reversal",
    "MACD bullish crossover on M5",
    "Price at lower Bollinger Band support",
    "Uptrend confirmed on M15 timeframe"
  ]
}
```

### AI Position Management

The AI doesn't just decide when to enter trades - it also actively manages open positions!

#### How It Works

1. **Every Trading Iteration**: Before generating new signals, the AI analyzes all open positions
2. **Comprehensive Analysis**: AI evaluates:
   - Current market conditions vs entry conditions
   - Unrealized P/L and position duration
   - Technical indicator changes since entry
   - Risk/reward ratio and profit targets
   - Market volatility and momentum shifts

3. **Three Possible Actions**:
   - **HOLD**: Keep position open (market conditions still favorable)
   - **CLOSE**: Close entire position (conditions changed, protect profit/loss)
   - **CLOSE_PARTIAL**: Close part of position (lock in some profit, let rest run)

#### Position Management Response Format

```json
{
  "action": "CLOSE_PARTIAL",
  "reasoning": "Position is profitable at +45 pips. RSI showing overbought at 72 and MACD momentum weakening. Close 50% to lock in profit while keeping upside potential if trend continues.",
  "confidence": 0.82,
  "partial_percentage": 0.5
}
```

#### Configuration

**Enable/Disable Position Management**:
```json
"enable_position_management": true
```

**Minimum Hold Time** (prevents premature exits):
```json
"min_hold_time_minutes": 5
```

**Position Check Interval**:
```json
"position_check_interval": 1  // Check every iteration
```

#### Example Scenarios

**Scenario 1: Profitable Position, Trend Continues**
- Action: HOLD
- Reasoning: "Position profitable at +30 pips. Trend remains strong with MACD bullish and price above MA20. Hold for further gains."

**Scenario 2: Trend Reversal Detected**
- Action: CLOSE
- Reasoning: "Trend reversed. RSI crossed below 50, MACD bearish crossover, price broke below MA50. Close to protect profit."

**Scenario 3: Partial Profit Taking**
- Action: CLOSE_PARTIAL (50%)
- Reasoning: "Strong profit at +60 pips but momentum slowing. Close 50% to lock in gains, let remaining 50% run with trailing stop."

#### Benefits

- **Profit Protection**: AI exits when conditions deteriorate
- **Trend Following**: Holds winners when trend continues
- **Risk Management**: Reduces exposure when uncertainty increases
- **Partial Closes**: Lock in profits while keeping upside potential
- **Explainable**: Every decision includes detailed reasoning

### Confidence Threshold

The `confidence_threshold` parameter filters out low-confidence trades:

- **0.7 (Default)**: Only trades when AI is 70%+ confident
- **0.8 (Conservative)**: Higher threshold, fewer but higher quality trades
- **0.6 (Aggressive)**: Lower threshold, more trades but potentially lower quality

**Recommendation**: Start with 0.7 and adjust based on performance.

### Monitoring AI Decisions

All AI decisions are logged to `logs/ai_decisions.jsonl` with:
- Timestamp
- Symbol
- Decision (BUY/SELL/NONE)
- Reasoning
- Confidence score
- Key factors
- Model used
- Market context

**Example log entry**:
```json
{
  "timestamp": "2025-11-05T10:30:45",
  "symbol": "EURUSD",
  "decision": "BUY",
  "reasoning": "Strong bullish signals...",
  "confidence": 0.85,
  "key_factors": ["RSI oversold", "MACD bullish"],
  "model": "deepseek/deepseek-chat-v3.1:free",
  "market_context": {...}
}
```

### Switching Between AI and Traditional Strategies

To switch back to traditional strategies, update `config/settings.json`:

```json
{
  "strategy_config": {
    "enabled_strategies": ["SimpleStrategy", "MAStrategy", "RSIStrategy"],

    "AIStrategy": {
      "enabled": false,
      ...
    },

    "SimpleStrategy": {
      "enabled": true,
      ...
    }
  }
}
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
| `analysis_interval_seconds` | integer | 5 | How often AI analyzes the market (seconds) |
| `trade_interval_seconds` | integer | 60 | Minimum cooldown between trades (seconds) |
| `enable_urgent_bypass` | boolean | true | Allow urgent trades to bypass cooldown |
| `max_concurrent_trades` | integer | 10 | Maximum number of open positions |
| `enable_continuous_trading` | boolean | true | Enable continuous trading mode |

### Timing Architecture

The bot uses a **dual-interval system** for optimal performance:

#### Analysis Interval (Default: 5 seconds)
- **Purpose**: How often the AI analyzes the market
- **Frequency**: Every 5 seconds (12 times per minute)
- **What happens**:
  - AI collects market data
  - Analyzes technical indicators
  - Checks open positions
  - Generates trading signals
  - Detects urgent opportunities

#### Trade Interval (Default: 60 seconds)
- **Purpose**: Minimum cooldown between trade executions
- **Frequency**: Enforced gap between trades
- **What happens**:
  - Prevents overtrading
  - Enforces risk management
  - Can be bypassed for urgent trades

#### Urgent Bypass
When `enable_urgent_bypass: true`, the AI can bypass the trade cooldown for time-sensitive opportunities:
- **Strong breakouts** requiring immediate entry
- **Critical support/resistance tests**
- **Extreme volatility events**
- **Rapid trend reversals**

**Example Timeline:**
```
0:00 - AI analyzes market → No signal
0:05 - AI analyzes market → No signal
0:10 - AI analyzes market → BUY signal (confidence 0.85) → Trade executed
0:15 - AI analyzes market → SELL signal (confidence 0.90) → Blocked (cooldown)
0:20 - AI analyzes market → SELL signal (confidence 0.95, URGENT) → Trade executed (bypass)
0:25 - AI analyzes market → Position management
...
1:10 - AI analyzes market → BUY signal → Trade executed (cooldown expired)
```

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

### Single Trade Mode (Default)

Execute one trade and exit:

```bash
python main.py
```

**Use case**: Testing, manual control, scheduled tasks

### Continuous Trading Mode

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

**Use case**: Automated 24/7 trading

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

