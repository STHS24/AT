import pandas as pd
import numpy as np
import pandas_ta as ta


def mean_reversion_strategy(symbol, lookback_period=20, entry_zscore=2.0, exit_zscore=0.5):
    """
    Mean reversion using Bollinger Bands from pandas-ta.
    Entry on touch/penetration of entry bands; HOLD within exit bands.
    """
    def strategy(df):
        if len(df) < lookback_period:
            return 'HOLD'

        df = df.copy()
        # Entry bands
        bb_entry = df.ta.bbands(close='close', length=lookback_period, std=entry_zscore)
        if bb_entry is None or bb_entry.isna().iloc[-1].any():
            return 'HOLD'
        upper_entry = bb_entry.iloc[-1][bb_entry.columns[2]]  # BBU
        lower_entry = bb_entry.iloc[-1][bb_entry.columns[0]]  # BBL

        # Exit bands (narrower)
        bb_exit = df.ta.bbands(close='close', length=lookback_period, std=exit_zscore)
        if bb_exit is None or bb_exit.isna().iloc[-1].any():
            return 'HOLD'
        upper_exit = bb_exit.iloc[-1][bb_exit.columns[2]]
        lower_exit = bb_exit.iloc[-1][bb_exit.columns[0]]

        current_close = df['close'].iloc[-1]

        # Entry logic
        if current_close >= upper_entry:
            return 'SELL'
        elif current_close <= lower_entry:
            return 'BUY'
        # Exit logic (inside tighter exit bands)
        elif (current_close <= upper_exit and current_close >= lower_exit):
            return 'HOLD'

        return 'HOLD'

    return strategy