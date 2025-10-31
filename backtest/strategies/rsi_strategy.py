# backtest/strategies/rsi_strategy.py
import pandas as pd
import numpy as np
import pandas_ta as ta


def rsi_strategy(symbol, rsi_period=14, oversold=30, overbought=70, exit_level=50):
    """
    RSI-based mean reversion strategy using pandas-ta RSI.
    """
    def strategy(df):
        if len(df) < rsi_period + 1:
            return 'HOLD'

        df = df.copy()
        rsi_series = df.ta.rsi(close='close', length=rsi_period)
        if rsi_series is None or len(rsi_series) == 0:
            return 'HOLD'

        current_rsi = rsi_series.iloc[-1]
        if np.isnan(current_rsi):
            return 'HOLD'

        # Entry logic
        if current_rsi <= oversold:
            return 'BUY'
        elif current_rsi >= overbought:
            return 'SELL'
        # Exit logic - neutral RSI region
        elif (current_rsi >= exit_level and current_rsi <= exit_level + 10):
            return 'HOLD'

        return 'HOLD'

    return strategy