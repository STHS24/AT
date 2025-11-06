# TraderBot Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

---

## [0.9.0] - 2025-11-05

### Milestone 9: Separated Analysis & Execution Timing + Urgent Bypass ✅ COMPLETED

This release separates market analysis from trade execution timing, allowing the AI to constantly monitor the market while respecting trade cooldowns. It also adds an urgent bypass mechanism for time-sensitive opportunities.

#### Added

**Separated Timing Architecture (`main.py`, `config/settings.json`)**
- **`analysis_interval_seconds`**: How often AI analyzes the market (default: 5 seconds)
- **`trade_interval_seconds`**: Minimum cooldown between trade executions (default: 60 seconds)
- **Constant Market Monitoring**: AI now analyzes market every 5 seconds instead of every 60 seconds
- **Position Management Always Active**: Position analysis runs every iteration regardless of trade cooldown
- **Independent Intervals**: Analysis and execution are now completely separate

**Urgent Bypass System (`strategies/ai_strategy.py`, `strategies/llm_client.py`)**
- **Urgent Flag**: AI can mark decisions as "urgent" for time-sensitive opportunities
- **Cooldown Bypass**: Urgent trades bypass the trade_interval cooldown
- **`enable_urgent_bypass`**: Configuration to enable/disable urgent bypass (default: true)
- **Urgent Detection**: AI marks opportunities as urgent for:
  - Strong breakouts
  - Critical support/resistance tests
  - Extreme volatility events
  - Time-sensitive market conditions

**Enhanced Rate Limiting (`strategies/llm_client.py`)**
- **Retry-After Header Support**: Respects API's Retry-After header for rate limits
- **Capped Exponential Backoff**: Maximum wait time of 30 seconds
- **Better Error Messages**: Clearer rate limit warnings with wait times

**Last Trade Time Tracking (`main.py`)**
- **Global Trade Cooldown**: Tracks last trade execution time
- **Cooldown Display**: Shows remaining cooldown time in logs
- **Force Execution Parameter**: `trading_iteration()` accepts `force_execution` parameter

#### Changed

**Trading Loop (`main.py`)**
- **Analysis Every 5 Seconds**: AI analyzes market much more frequently
- **Trade Cooldown Enforcement**: Trades only execute after cooldown expires (unless urgent)
- **Urgent Check**: Checks if AI marked last decision as urgent before each iteration
- **Better Logging**: Shows analysis interval vs trade cooldown in startup message

**AI Strategy (`strategies/ai_strategy.py`)**
- **Urgency Tracking**: Stores `last_decision_urgent` flag
- **`is_last_decision_urgent()` Method**: Allows checking if last decision was urgent
- **Urgent Logging**: Logs urgency flag with all decisions
- **Urgent Display**: Shows 🚨 URGENT flag in console output

**LLM Client (`strategies/llm_client.py`)**
- **Urgent Field in Prompt**: System prompt now requests "urgent" field in JSON response
- **Urgent Parsing**: Extracts and validates "urgent" boolean from LLM responses
- **Urgency Guidelines**: Provides clear guidelines for when to mark decisions as urgent

#### Configuration

**New Parameters in `config/settings.json`:**
```json
{
  "analysis_interval_seconds": 5,
  "trade_interval_seconds": 60,
  "enable_urgent_bypass": true
}
```

#### Technical Details

- Analysis runs every 5 seconds (12x per minute)
- Trades execute with 60-second cooldown (unless urgent)
- Position management runs every analysis iteration
- Urgent bypass requires both `enable_urgent_bypass: true` and AI marking decision as urgent
- Rate limiting now respects Retry-After headers
- Last trade time tracked globally to enforce cooldown across all strategies

#### Benefits

1. **Faster Market Response**: AI sees market changes within 5 seconds instead of 60
2. **Better Opportunity Detection**: More frequent analysis catches short-lived opportunities
3. **Risk Management**: Trade cooldown prevents overtrading
4. **Urgent Action**: Can act immediately on critical opportunities
5. **Position Monitoring**: Positions analyzed 12x more frequently
6. **Reduced Slippage**: Faster detection of exit signals

---

