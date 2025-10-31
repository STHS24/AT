# backtest/strategies/trend_following.py
import pandas as pd
import numpy as np
import pandas_ta as ta


def trend_following_strategy(symbol, lookback_fast=8, lookback_slow=21, trend_threshold=0.3):
    """
    Simplified trend following strategy using pandas-ta EMAs.
    """
    def strategy(df):
        if len(df) < lookback_slow:
            return 'HOLD'

        df = df.copy()
        ema_fast = df.ta.ema(close='close', length=lookback_fast)
        ema_slow = df.ta.ema(close='close', length=lookback_slow)
        if ema_fast is None or ema_slow is None:
            return 'HOLD'

        current_fast = ema_fast.iloc[-1]
        current_slow = ema_slow.iloc[-1]
        prev_fast = ema_fast.iloc[-2]
        prev_slow = ema_slow.iloc[-2]

        if np.isnan(current_fast) or np.isnan(current_slow) or np.isnan(prev_fast) or np.isnan(prev_slow):
            return 'HOLD'

        # Cross-over detection
        if current_fast > current_slow and prev_fast <= prev_slow:
            return 'BUY'
        elif current_fast < current_slow and prev_fast >= prev_slow:
            return 'SELL'

        return 'HOLD'

    return strategy