# backtest/optimizer.py
import itertools
from .config import BacktestConfig
from .engine import BacktestEngine
import pandas as pd

def grid_search_optimize(df, base_config, param_grid, metric='TotalReturn'):
    """
    Simple grid search for parameter optimization
    Example usage:
        param_grid = {
            'sl_pips': [0.0005, 0.001, 0.002],
            'tp_pips': [0.001, 0.002, 0.003],
            'volume': [0.1, 0.2]
        }
    """
    results = []
    
    # Generate all parameter combinations
    param_names = list(param_grid.keys())
    param_values = list(param_grid.values())
    combinations = list(itertools.product(*param_values))
    
    print(f"Testing {len(combinations)} parameter combinations...")
    
    for i, combo in enumerate(combinations):
        # Create config with current parameters
        current_config = BacktestConfig(
            symbol=base_config.symbol,
            days=base_config.days,
            initial_balance=base_config.initial_balance,
            timeframe=base_config.timeframe
        )
        
        # Set the current parameter combination
        for param_name, param_value in zip(param_names, combo):
            setattr(current_config, param_name, param_value)
        
        # Run backtest
        try:
            engine = BacktestEngine(current_config)
            _, total_return, trades = engine.run(df.copy())
            
            # Calculate additional metrics
            closed_trades = [t for t in trades if t.get('profit') is not None]
            win_rate = len([t for t in closed_trades if t['profit'] > 0]) / max(len(closed_trades), 1) * 100
            profit_factor = abs(sum(t['profit'] for t in closed_trades if t['profit'] > 0)) / \
                           abs(sum(t['profit'] for t in closed_trades if t['profit'] < 0)) if any(t['profit'] < 0 for t in closed_trades) else float('inf')
            
            result = {
                'combination': i,
                'total_return': total_return,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'total_trades': len(closed_trades),
                **dict(zip(param_names, combo))
            }
            results.append(result)
            
            print(f"Combo {i+1}/{len(combinations)}: Return={total_return:+.2f}% | WinRate={win_rate:.1f}%")
            
        except Exception as e:
            print(f"❌ Combo {i+1} failed: {e}")
            continue
    
    return pd.DataFrame(results)

def find_best_parameters(results_df, metric='total_return', min_trades=10):
    """Filter and rank results to find optimal parameters"""
    # Filter out results with too few trades
    filtered = results_df[results_df['total_trades'] >= min_trades]
    
    if filtered.empty:
        print("⚠️ No results with sufficient trades")
        return results_df.nlargest(5, metric)
    
    # Rank by selected metric
    best = filtered.nlargest(10, metric)
    
    print(f"\n🏆 TOP 5 PARAMETER COMBINATIONS (by {metric}):")
    print("="*60)
    for i, (_, row) in enumerate(best.head().iterrows(), 1):
        params = {k: v for k, v in row.items() if k not in ['combination', 'total_return', 'win_rate', 'profit_factor', 'total_trades']}
        print(f"{i}. Return: {row['total_return']:+.2f}% | WinRate: {row['win_rate']:.1f}% | Trades: {row['total_trades']}")
        print(f"   Params: {params}")
        print()
    
    return best