## [0.8.0] - 2025-11-05

### Milestone 8: AI Position Management ✅ COMPLETED

This release enhances the AI trading bot with intelligent position management capabilities. The AI now actively manages open positions, deciding when to hold, close, or partially close positions based on market analysis.

#### Added

**AI Position Management (`strategies/ai_strategy.py`)**
- **Position Analysis**: AI analyzes open positions and recommends HOLD, CLOSE, or CLOSE_PARTIAL actions
- **Market Condition Comparison**: Compares current market conditions vs entry conditions
- **Profit Protection**: Evaluates unrealized P/L and position duration for optimal exits
- **Confidence-Based Decisions**: Respects confidence thresholds for closing decisions (default: 70%)
- **Decision Logging**: All position management decisions logged with reasoning

**Partial Position Closing (`main.py`)**
- **Partial Close Support**: Enhanced `close_position()` to support closing a percentage of position
- **Profit Locking**: Lock in partial profits while keeping upside potential
- **Risk Reduction**: Reduce exposure while maintaining market participation
- **AI-Recommended Percentages**: AI suggests optimal percentage to close (e.g., 50%)

**Enhanced LLM Client (`strategies/llm_client.py`)**
- **Position Management API**: New `get_position_management_decision()` method
- **Position-Specific Prompts**: Optimized system prompt for exit decision analysis
- **Response Parsing**: Dedicated parser for position management responses (action, reasoning, confidence, partial_percentage)
- **Robust JSON Extraction**: Handles extra text before/after JSON in LLM responses

**Enhanced Market Analyzer (`strategies/market_analyzer.py`)**
- **Position Context Collection**: New `get_position_analysis_context()` method
- **Position Detail Formatting**: New `_format_position_details()` method
- **Duration Calculation**: Calculates position hold time in minutes and formatted string
- **Pip Calculation**: Calculates current profit/loss in pips
- **SL/TP Distance**: Calculates distance to stop-loss and take-profit levels

**Configuration Options (`config/settings.json`)**
- **`enable_position_management`**: Toggle AI position management (default: true)
- **`min_hold_time_minutes`**: Minimum hold time before AI can close (default: 5 minutes)
- **`position_check_interval`**: How often to analyze positions (default: every iteration)

**Comprehensive Testing (`tests/test_ai_strategy.py`)**
- **5 New Tests**: Position management test suite
  - `test_analyze_position_hold`: Tests HOLD decision
  - `test_analyze_position_close`: Tests CLOSE decision
  - `test_analyze_position_close_partial`: Tests CLOSE_PARTIAL decision
  - `test_analyze_position_low_confidence_filtered`: Tests confidence filtering
  - `test_format_position_details`: Tests position data formatting
- **21 Total Tests**: All tests passing

#### Changed

**Trading Loop (`main.py`)**
- **Position Management First**: Analyzes and manages positions before generating new signals
- **Minimum Hold Time**: Respects minimum hold time to prevent premature exits
- **AI Reasoning in Comments**: Close orders include AI reasoning for audit trail

**Close Position Function (`main.py`)**
- **Volume Parameter**: Added optional `volume` parameter for partial closes
- **Reason Parameter**: Added `reason` parameter for logging close rationale
- **Partial Close Support**: Calculates proportional profit/commission/swap for partial closes
- **Enhanced Logging**: Logs partial vs full closes with reasoning

#### Technical Details

- Position management decisions respect confidence thresholds (default: 0.7)
- Low confidence close decisions automatically filtered to HOLD
- Minimum hold time prevents analysis of newly opened positions
- All position decisions logged to `logs/ai_decisions.jsonl` with type "position_management"
- Partial closes calculate proportional P/L based on volume closed
- AI reasoning included in MT5 order comments for full audit trail

---

## [0.7.0] - 2025-11-05

### Milestone 7: AI-Powered Trading Strategy ✅ COMPLETED

This release transforms the bot from signal-based trading to AI-powered decision making using Large Language Models (LLMs).

#### Added

