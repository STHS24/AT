# backtest_mvp/extensions.py
import numpy as np

def apply_slippage_and_commission(engine, price, profit):
    """Apply small random slippage and fixed commission to emulate reality."""
    slip = np.random.uniform(-0.00002, 0.00002)   # ±0.2 pip
    commission = -3                                # per closed trade
    adj_profit = profit + slip * 100000 * engine.config.volume + commission
    return adj_profit

def adaptive_stops(engine, vol_window=20):
    """Dynamically scale SL/TP based on rolling volatility."""
    df = engine.df  # attach dataframe externally before run
    if len(df) < vol_window:
        return
    vol = df['close'].rolling(vol_window).std().iloc[-1]
    base_vol = df['close'].rolling(vol_window * 10).std().mean()
    if np.isnan(base_vol) or base_vol == 0:
        return
    scale = vol / base_vol
    engine.config.sl_pips *= scale
    engine.config.tp_pips *= scale
