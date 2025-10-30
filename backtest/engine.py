# backtest/engine.py
import pandas as pd
import numpy as np
from .config import BacktestConfig
from strategy import trade_decision
import MetaTrader5 as mt5

class BacktestEngine:
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.balance = config.initial_balance
        self.position = None
        self.entry_price = self.sl = self.tp = 0
        self.trailing_active = False
        self.equity = []
        self.trades = []

    def _update_trailing(self, high: float, low: float):
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
        if not self.position:
            return

        vol = self.config.volume
        pip_val = self.config.pip_value * 100000

        if self.position == 'BUY':
            if low <= self.sl:
                profit = (self.sl - self.entry_price) * pip_val * vol
                reason = 'TRAIL_SL' if self.trailing_active else 'SL'
                self._close_position(reason, self.sl, profit)
            elif high >= self.tp:
                profit = (self.tp - self.entry_price) * pip_val * vol
                self._close_position('TP', self.tp, profit)

        elif self.position == 'SELL':
            if high >= self.sl:
                profit = (self.entry_price - self.sl) * pip_val * vol
                reason = 'TRAIL_SL' if self.trailing_active else 'SL'
                self._close_position(reason, self.sl, profit)
            elif low <= self.tp:
                profit = (self.entry_price - self.tp) * pip_val * vol
                self._close_position('TP', self.tp, profit)

    def _close_position(self, reason: str, price: float, profit: float):
        self.balance += profit
        self.trades.append({'type': reason, 'price': price, 'profit': profit})
        print(f"{reason} hit @ {price:.5f} → Profit: {profit:+.2f}")
        self.position = None
        self.trailing_active = False

    def run(self, df: pd.DataFrame):
        print(f"Running backtest on {len(df)} bars...")
        for i in range(20, len(df)):
            window = df.iloc[i-20:i].to_records(index=False)
            mt5.copy_rates_from_pos = lambda *_, **__: window

            signal = trade_decision(self.config.symbol)
            high, low, close = df.iloc[i][['high', 'low', 'close']]

            self._update_trailing(high, low)
            self._check_exit(high, low, close)

            # Reverse
            if self.position and (
                (self.position == 'BUY' and signal == 'SELL') or
                (self.position == 'SELL' and signal == 'BUY')
            ):
                profit = (close - self.entry_price) * (1 if self.position == 'BUY' else -1) * 100000 * self.config.volume
                self._close_position('REVERSE', close, profit)

            # Open
            if not self.position and signal in ['BUY', 'SELL']:
                self.position = signal
                self.entry_price = close
                self.sl = close - self.config.sl_pips if signal == 'BUY' else close + self.config.sl_pips
                self.tp = close + self.config.tp_pips if signal == 'BUY' else close - self.config.tp_pips
                self.trailing_active = False
                self.trades.append({'type': 'OPEN', 'side': signal, 'price': close, 'sl': self.sl, 'tp': self.tp})

            self.equity.append(self.balance)

        return self._finalize(df)

    def _finalize(self, df: pd.DataFrame):
        df['equity'] = self.equity + [self.equity[-1]] * (len(df) - len(self.equity))
        total_return = (self.balance - self.config.initial_balance) / self.config.initial_balance * 100
        closed = [t for t in self.trades if t['type'] in ['SL', 'TRAIL_SL', 'TP', 'REVERSE']]
        win_rate = len([t for t in closed if t.get('profit', 0) > 0]) / max(len(closed), 1) * 100

        print(f"\n{'='*60}")
        print(f"BACKTEST COMPLETE")
        print(f"   Final Balance: ${self.balance:,.2f}")
        print(f"   Return: {total_return:+.2f}% | Win Rate: {win_rate:.1f}%")
        print(f"   Trades: {len(closed)} | Trailing Used: {any(t['type']=='TRAIL_SL' for t in self.trades)}")
        print(f"{'='*60}")

        return df, total_return, self.trades