**AI Strategy System (`strategies/ai_strategy.py`)**
- **LLM Integration**: Uses OpenRouter API with DeepSeek Chat v3.1 model for trading decisions
- **Comprehensive Analysis**: AI analyzes market data, technical indicators, positions, and risk metrics
- **Explainable Decisions**: Every decision includes detailed reasoning and key factors
- **Confidence Filtering**: Only trades when AI confidence exceeds threshold (default: 70%)
- **Decision History**: Logs all AI decisions with reasoning for review and analysis
- **Statistics Tracking**: Monitors AI performance, confidence levels, and API usage

**LLM Client (`strategies/llm_client.py`)**
- **OpenRouter API Integration**: Communicates with OpenRouter API for LLM access
- **Retry Logic**: Exponential backoff retry mechanism for API failures
- **Error Handling**: Robust error handling for timeouts, rate limits, and API errors
- **Response Parsing**: Parses JSON responses with support for markdown code blocks
- **Token Tracking**: Monitors API usage and token consumption
- **Configurable Parameters**: Adjustable model, temperature, timeout, and retry settings

**Market Analyzer (`strategies/market_analyzer.py`)**
- **Multi-Timeframe Analysis**: Collects price data from M1, M5, M15, and H1 timeframes
- **Technical Indicators**: Calculates RSI, MACD, Moving Averages, ATR, Bollinger Bands
- **Price Action Analysis**: Analyzes trends, momentum, and volatility across timeframes
- **Position Tracking**: Includes current positions, P/L, and pip calculations
- **Account Status**: Provides balance, equity, margin, and daily P/L information
- **Risk Context**: Includes risk constraints, limits, and current exposure

**Configuration**
- **AI Strategy Config**: Added AIStrategy configuration to `config/settings.json`
- **API Key Management**: Secure API key configuration
- **Model Selection**: Configurable LLM model (default: deepseek/deepseek-chat-v3.1:free)
- **Confidence Threshold**: Adjustable minimum confidence for trading (default: 0.7)
- **Temperature Control**: LLM creativity parameter (default: 0.7)
- **Enabled by Default**: AI strategy enabled, traditional strategies disabled

**Testing**
- **16 New Tests**: Comprehensive test coverage for AI components
- **LLM Client Tests**: API calls, retry logic, response parsing, error handling
- **Market Analyzer Tests**: Indicator calculations, data collection, context building
- **AI Strategy Tests**: Signal generation, confidence filtering, statistics
- **100% Pass Rate**: All tests passing successfully

**Logging**
- **AI Decision Log**: All AI decisions saved to `logs/ai_decisions.jsonl`
- **Detailed Reasoning**: Each decision includes full reasoning and key factors
- **Confidence Scores**: Tracks confidence levels for all decisions
- **Model Information**: Logs which model made each decision

#### Changed

- **Strategy System**: AI strategy now primary decision maker (traditional strategies available as fallback)
- **Main Configuration**: Updated `config/settings.json` to use AIStrategy by default
- **Strategy Manager**: Enhanced to support AI strategy initialization with risk manager
- **Imports**: Added AIStrategy to main.py imports and strategy package exports

#### Technical Details

**AI Decision Workflow:**
1. **Data Collection**: Market Analyzer gathers comprehensive market context
2. **Prompt Building**: LLM Client formats data into structured prompt
3. **AI Analysis**: LLM analyzes data and provides decision with reasoning
4. **Confidence Check**: Decision filtered based on confidence threshold
5. **Execution**: High-confidence decisions passed to trading system
6. **Logging**: All decisions and reasoning logged for review

**Market Context Provided to AI:**
- Current price (bid/ask/spread)
- Technical indicators (RSI, MACD, MA, ATR, Bollinger Bands)
- Multi-timeframe price action and trends
- Current positions and P/L
- Account balance and equity
- Risk constraints and limits
- Daily P/L status

**AI Response Format:**
```json
{
  "decision": "BUY|SELL|NONE",
  "reasoning": "Detailed explanation of analysis",
  "confidence": 0.0-1.0,
  "key_factors": ["factor1", "factor2", "factor3"]
}
```

#### Benefits

