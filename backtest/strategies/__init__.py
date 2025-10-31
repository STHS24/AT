# backtest/strategies/__init__.py
from .mean_reversion import mean_reversion_strategy
from .trend_following import trend_following_strategy
from .breakout import breakout_strategy
from .strategy_manager import trade_decision
__all__ = [
    "mean_reversion_strategy",
    "trend_following_strategy", 
    "breakout_strategy",
    "trade_decision",
]