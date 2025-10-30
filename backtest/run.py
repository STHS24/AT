# backtest/run.py
from .config import BacktestConfig
from .engine import BacktestEngine
from .utils import fetch_data, save_plot
import pandas as pd

def run_backtest(config: BacktestConfig = None):
    config = config or BacktestConfig()
    df = fetch_data(config.symbol, config.days)
    engine = BacktestEngine(config)
    df, total_return, trades = engine.run(df)

    # Save results
    save_plot(df, config.symbol, total_return, config, f"{config.symbol}_modular")
    pd.DataFrame(trades).to_csv(f"backtests/{config.symbol}_trades_modular.csv", index=False)
    print(f"Trade log: backtests/{config.symbol}_trades_modular.csv")

if __name__ == "__main__":
    run_backtest()