- **Holistic Analysis**: AI considers all factors simultaneously, not just individual indicators
- **Adaptive**: AI can adapt to changing market conditions without manual strategy tuning
- **Explainable**: Every decision includes clear reasoning for transparency
- **Conservative**: Confidence filtering prevents low-quality trades
- **Comprehensive**: Analyzes multiple timeframes and indicators together
- **Risk-Aware**: AI considers current positions, exposure, and risk limits

#### Migration Notes

- **Existing Bots**: Traditional strategies still available, can be re-enabled in config
- **API Key Required**: AIStrategy requires OpenRouter API key in configuration
- **Free Tier**: Using free DeepSeek model, no API costs
- **Backward Compatible**: Can switch back to traditional strategies by updating config

---

## [0.6.0] - 2025-10-29

### Milestone 6: Logging & Analytics ✅ COMPLETED

This release implements enhanced logging and comprehensive performance analytics.

#### Added

**Enhanced Trade Logger (`trade_logger.py`)**
- **Multi-format Logging**: Simultaneous logging to text file, CSV, and SQLite database
- **Comprehensive Trade Data**: 20+ fields including timestamp, symbol, action, prices, P/L, commission, swap, duration, strategy
- **Trade Lifecycle Tracking**: Separate methods for trade open and close events
- **Automatic R/R Calculation**: Calculates risk/reward ratio for each trade
- **Database Indexes**: Fast querying by timestamp, symbol, action, status

**Performance Analytics (`analytics.py`)**
- **Comprehensive Reports**: Generate detailed performance reports with statistics
- **Basic Statistics**: Total trades, win rate, profit factor, average P/L, max profit/loss
- **Strategy Performance**: Compare performance across different strategies
- **Time-Based Analysis**: Daily and hourly performance breakdown
- **Risk Metrics**: Max drawdown, Sharpe ratio, consecutive wins/losses
- **Best/Worst Trades**: Track top 5 best and worst performing trades
- **Report Export**: Save reports to JSON format in `logs/reports/`
- **Console Display**: Formatted summary reports printed to console

**Database Storage**
- **SQLite Database**: Efficient storage in `logs/trades.db`
- **Structured Schema**: 21 fields with proper data types
- **Trade Updates**: Support for updating trades from OPEN to CLOSED status
- **Query Optimization**: Indexes for fast filtering and aggregation

**CSV Export**
- **Automatic Export**: All trades exported to `logs/trades.csv`
- **Excel Compatible**: Easy import into Excel or data analysis tools
- **Real-time Updates**: CSV updated as trades occur

**Testing**
- **12 New Tests**: Comprehensive test coverage for logging and analytics
- **Database Testing**: Tests for schema, inserts, updates, queries
- **Report Testing**: Tests for all report generation features
- **Edge Cases**: Tests for empty database, missing data

#### Changed
- **Updated `main.py`**: Integrated new `TradeLogger` and `PerformanceAnalytics`
- **Enhanced `log_trade()`**: Now logs to multiple formats with strategy name
- **Updated `execute_trade()`**: Logs trade opening with full details
- **Updated `close_position()`**: Logs trade closure with P/L, commission, swap
- **Shutdown Report**: Performance report generated and displayed on bot shutdown

#### Technical Details
- **Total Tests**: 86 passing tests (12 new for logging/analytics)
- **New Modules**: `trade_logger.py` (300 lines), `analytics.py` (300 lines)
- **New Test File**: `tests/test_logging_analytics.py` (349 lines)
- **Database Location**: `logs/trades.db`
- **CSV Location**: `logs/trades.csv`
- **Reports Directory**: `logs/reports/`

---

## [0.5.0] - 2025-10-29

### Milestone 5: Risk Management ✅ COMPLETED

This release implements comprehensive risk management features to protect capital and optimize position sizing.

#### Added

**Risk Management Module (`risk_manager.py`)**
- **Dynamic Lot Sizing**: Automatically calculates optimal position size based on account balance, risk percentage, SL distance, and symbol specifications
- **Automatic SL/TP Calculation**: Three methods available (ATR, fixed pips, percentage)
- **ATR Calculation**: Volatility-based indicator with caching for performance
- **Daily Loss/Profit Limits**: Auto-disable trading when limits reached (default: $500 loss, $1000 profit)
- **P/L Tracking**: Persistent daily tracking in `logs/daily_pnl.json`
- **Trade Validation**: Validates lot size, daily limits, and symbol constraints

