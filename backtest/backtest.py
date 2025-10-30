# backtest.py
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from strategy import trade_decision
import os

# === CONFIG (mirrors live bot) ===
SL_PIPS = 0.001       # 10 pips
TP_PIPS = 0.002       # 20 pips
TRAIL_PIPS = 0.001    # Same as SL for trailing
VOLUME = 0.1
PIP_VALUE = 10        # $10 per pip for 0.1 lot
# =====================================

def run_backtest(symbol="EURUSD", days=30, initial_balance=10000):
    print(f"Backtesting {symbol} over last {days} days with SL/TP + TRAILING STOP...")

    # Initialize MT5
    if not mt5.initialize():
        print("MT5 init failed")
        return
    if not mt5.symbol_select(symbol, True):
        print(f"Symbol {symbol} not available")
        mt5.shutdown()
        return

    # Fetch data
    from_ts = int((pd.Timestamp.now() - pd.Timedelta(days=days)).timestamp())
    to_ts = int(datetime.now().timestamp())
    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, from_ts, to_ts)
    mt5.shutdown()

    if rates is None or len(rates) < 100:
        print("Not enough data")
        return

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')

    # Trading state
    balance = initial_balance
    position = None
    entry_price = sl = tp = 0
    trailing_active = False  # Becomes True after first trail
    equity = []
    trades = []

    print(f"Starting backtest with ${balance:,.2f}...")

    for i in range(20, len(df)):
        window = df.iloc[i-20:i]
        window_mt5 = window.to_records(index=False)
        mt5.copy_rates_from_pos = lambda *_, **__: window_mt5

        signal = trade_decision(symbol)
        price = df.iloc[i]['close']
        high = df.iloc[i]['high']
        low = df.iloc[i]['low']

        # === TRAILING STOP LOGIC (NEW) ===
        if position == 'BUY' and position:
            # Update SL if price moves up
            new_sl = high - TRAIL_PIPS
            if new_sl > sl:  # Only move SL up
                sl = new_sl
                trailing_active = True
                print(f"Trailing SL ↑ to {sl:.5f}")

        elif position == 'SELL' and position:
            # Update SL if price moves down
            new_sl = low + TRAIL_PIPS
            if new_sl < sl:  # Only move SL down
                sl = new_sl
                trailing_active = True
                print(f"Trailing SL ↓ to {sl:.5f}")
        # ===================================

        # === CLOSE ON SL/TP HIT (UPDATED TO USE TRAILING SL) ===
        if position:
            if position == 'BUY':
                if low <= sl:
                    profit = (sl - entry_price) * 100000 * VOLUME
                    balance += profit
                    reason = 'TRAIL_SL' if trailing_active else 'SL'
                    trades.append({'type': reason, 'price': sl, 'profit': profit})
                    print(f"{reason} hit @ {sl:.5f} → Profit: {profit:+.2f}")
                    position = None
                    trailing_active = False
                elif high >= tp:
                    profit = (tp - entry_price) * 100000 * VOLUME
                    balance += profit
                    trades.append({'type': 'TP', 'price': tp, 'profit': profit})
                    print(f"TP hit @ {tp:.5f} → Profit: {profit:+.2f}")
                    position = None
                    trailing_active = False

            elif position == 'SELL':
                if high >= sl:
                    profit = (entry_price - sl) * 100000 * VOLUME
                    balance += profit
                    reason = 'TRAIL_SL' if trailing_active else 'SL'
                    trades.append({'type': reason, 'price': sl, 'profit': profit})
                    print(f"{reason} hit @ {sl:.5f} → Profit: {profit:+.2f}")
                    position = None
                    trailing_active = False
                elif low <= tp:
                    profit = (entry_price - tp) * 100000 * VOLUME
                    balance += profit
                    trades.append({'type': 'TP', 'price': tp, 'profit': profit})
                    print(f"TP hit @ {tp:.5f} → Profit: {profit:+.2f}")
                    position = None
                    trailing_active = False
        # =======================================================

        # === REVERSE ON SIGNAL ===
        if position and (
            (position == 'BUY' and signal == 'SELL') or
            (position == 'SELL' and signal == 'BUY')
        ):
            close_price = price
            profit = (close_price - entry_price) * (1 if position == 'BUY' else -1) * 100000 * VOLUME
            balance += profit
            trades.append({'type': 'REVERSE', 'price': close_price, 'profit': profit})
            print(f"Reversed @ {close_price:.5f} → Profit: {profit:+.2f}")
            position = None
            trailing_active = False

        # === OPEN NEW POSITION ===
        if not position and signal in ['BUY', 'SELL']:
            position = signal
            entry_price = price
            sl = price - SL_PIPS if signal == 'BUY' else price + SL_PIPS
            tp = price + TP_PIPS if signal == 'BUY' else price - TP_PIPS
            trailing_active = False  # Reset on new entry
            trades.append({'type': 'OPEN', 'side': signal, 'price': entry_price, 'sl': sl, 'tp': tp})

        equity.append(balance)

    # === FINAL STATS ===
    df['equity'] = equity + [equity[-1]] * (len(df) - len(equity))
    total_return = (balance - initial_balance) / initial_balance * 100
    closed_trades = [t for t in trades if t['type'] in ['SL', 'TRAIL_SL', 'TP', 'REVERSE']]
    winning_trades = [t for t in closed_trades if t.get('profit', 0) > 0]
    win_rate = len(winning_trades) / max(len(closed_trades), 1) * 100

    print(f"\n{'='*60}")
    print(f"BACKTEST COMPLETE WITH TRAILING STOP")
    print(f"   Final Balance: ${balance:,.2f}")
    print(f"   Total Return:  {total_return:+.2f}%")
    print(f"   Win Rate:      {win_rate:.1f}%")
    print(f"   Total Trades:  {len(closed_trades)}")
    print(f"   Trailing Used: {any(t['type']=='TRAIL_SL' for t in trades)}")
    print(f"{'='*60}")

    # === PLOT ===
    plt.figure(figsize=(14, 7))
    plt.plot(df['time'], df['equity'], label='Equity Curve (with Trailing)', color='green', linewidth=2)
    plt.title(f"Backtest: {symbol} | {total_return:+.2f}% | SL={SL_PIPS} TP={TP_PIPS} Trail={TRAIL_PIPS}")
    plt.xlabel("Time")
    plt.ylabel("Balance ($)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()

    os.makedirs("backtests", exist_ok=True)
    plt.savefig(f"backtests/{symbol}_trailing_backtest.png", dpi=150)
    plt.show()

    # === SAVE TRADE LOG ===
    pd.DataFrame(trades).to_csv(f"backtests/{symbol}_trades_trailing.csv", index=False)
    print(f"Trade log saved to backtests/{symbol}_trades_trailing.csv")

if __name__ == "__main__":
    run_backtest(symbol="EURUSD", days=7)