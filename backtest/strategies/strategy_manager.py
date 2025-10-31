# backtest/strategies/strategy_manager.py
"""
Strategy manager to easily switch between different strategies
"""
from .mean_reversion import mean_reversion_strategy
from .trend_following import trend_following_strategy
from .breakout import breakout_strategy
from .rsi_strategy import rsi_strategy

class StrategyManager:
    def __init__(self, strategy_name="trend_following", **strategy_params):
        self.strategy_name = strategy_name
        self.strategy_params = strategy_params
        self.strategy = self._load_strategy()
    
    def _load_strategy(self):
        strategies = {
            "mean_reversion": mean_reversion_strategy,
            "trend_following": trend_following_strategy, 
            "breakout": breakout_strategy,
            "rsi": rsi_strategy,
        }
        
        if self.strategy_name not in strategies:
            raise ValueError(f"Strategy '{self.strategy_name}' not found. Available: {list(strategies.keys())}")
        
        # Always provide symbol as first argument
        params = dict(self.strategy_params)
        symbol = params.pop('symbol', 'EURUSD')
        return strategies[self.strategy_name](symbol, **params)
    
    def get_signal(self, df):
        """Get trading signal for the given dataframe"""
        return self.strategy(df)

# Default strategy (compatible with your existing code)
def trade_decision(symbol, df, strategy_name="trend_following", **params):
    """
    Default trade decision function - maintains compatibility with existing engine
    """
    manager = StrategyManager(strategy_name, **params)
    return manager.get_signal(df)