**Configuration Enhancements**
- Added `risk_management` section with 26 new parameters
- Risk percentages, lot size limits, SL/TP methods, ATR config, daily limits

**Main Bot Integration**
- Check daily limits before each trading iteration
- Calculate dynamic lot sizes and SL/TP for each trade
- Update daily P/L after closing positions
- Display daily P/L status in each iteration

**Testing**
- Created `tests/test_risk_management.py` with 22 comprehensive tests
- Updated `tests/test_milestone2.py` to properly mock RiskManager
- All 74 tests passing

#### Changed
- `main.py`: Integrated RiskManager into execute_trade(), close_position(), and trading_iteration()
- `config/settings.json`: Expanded from 55 to 81 lines with risk management config

#### Technical Details
- Dynamic lot sizing: `lot_size = risk_amount / (sl_pips × pip_value_per_lot)`
- ATR: `True Range = max(H-L, |H-PrevC|, |L-PrevC|)`, `ATR = avg(TR over N periods)`
- Three SL/TP methods: ATR-based, fixed pips, percentage

#### Live Testing Results
✅ Successfully tested with live MT5 connection:
- Dynamic lot sizing: 1.0 lot for 34 pip SL ✓
- ATR-based SL/TP working ✓
- Daily P/L tracking: $1.90 profit tracked ✓
- Daily limits check working ✓
- Position closed and P/L updated ✓

#### Files
- Modified: `main.py` (+50 lines), `config/settings.json` (+26 lines), `tests/test_milestone2.py`
- Created: `risk_manager.py` (300 lines), `tests/test_risk_management.py` (22 tests), `logs/daily_pnl.json`
- Statistics: 74 passing tests, +350 lines of code

---

## [0.4.0] - 2025-10-29

### Milestone 3 - Multiple Strategies ✅ COMPLETED

#### Added
- **Strategy System Architecture**
  - Created `strategies/` package with modular design
  - Implemented `BaseStrategy` abstract class for all strategies
  - Added `StrategyManager` for combining multiple strategy signals
  - Strategy enable/disable control
  - Weighted voting system for strategy importance

- **New Trading Strategies**
  - `SimpleStrategy`: Refactored momentum-based strategy (original logic)
  - `MAStrategy`: Moving Average Crossover (SMA/EMA support, Golden/Death cross)
  - `RSIStrategy`: Relative Strength Index overbought/oversold detection
  - `MACDStrategy`: MACD crossover strategy with signal line

- **Strategy Manager Features**
  - Four combination methods: `unanimous`, `majority`, `weighted`, `any`
  - Individual strategy enable/disable control
  - Weighted voting system for strategy importance
  - Signal history tracking
  - Real-time signal display for debugging

- **Configuration Enhancements**
  - Added `strategy_config` section in settings.json
  - Per-strategy parameters (timeframe, periods, thresholds)
  - Strategy weights for weighted voting
  - Enable/disable individual strategies
  - Combination method selection

- **Testing**
  - Created `tests/test_strategies_new.py` with 15 comprehensive tests
  - All strategy classes tested (SimpleStrategy, MAStrategy, RSIStrategy, MACDStrategy)
  - StrategyManager combination methods tested (unanimous, majority, weighted, any)
  - Updated Milestone 2 tests to work with new strategy system
  - **Total: 51 passing tests** (up from 38)

#### Changed
- Refactored `main.py` to use `StrategyManager` instead of single `trade_decision()`
- Added `initialize_strategies()` function for strategy setup with config parsing
- Updated trading iteration to use combined signals from multiple strategies
- Expanded `config/settings.json` from 7 to 55 lines with comprehensive strategy configuration
- Modified position management to support pyramiding (multiple positions in same direction)

#### Technical Details
- **Strategy Pattern**: Abstract base class with concrete implementations
- **Signal Combination**: Multiple methods for aggregating strategy signals
- **Timeframe Support**: M1, M5, M15, M30, H1, H4, D1, W1, MN1
- **Technical Indicators**: SMA, EMA, RSI, MACD implemented from scratch using numpy
- **Indicator Calculations**:
  - SMA: Convolution-based moving average
  - EMA: Exponential smoothing with multiplier
  - RSI: Smoothed average gains/losses
  - MACD: EMA differences with signal line

