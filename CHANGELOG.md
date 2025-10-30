# TraderBot Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- AI/ML integration for predictive trading
- Backtesting framework
- Multi-symbol trading support
- Telegram/Slack notifications

---

## [0.7.0] - 2025-10-30

### Added - Real-Time Dashboard Integration

**WebSocket Server Module (`websocket_server.py`)**
- Real-time WebSocket server on `ws://localhost:5000`
- Broadcasts bot status to connected dashboard clients
- Handles dashboard commands (pause/resume/stop)
- Manages multiple client connections
- Tracks recent actions and logs for dashboard display
- Trading pause/resume control via dashboard

**Avalonia Desktop Dashboard (`TraderDashboard/`)**
- Professional cross-platform desktop application (.NET 8, C#)
- Real-time monitoring of bot status, balance, equity, profit
- Live equity curve chart with automatic updates
- Open positions table with symbol, side, and P/L
- Activity log with timestamps and color-coded messages
- Control buttons: Start, Pause, Stop, Theme Toggle
- Auto-reconnect on connection loss (every 5 seconds)
- Dark/Light theme support

**Main Bot Enhancements**
- Async/await support for WebSocket server integration
- `get_current_status()` function for status reporting
- Dashboard logging throughout trading operations
- Real-time broadcasts after each trading iteration
- Pause/resume functionality controlled by dashboard
- WebSocket server starts automatically with bot

**Documentation**
- `USAGE.md` - Comprehensive usage guide for bot and dashboard
- `DASHBOARD_INTEGRATION.md` - Technical integration details
- `TraderDashboard/README.md` - Dashboard user guide
- `TraderDashboard/QUICKSTART.md` - Quick start guide

### Changed
- `main.py` - Converted to async with `run_continuous_trading_async()`
- `main.py` - Added dashboard logging to all trading functions
- `main.py` - Integrated WebSocket broadcasts
- `.gitignore` - Added .NET build artifacts exclusion

### Technical Details
- **Total Tests**: 86 passing, 17 skipped
- **New Module**: `websocket_server.py` (170 lines)
- **Dashboard**: Complete Avalonia application (1000+ lines)
- **WebSocket Protocol**: JSON-based bidirectional communication
- **Update Frequency**: Every 60 seconds (configurable)

---

## [0.6.0] - 2025-10-29

### Added - Logging & Analytics

**Enhanced Trade Logger (`trade_logger.py`)**
- Multi-format logging: text file, CSV, and SQLite database
- Comprehensive trade data: 20+ fields per trade
- Trade lifecycle tracking: open and close events
- Automatic risk/reward ratio calculation
- Database indexes for fast querying

**Performance Analytics (`analytics.py`)**
- Comprehensive performance reports with statistics
- Basic statistics: total trades, win rate, profit factor
- Strategy performance comparison
- Time-based analysis: daily and hourly breakdown
- Risk metrics: max drawdown, Sharpe ratio
- Best/worst trades tracking
- Report export to JSON format

**Database Storage**
- SQLite database: `logs/trades.db`
- Structured schema with 21 fields
- Trade status updates (OPEN → CLOSED)
- Query optimization with indexes

**CSV Export**
- Automatic export to `logs/trades.csv`
- Excel-compatible format
- Real-time updates

### Changed
- `main.py` - Integrated TradeLogger and PerformanceAnalytics
- `execute_trade()` - Logs trade opening with full details
- `close_position()` - Logs trade closure with P/L, commission, swap
- Shutdown handler - Generates performance report on exit

### Technical Details
- **Total Tests**: 86 passing (12 new for logging/analytics)
- **New Modules**: `trade_logger.py` (300 lines), `analytics.py` (300 lines)
- **New Test File**: `tests/test_logging_analytics.py` (349 lines)

---

## [0.5.0] - 2025-10-29

### Added - Risk Management

**Risk Management Module (`risk_manager.py`)**
- Dynamic lot sizing based on account balance and risk percentage
- Automatic SL/TP calculation: ATR, fixed pips, or percentage methods
- ATR calculation with caching for performance
- Daily loss/profit limits with auto-disable
- Persistent P/L tracking in `logs/daily_pnl.json`
- Trade validation: lot size, daily limits, symbol constraints

**Configuration**
- New `risk_management` section with 26 parameters
- Risk percentages, lot size limits, SL/TP methods
- ATR configuration, daily limits

### Changed
- `main.py` - Integrated RiskManager into trading functions
- `trading_iteration()` - Check daily limits before trading
- `execute_trade()` - Calculate dynamic lot sizes and SL/TP
- `close_position()` - Update daily P/L after closing positions

### Technical Details
- **Total Tests**: 74 passing (22 new for risk management)
- **New Module**: `risk_manager.py` (400 lines)
- **New Test File**: `tests/test_risk_management.py` (500 lines)

---

## [0.4.0] - 2025-10-29

### Added - Multiple Trading Strategies

**Strategy System**
- Base strategy class for all strategies
- Strategy Manager with 4 combination methods
- Strategy weights for prioritization
- Enable/disable individual strategies

**New Strategies**
- Moving Average (MA) Strategy
- RSI Strategy
- MACD Strategy

**Configuration**
- New `strategy_config` section
- Per-strategy parameters

### Changed
- `strategy.py` - Refactored into class-based structure
- `main.py` - Integrated StrategyManager

### Technical Details
- **Total Tests**: 52 passing (40 new)
- **New Modules**: 6 strategy files in `strategies/`

---

## [0.3.0] - 2025-10-28

### Added - Continuous Trading Loop

**Continuous Trading**
- Automated trading at configurable intervals
- Position tracking to avoid duplicates
- Max concurrent trades limit
- Graceful shutdown (CTRL+C)

**Position Management**
- `get_open_positions()` - Retrieve open positions
- `has_open_position()` - Check position exists
- `can_open_new_trade()` - Verify max trades limit
- `close_position()` - Close positions on signal change

### Changed
- `main.py` - Added continuous trading loop

### Technical Details
- **Total Tests**: 12 passing (15 new, some skipped)
- **New Test File**: `tests/test_milestone2.py` (300 lines)

---

## [0.2.0] - 2025-10-27

### Added - Core Bot Foundation

**Core Trading Bot**
- MT5 connection and account info retrieval
- Trade execution: BUY/SELL orders
- Automatic SL/TP calculation
- Trade logging to `logs/trades.log`
- FOK order filling mode

**Strategy System**
- Simple price momentum strategy
- Signal generation: BUY, SELL, or NONE

**Configuration**
- `config/settings.json` for all parameters

### Technical Details
- **Main Module**: `main.py` (200 lines)
- **Strategy Module**: `strategy.py` (50 lines)

---

## [0.1.0] - 2025-10-26

### Initial Setup

- Project structure created
- Repository initialized
- Basic documentation
- Requirements file

---

**For detailed integration history and milestone summaries, see [INTEGRATION_HISTORY.md](INTEGRATION_HISTORY.md)**

