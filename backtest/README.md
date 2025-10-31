# 🧠 Backtesting Framework

A modular backtesting system for forex trading strategies with realistic market simulation and advanced analytics.

---

## 📁 Project Structure

### **📂 backtest/** — Core Backtesting Engine
The main backtesting framework that handles trade execution, position management, and real-time simulation.

#### **Key Components**
- **engine.py** — Core backtesting engine with trailing stops, SL/TP management  
- **config.py** — Configuration dataclass for backtest parameters  
- **run.py** — Main entry point for running backtests  
- **utils.py** — Data fetching and visualization utilities  
- **backtest.py** — Main backtest orchestrator with Backtrader integration
- **backtrader_engine.py** — Backtrader adapter for advanced backtesting capabilities
- **backtest_runner.py** — Data fetching and backtest execution coordinator

#### **Backtrader Integration**
- **backtrader_engine.py** — Adapter bridging StrategyManager with Backtrader framework
  - `StrategyAdapter` — Wraps StrategyManager signals as Backtrader strategy
  - `BTConfig` — Backtrader-specific configuration (commission, slippage, stake sizing)
  - `FixedStakeSizer` — Consistent position sizing across trades
  - `run_backtrader_with_df()` — Main entry point for Backtrader backtests

#### **Features**
- **Dual Engine Support** — Choose between native engine or Backtrader framework
- Real-time trade simulation with MetaTrader 5 integration  
- Trailing stop loss and take profit management  
- Position tracking and equity curve calculation  
- Trade reversal logic and signal processing  
- Comprehensive trade logging and CSV export  
- Advanced analytics (Sharpe ratio, drawdown, trade analysis)

---

### **📂 backtest_mvp/** — Analytics & Extensions Module
Advanced analytics, risk management extensions, and walk-forward testing capabilities.

#### **Key Components**
- **extensions.py** — Realistic market simulation enhancements  
  - `apply_slippage_and_commission()` — Adds trading costs and random slippage  
  - `adaptive_stops()` — Dynamic SL/TP scaling based on market volatility  
- **analytics.py** — Performance metrics and risk analysis  
  - `performance_metrics()` — Sharpe ratio, Sortino ratio, max drawdown  
  - `trade_summary()` — Win rate, expectancy, risk-reward analysis  
- **walkforward.py** — Robustness testing  
  - `walk_forward()` — Sequential testing for strategy stability  
  - Returns stability metrics and consistency analysis  

---

### **📂 strategies/** — Trading Strategy Module
Strategy implementations and signal generation.

#### **Key Components**
- **strategy_manager.py** — Unified strategy interface and signal generation
  - Supports multiple strategy types (trend_following, rsi, etc.)
  - Configurable parameters per strategy
  - Consistent signal interface across engines

---

## ⚡ Quick Start

### **Option 1: Native Engine**
```python
from backtest import BacktestConfig, run_backtest

# Configure backtest
config = BacktestConfig(
    symbol="EURUSD",
    days=7,
    sl_pips=0.001,
    tp_pips=0.002
)

# Run backtest
run_backtest(config)