---

### Milestone 2 - Continuous Trading Loop ✅ COMPLETED (2025-10-29)

#### Added
- **Continuous Trading Mode**: Bot can now run indefinitely with configurable intervals
  - Single trade mode (original behavior)
  - Continuous loop mode with scheduler
  - Configurable via `enable_continuous_trading` in settings.json

- **Position Tracking System**:
  - `get_open_positions()`: Retrieve all or filtered open positions
  - `has_open_position()`: Check if position exists for symbol
  - `can_open_new_trade()`: Validate against max concurrent trades limit
  - Prevents duplicate trades on same symbol
  - Enforces max concurrent trades limit

- **Graceful Shutdown Handling**:
  - CTRL+C (SIGINT) signal handler
  - SIGTERM signal handler for service environments
  - Clean MT5 connection closure
  - Iteration count reporting
  - No orphaned processes

- **Enhanced Configuration**:
  - `trade_interval_seconds`: Time between trading checks (default: 300)
  - `max_concurrent_trades`: Maximum open positions (default: 3)
  - `enable_continuous_trading`: Toggle continuous mode (default: false)

- **Refactored Code Structure**:
  - `initialize_mt5()`: Modular MT5 initialization
  - `prepare_symbol()`: Symbol validation and preparation
  - `execute_trade()`: Centralized trade execution
  - `trading_iteration()`: Single iteration logic
  - `run_single_trade()`: Single trade mode
  - `run_continuous_trading()`: Continuous mode with loop

#### Testing
- **Comprehensive Test Suite** (38 passing tests):
  - `tests/__init__.py`: Test package initialization
  - `tests/conftest.py`: Shared fixtures and mocks
  - `tests/test_main.py`: Main bot functionality tests
  - `tests/test_strategy.py`: Strategy tests with future placeholders
  - `tests/test_milestone2.py`: Milestone 2 feature tests (19 tests)
  - `tests/README.md`: Complete testing documentation

- **Test Coverage**:
  - Configuration loading and validation
  - MT5 connection and initialization
  - Symbol preparation
  - Order execution (BUY/SELL)
  - Trade logging
  - Position tracking
  - Max concurrent trades enforcement
  - Graceful shutdown
  - Trading iteration logic

#### Documentation
- **USAGE.md**: Complete usage guide
  - Installation instructions
  - Configuration reference
  - Trading modes explanation
  - Monitoring guidelines
  - Safety features overview
  - Troubleshooting guide
  - Best practices
  - Advanced usage (Windows/Linux services)

- **tests/README.md**: Testing documentation
  - Test structure overview
  - Running tests guide
  - Test categories explanation
  - Fixtures documentation
  - Writing new tests guide

- **CHANGELOG.md**: This file

#### Infrastructure
- **Enhanced .gitignore**:
  - Comprehensive Python patterns
  - Trading bot specific (logs, configs, data)
  - ML/AI model files
  - IDE configurations
  - OS-specific files
  - Security (credentials, keys, secrets)
  - Future-proof structure

### Milestone 1 - Core Bot Foundation ✅ COMPLETED

#### Added
- Split logic into `main.py` and `strategy.py`
- MT5 connection and account info logging
- BUY/SELL trade execution with proper rounding
- Stop-loss and take-profit implementation
- Trade logging to `logs/trades.log`
- FOK order filling mode
- Safe handling for "no signal" scenarios
- Configuration via `config/settings.json`

## Project Statistics

### Code Metrics
- **Main Files**: 2 (main.py, strategy.py)
- **Test Files**: 4 (55 total tests, 38 passing, 17 future placeholders)
- **Configuration Files**: 1 (settings.json)
- **Documentation Files**: 4 (README, USAGE, ROADMAP, CHANGELOG)
- **Lines of Code**: ~600+ (excluding tests)
- **Test Coverage**: Core functionality fully tested

