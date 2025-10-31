# backtest/analytics.py
import numpy as np
import pandas as pd

def performance_metrics(equity):
    """Compute key risk-adjusted metrics from equity curve."""
    returns = pd.Series(np.diff(equity) / equity[:-1])
    ann_factor = np.sqrt(252 * 24 * 60)  # assuming 1-min bars ≈ 252d * 24h * 60m
    sharpe = ann_factor * returns.mean() / (returns.std() + 1e-9)
    downside = returns[returns < 0].std()
    sortino = ann_factor * returns.mean() / (downside + 1e-9)
    max_dd = (equity / np.maximum.accumulate(equity) - 1).min()
    return {
        "Sharpe": round(sharpe, 3),
        "Sortino": round(sortino, 3),
        "MaxDrawdown": round(max_dd * 100, 2),
        "TotalReturn": round((equity[-1] / equity[0] - 1) * 100, 2),
    }

def trade_summary(trades):
    """Aggregate win rate, expectancy, risk:reward."""
    df = pd.DataFrame([t for t in trades if 'profit' in t])
    if df.empty:
        return {}
    win_rate = (df.profit > 0).mean() * 100
    avg_win = df.loc[df.profit > 0, 'profit'].mean()
    avg_loss = abs(df.loc[df.profit < 0, 'profit'].mean())
    expectancy = df.profit.mean()
    rr = avg_win / avg_loss if avg_loss else np.nan
    return {
        "WinRate": round(win_rate, 2),
        "Expectancy": round(expectancy, 2),
        "RiskReward": round(rr, 2),
    }
