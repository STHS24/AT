# backtest/utils.py
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import os

def fetch_data(symbol: str, days: int, timeframe: int = 1):
    if not mt5.initialize():
        raise RuntimeError("MT5 init failed")
    if not mt5.symbol_select(symbol, True):
        mt5.shutdown()
        raise ValueError(f"Symbol {symbol} not available")

    from_ts = int((pd.Timestamp.now() - pd.Timedelta(days=days)).timestamp())
    to_ts = int(datetime.now().timestamp())
    rates = mt5.copy_rates_range(symbol, timeframe, from_ts, to_ts)
    mt5.shutdown()

    if rates is None or len(rates) < 100:
        raise ValueError("Not enough data")

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def save_plot(df, symbol, total_return, config, filename):
    import matplotlib.pyplot as plt
    plt.figure(figsize=(14, 7))
    plt.plot(df['time'], df['equity'], label='Equity Curve (Trailing)', color='green', linewidth=2)
    plt.title(f"Backtest: {symbol} | {total_return:+.2f}% | SL={config.sl_pips} TP={config.tp_pips} Trail={config.trail_pips}")
    plt.xlabel("Time")
    plt.ylabel("Balance ($)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    os.makedirs("backtests", exist_ok=True)
    path = f"backtests/{filename}.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"Chart saved: {path}")