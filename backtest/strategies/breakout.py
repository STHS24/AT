# backtest/strategies/breakout.py
import pandas as pd
import numpy as np
import pandas_ta as ta


def breakout_strategy(symbol, lookback_period=20, volatility_multiplier=1.5):
    """
    Breakout strategy - enters when price breaks resistance/support levels
    Uses ATR (pandas-ta) for volatility-aware thresholding.
    """
    def strategy(df):
        if len(df) < lookback_period:
            return 'HOLD'

        df = df.copy()
        # Levels based on rolling extremes (previous period)
        df['high_n'] = df['high'].rolling(window=lookback_period).max()
        df['low_n'] = df['low'].rolling(window=lookback_period).min()

        # True ATR for volatility
        atr_series = df.ta.atr(high='high', low='low', close='close', length=lookback_period)
        if atr_series is None or np.isnan(atr_series.iloc[-1]):
            return 'HOLD'

        current_high = df['high'].iloc[-1]
        current_low = df['low'].iloc[-1]
        current_close = df['close'].iloc[-1]
        resistance = df['high_n'].iloc[-2]
        support = df['low_n'].iloc[-2]
        atr = atr_series.iloc[-1]

        breakout_threshold = atr * volatility_multiplier

        # Breakout above resistance
        if current_close > (resistance + breakout_threshold):
            return 'BUY'
        # Breakdown below support
        elif current_close < (support - breakout_threshold):
            return 'SELL'

        return 'HOLD'

    return strategy