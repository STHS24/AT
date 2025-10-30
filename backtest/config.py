# backtest/config.py
from dataclasses import dataclass

@dataclass
class BacktestConfig:
    symbol: str = "EURUSD"
    days: int = 7
    initial_balance: float = 10_000
    volume: float = 0.1
    sl_pips: float = 0.001
    tp_pips: float = 0.002
    trail_pips: float = 0.001
    pip_value: float = 10.0  # $ per pip for 0.1 lot
    timeframe: int = 1  # MT5.TIMEFRAME_M1