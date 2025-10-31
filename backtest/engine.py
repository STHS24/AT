# backtest/engine.py
import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from .config import BacktestConfig
from .strategies import trade_decision
from backtest.backtest_mvp.extensions import apply_slippage_and_commission, adaptive_stops
from backtest.backtest_mvp.analytics import performance_metrics, trade_summary
from backtest.backtest_mvp.multi_timeframe import multi_timeframe_confirmation

class BacktestEngine:
    """
    Enhanced backtesting engine with:
      • Trailing stop + SL/TP
      • Slippage + commission realism
      • Volatility-adaptive stops
      • Multi-timeframe signal confirmation
      • Sharpe, Sortino, MaxDrawdown metrics
    """

    def __init__(self, config: BacktestConfig):
        self.config = config
        self.balance = config.initial_balance
        self.position = None
        self.entry_price = self.sl = self.tp = 0
        self.trailing_active = False
        self.equity = []
        self.trades = []
        self.df = None  # stored reference for adaptive volatility

    # === INTERNAL HELPERS ===
    def _update_trailing(self, high: float, low: float):
        """Move SL in the direction of profit."""
        if not self.position:
            return
        trail = self.config.trail_pips
        if self.position == 'BUY':
            new_sl = high - trail
            if new_sl > self.sl:
                self.sl = new_sl
                self.trailing_active = True
                print(f"Trailing SL ↑ to {self.sl:.5f}")
        elif self.position == 'SELL':
            new_sl = low + trail
            if new_sl < self.sl:
                self.sl = new_sl
                self.trailing_active = True
                print(f"Trailing SL ↓ to {self.sl:.5f}")

    def _check_exit(self, high: float, low: float, close: float):
        """Evaluate SL/TP exit conditions and actually close positions."""
        if not self.position:
            return

        pip_val = self.config.pip_value * self.config.volume * 100000
        profit = 0

        if self.position == 'BUY':
            if low <= self.sl:
                profit = (self.sl - self.entry_price) * pip_val
                profit = apply_slippage_and_commission(self, self.sl, profit)
                reason = 'TRAIL_SL' if self.trailing_active else 'SL'
                self._close_position(reason, self.sl, profit)
            elif high >= self.tp:
                profit = (self.tp - self.entry_price) * pip_val
                profit = apply_slippage_and_commission(self, self.tp, profit)
                self._close_position('TP', self.tp, profit)

        elif self.position == 'SELL':
            if high >= self.sl:
                profit = (self.entry_price - self.sl) * pip_val
                profit = apply_slippage_and_commission(self, self.sl, profit)
                reason = 'TRAIL_SL' if self.trailing_active else 'SL'
                self._close_position(reason, self.sl, profit)
            elif low <= self.tp:
                profit = (self.entry_price - self.tp) * pip_val
                profit = apply_slippage_and_commission(self, self.tp, profit)
                self._close_position('TP', self.tp, profit)

    def _close_position(self, reason: str, price: float, profit: float):
        """Close trade and log result."""
        self.balance += profit
        self.trades.append({'type': reason, 'price': price, 'profit': profit})
        print(f"{reason} hit @ {price:.5f} → Profit: {profit:+.2f}")
        self.position = None
        self.trailing_active = False

    # === MAIN RUN ===
    def run(self, df: pd.DataFrame):
        self.df = df  # store for volatility scaling
        print(f"Running enhanced backtest with MTF confirmation on {len(df)} bars...")

        for i in range(20, len(df)):
            window = df.iloc[i-20:i].to_records(index=False)
            mt5.copy_rates_from_pos = lambda *_, **__: window

            # Use multi-timeframe confirmed signal instead of raw signal
            signal = signal = trade_decision(
                self.config.symbol, 
                window,
                strategy_name="trend_following"
            )

            # Adaptive SL/TP
            adaptive_stops(self)

            # Check current position
            self._update_trailing(high, low)
            self._check_exit(high, low, close)

            # Reverse on opposite confirmed signal
            if self.position and (
                (self.position == 'BUY' and signal == 'SELL') or
                (self.position == 'SELL' and signal == 'BUY')
            ):
                pip_val = self.config.pip_value * self.config.volume * 100000
                profit = (close - self.entry_price) * (1 if self.position == 'BUY' else -1) * pip_val
                profit = apply_slippage_and_commission(self, close, profit)
                self._close_position('REVERSE', close, profit)

            # Open new position on confirmed signal
            if not self.position and signal in ['BUY', 'SELL']:
                self.position = signal
                self.entry_price = close
                self.sl = close - self.config.sl_pips if signal == 'BUY' else close + self.config.sl_pips
                self.tp = close + self.config.tp_pips if signal == 'BUY' else close - self.config.tp_pips
                self.trailing_active = False
                self.trades.append({
                    'type': 'OPEN', 
                    'side': signal, 
                    'price': close, 
                    'sl': self.sl, 
                    'tp': self.tp
                })

            self.equity.append(self.balance)

        return self._finalize(df)

    # === FINALIZATION ===
    def _finalize(self, df: pd.DataFrame):
        """Wrap-up analytics and performance summary."""
        df['equity'] = self.equity + [self.equity[-1]] * (len(df) - len(self.equity))
        total_return = (self.balance - self.config.initial_balance) / self.config.initial_balance * 100
        closed = [t for t in self.trades if t['type'] in ['SL', 'TRAIL_SL', 'TP', 'REVERSE']]
        win_rate = len([t for t in closed if t.get('profit', 0) > 0]) / max(len(closed), 1) * 100

        # Extended metrics
        perf = performance_metrics(df['equity'].values)
        summary = trade_summary(self.trades)

        # Performance Output
        print("\n" + "🧠💻 " + "="*46)
        print(f"🚀 BACKTEST DONE — {self.config.symbol} WITH MTF CONFIRMATION 📊")
        print("🧩  Setup:", f"{self.config.days}D | SL={self.config.sl_pips} | TP={self.config.tp_pips} | Trail={self.config.trail_pips}")
        print("💵  Start:", f"${self.config.initial_balance:,.2f}")
        print("📈  End  :", f"${self.balance:,.2f} ({total_return:+.2f}%)")
        print("⚔️   Trades:", f"{len(closed)} | Winrate: {win_rate:.1f}% | RR: {summary.get('RiskReward', 0):.2f}")
        print("🪙  Expectancy:", f"{summary.get('Expectancy', 0):+.2f} per trade")
        print("\n📊  ADVANCED VIBES:")
        print(f"  🔹 Sharpe: {perf['Sharpe']:.2f} | Sortino: {perf['Sortino']:.2f}")
        print(f"  🔻 Max Drawdown: {perf['MaxDrawdown']}%")
        print("\n🧾  Verdict:")
        if total_return > 0:
            print("  ✅ Portfolio UP — MTF filtering working! ✨")
        elif total_return > -5:
            print("  ⚖️ Meh performance — consider adjusting MTF parameters 🫡")
        else:
            print("  💀 RIP account — MTF didn't help, back to drawing board 💅")
        print("="*50 + "\n")
        return df, total_return, self.trades