### Features Implemented
- ✅ MT5 Integration
- ✅ Simple Momentum Strategy
- ✅ Trade Execution (BUY/SELL)
- ✅ Trade Logging
- ✅ Configuration Management
- ✅ Continuous Trading Loop
- ✅ Position Tracking
- ✅ Graceful Shutdown
- ✅ Max Concurrent Trades
- ✅ Comprehensive Testing

### Features Planned
- ⏳ Multiple Strategies (MA, RSI, MACD)
- ⏳ Strategy Manager
- ⏳ AI/ML Integration
- ⏳ Risk Management
- ⏳ Advanced Analytics
- ⏳ Web Dashboard
- ⏳ Notifications (Telegram/Slack)
- ⏳ Backtesting Framework

## Migration Guide

### Upgrading from Milestone 1 to Milestone 2

#### Configuration Changes
Add new parameters to `config/settings.json`:
```json
{
  "symbol": "EURUSD",
  "volume": 0.1,
  "deviation": 50,
  "trade_interval_seconds": 300,        // NEW
  "max_concurrent_trades": 3,           // NEW
  "enable_continuous_trading": false    // NEW
}
```

#### Behavior Changes
1. **Default Mode**: Still single trade execution (backward compatible)
2. **New Mode**: Enable `enable_continuous_trading: true` for continuous operation
3. **Position Checking**: Bot now checks for existing positions before trading
4. **Concurrent Limit**: Bot enforces max concurrent trades limit

#### Code Changes
- No breaking changes to existing functionality
- New functions added (backward compatible)
- Signal handler added (transparent to users)

## Known Issues

### Current Limitations
1. **Fixed SL/TP**: Stop-loss and take-profit use fixed pip values
   - Planned: ATR-based dynamic SL/TP (Milestone 5)

2. **Single Symbol**: Bot trades only one symbol at a time
   - Planned: Multi-symbol support (Milestone 7)

3. **Simple Strategy**: Only momentum-based strategy available
   - Planned: Multiple strategies (Milestone 3)

4. **No Risk Management**: Fixed lot size, no dynamic sizing
   - Planned: Dynamic lot sizing (Milestone 5)

5. **Basic Logging**: Simple text file logging
   - Planned: Database storage and analytics (Milestone 6)

### Workarounds
- **Fixed SL/TP**: Adjust values in `execute_trade()` function
- **Single Symbol**: Run multiple bot instances with different configs
- **Simple Strategy**: Modify `strategy.py` for custom logic
- **Fixed Lot Size**: Change `volume` in settings.json
- **Basic Logging**: Parse logs with external tools

## Security Notes

### Sensitive Data
- Never commit `config/settings.json` with real account credentials
- Use `.gitignore` to exclude sensitive files
- Keep API keys and passwords in environment variables

### Safe Practices
- Always test on demo account first
- Start with small lot sizes
- Monitor bot regularly
- Set appropriate max concurrent trades
- Use stop-loss on all trades

## Performance Notes

### Resource Usage
- **CPU**: Minimal (<1% during idle, <5% during execution)
- **Memory**: ~50-100 MB
- **Network**: Minimal (only MT5 API calls)
- **Disk**: Log files grow over time (rotate regularly)

### Optimization Tips
- Increase `trade_interval_seconds` to reduce API calls
- Limit `max_concurrent_trades` to reduce complexity
- Rotate log files weekly/monthly
- Use SSD for faster file I/O

## Contributing

### Development Workflow
1. Create feature branch from `main`
2. Implement feature with tests
3. Run test suite: `pytest tests/ -v`
4. Update documentation
5. Submit pull request

### Testing Requirements
- All new features must have tests
- Maintain >80% code coverage
- All tests must pass before merge
- Follow existing test patterns

## Support

- **GitHub Issues**: https://github.com/STHS24/AT/issues
- **Documentation**: See USAGE.md and ROADMAP.md
- **Tests**: Run `pytest tests/ -v` to verify installation

## License

See LICENSE file for details.

## Acknowledgments

- MetaTrader 5 Python API
- pytest testing framework
- Python community

---

**Note**: This is an active development project. Features and APIs may change between milestones. Always check this changelog before upgrading.

