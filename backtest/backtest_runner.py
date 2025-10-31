# backtest_runner.py
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import os
from multiprocessing import Pool, cpu_count
from functools import partial

# Import strategy manager directly
from backtest.strategies.strategy_manager import StrategyManager

class BacktestRunner:
    def __init__(self, symbol="EURUSD", initial_balance=10000, strategy_name="trend_following", **strategy_params):
        self.symbol = symbol
        self.initial_balance = initial_balance
        self.strategy_name = strategy_name
        self.strategy_params = strategy_params
        
        # Risk management
        self.sl_pips = 0.001
        self.tp_pips = 0.002
        self.trail_pips = 0.001
        self.volume = 0.1
        self.pip_value = 10
        
    def fetch_data(self, days=30):
        """Fetch historical data from MT5"""
        if not mt5.initialize():
            print("MT5 initialization failed")
            return None
            
        if not mt5.symbol_select(self.symbol, True):
            print(f"Symbol {self.symbol} not available")
            mt5.shutdown()
            return None
            
        from_ts = int((pd.Timestamp.now() - pd.Timedelta(days=days)).timestamp())
        to_ts = int(datetime.now().timestamp())
        rates = mt5.copy_rates_range(self.symbol, mt5.TIMEFRAME_M1, from_ts, to_ts)
        mt5.shutdown()
        
        if rates is None or len(rates) < 100:
            print("Not enough data")
            return None
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
    
    def _run_backtest_core(self, df, suppress_output=False):
        """Core backtest logic without result generation (for parallel execution)"""
        # Initialize strategy
        strategy_manager = StrategyManager(
            strategy_name=self.strategy_name,
            **self.strategy_params
        )
        
        # Trading state
        balance = self.initial_balance
        position = None
        entry_price = sl = tp = 0
        trailing_active = False
        equity = []
        trades = []
        
        if not suppress_output:
            print(f"Starting backtest [{self.strategy_name}] with ${balance:,.2f}...")
        
        for i in range(50, len(df)):
            window = df.iloc[i-50:i]
            
            # Get trading signal
            signal = strategy_manager.get_signal(window)
            
            current_data = df.iloc[i]
            price = current_data['close']
            high = current_data['high']
            low = current_data['low']
            
            # Trailing stop logic
            if position == 'BUY':
                new_sl = high - self.trail_pips
                if new_sl > sl:
                    sl = new_sl
                    trailing_active = True
                    if not suppress_output:
                        print(f"[{self.strategy_name}] Trailing SL ↑ to {sl:.5f}")
                    
            elif position == 'SELL':
                new_sl = low + self.trail_pips
                if new_sl < sl:
                    sl = new_sl
                    trailing_active = True
                    if not suppress_output:
                        print(f"[{self.strategy_name}] Trailing SL ↓ to {sl:.5f}")
            
            # Check exit conditions
            if position:
                pip_val = self.pip_value * self.volume * 100000
                
                if position == 'BUY':
                    if low <= sl:
                        profit = (sl - entry_price) * pip_val
                        balance += profit
                        reason = 'TRAIL_SL' if trailing_active else 'SL'
                        trades.append({'type': reason, 'price': sl, 'profit': profit})
                        if not suppress_output:
                            print(f"[{self.strategy_name}] {reason} hit @ {sl:.5f} → Profit: {profit:+.2f}")
                        position = None
                        trailing_active = False
                    elif high >= tp:
                        profit = (tp - entry_price) * pip_val
                        balance += profit
                        trades.append({'type': 'TP', 'price': tp, 'profit': profit})
                        if not suppress_output:
                            print(f"[{self.strategy_name}] TP hit @ {tp:.5f} → Profit: {profit:+.2f}")
                        position = None
                        trailing_active = False
                
                elif position == 'SELL':
                    if high >= sl:
                        profit = (entry_price - sl) * pip_val
                        balance += profit
                        reason = 'TRAIL_SL' if trailing_active else 'SL'
                        trades.append({'type': reason, 'price': sl, 'profit': profit})
                        if not suppress_output:
                            print(f"[{self.strategy_name}] {reason} hit @ {sl:.5f} → Profit: {profit:+.2f}")
                        position = None
                        trailing_active = False
                    elif low <= tp:
                        profit = (entry_price - tp) * pip_val
                        balance += profit
                        trades.append({'type': 'TP', 'price': tp, 'profit': profit})
                        if not suppress_output:
                            print(f"[{self.strategy_name}] TP hit @ {tp:.5f} → Profit: {profit:+.2f}")
                        position = None
                        trailing_active = False
            
            # Reverse on opposite signal
            if position and (
                (position == 'BUY' and signal == 'SELL') or
                (position == 'SELL' and signal == 'BUY')
            ):
                pip_val = self.pip_value * self.volume * 100000
                profit = (price - entry_price) * (1 if position == 'BUY' else -1) * pip_val
                balance += profit
                trades.append({'type': 'REVERSE', 'price': price, 'profit': profit})
                if not suppress_output:
                    print(f"[{self.strategy_name}] Reversed @ {price:.5f} → Profit: {profit:+.2f}")
                position = None
                trailing_active = False
            
            # Open new position
            if not position and signal in ['BUY', 'SELL']:
                position = signal
                entry_price = price
                sl = price - self.sl_pips if signal == 'BUY' else price + self.sl_pips
                tp = price + self.tp_pips if signal == 'BUY' else price - self.tp_pips
                trailing_active = False
                trades.append({
                    'type': 'OPEN', 
                    'side': signal, 
                    'price': entry_price, 
                    'sl': sl, 
                    'tp': tp
                })
                if not suppress_output:
                    print(f"[{self.strategy_name}] Opened {signal} @ {entry_price:.5f}")
            
            equity.append(balance)
        
        return df, trades, equity, balance
    
    def run_backtest(self, days=30, df=None, suppress_output=False):
        """Run the complete backtest. If df is provided, reuse it; otherwise fetch."""
        print(f"Backtesting {self.symbol} with {self.strategy_name} strategy...")
        
        # Fetch or reuse data
        if df is None:
            df = self.fetch_data(days)
        if df is None:
            return
            
        # Initialize strategy
        strategy_manager = StrategyManager(
            strategy_name=self.strategy_name,
            **self.strategy_params
        )
        
        # Trading state
        balance = self.initial_balance
        position = None
        entry_price = sl = tp = 0
        trailing_active = False
        equity = []
        trades = []
        
        print(f"Starting backtest with ${balance:,.2f}...")
        
        for i in range(50, len(df)):
            window = df.iloc[i-50:i]
            
            # Get trading signal
            signal = strategy_manager.get_signal(window)
            
            current_data = df.iloc[i]
            price = current_data['close']
            high = current_data['high']
            low = current_data['low']
            
            # Trailing stop logic
            if position == 'BUY':
                new_sl = high - self.trail_pips
                if new_sl > sl:
                    sl = new_sl
                    trailing_active = True
                    print(f"Trailing SL ↑ to {sl:.5f}")
                    
            elif position == 'SELL':
                new_sl = low + self.trail_pips
                if new_sl < sl:
                    sl = new_sl
                    trailing_active = True
                    print(f"Trailing SL ↓ to {sl:.5f}")
            
            # Check exit conditions
            if position:
                pip_val = self.pip_value * self.volume * 100000
                
                if position == 'BUY':
                    if low <= sl:
                        profit = (sl - entry_price) * pip_val
                        balance += profit
                        reason = 'TRAIL_SL' if trailing_active else 'SL'
                        trades.append({'type': reason, 'price': sl, 'profit': profit})
                        print(f"{reason} hit @ {sl:.5f} → Profit: {profit:+.2f}")
                        position = None
                        trailing_active = False
                    elif high >= tp:
                        profit = (tp - entry_price) * pip_val
                        balance += profit
                        trades.append({'type': 'TP', 'price': tp, 'profit': profit})
                        print(f"TP hit @ {tp:.5f} → Profit: {profit:+.2f}")
                        position = None
                        trailing_active = False
                
                elif position == 'SELL':
                    if high >= sl:
                        profit = (entry_price - sl) * pip_val
                        balance += profit
                        reason = 'TRAIL_SL' if trailing_active else 'SL'
                        trades.append({'type': reason, 'price': sl, 'profit': profit})
                        print(f"{reason} hit @ {sl:.5f} → Profit: {profit:+.2f}")
                        position = None
                        trailing_active = False
                    elif low <= tp:
                        profit = (entry_price - tp) * pip_val
                        balance += profit
                        trades.append({'type': 'TP', 'price': tp, 'profit': profit})
                        print(f"TP hit @ {tp:.5f} → Profit: {profit:+.2f}")
                        position = None
                        trailing_active = False
            
            # Reverse on opposite signal
            if position and (
                (position == 'BUY' and signal == 'SELL') or
                (position == 'SELL' and signal == 'BUY')
            ):
                pip_val = self.pip_value * self.volume * 100000
                profit = (price - entry_price) * (1 if position == 'BUY' else -1) * pip_val
                balance += profit
                trades.append({'type': 'REVERSE', 'price': price, 'profit': profit})
                print(f"Reversed @ {price:.5f} → Profit: {profit:+.2f}")
                position = None
                trailing_active = False
            
            # Open new position
            if not position and signal in ['BUY', 'SELL']:
                position = signal
                entry_price = price
                sl = price - self.sl_pips if signal == 'BUY' else price + self.sl_pips
                tp = price + self.tp_pips if signal == 'BUY' else price - self.tp_pips
                trailing_active = False
                trades.append({
                    'type': 'OPEN', 
                    'side': signal, 
                    'price': entry_price, 
                    'sl': sl, 
                    'tp': tp
                })
                print(f"Opened {signal} @ {entry_price:.5f}")
            
            equity.append(balance)
        
        # Generate results
        self._generate_results(df, equity, trades, balance)
        
        return df, trades, equity
    
    def run_all_strategies(self, strategies, days=30, parallel=True):
        """
        Run multiple strategies over the same dataset (single fetch).
        strategies: list of strategy names, or tuples (name, params_dict)
        parallel: if True, run strategies concurrently using multiprocessing
        Returns: dict[name] -> (df, trades, equity, balance)
        """
        df = self.fetch_data(days)
        if df is None:
            return {}
        
        # Prepare strategy arguments
        strategy_args = []
        for item in strategies:
            if isinstance(item, str):
                name, params = item, {}
            else:
                name, params = item
            strategy_args.append({
                'name': name,
                'params': params,
                'symbol': self.symbol,
                'initial_balance': self.initial_balance,
                'df': df.copy()  # Make a copy for each process
            })
        
        if parallel and len(strategies) > 1:
            print(f"Running {len(strategies)} strategies in parallel...")
            # Run in parallel
            with Pool(min(len(strategies), cpu_count())) as pool:
                results_list = pool.map(_run_single_strategy_parallel, strategy_args)
            results = {args['name']: result for args, result in zip(strategy_args, results_list)}
        else:
            print(f"Running {len(strategies)} strategies sequentially...")
            # Run sequentially
            results = {}
            for args in strategy_args:
                result = _run_single_strategy_parallel(args)
                results[args['name']] = result
        
        # Generate results and plots for all strategies
        print("\nGenerating results and charts...")
        for name, (df_result, trades, equity, balance) in results.items():
            runner = BacktestRunner(
                symbol=self.symbol,
                initial_balance=self.initial_balance,
                strategy_name=name,
                **strategy_args[[a['name'] for a in strategy_args].index(name)]['params']
            )
            runner._generate_results(df_result, equity, trades, balance)
        
        return results
    
    def _generate_results(self, df, equity, trades, final_balance):
        """Generate performance reports and charts"""
        total_return = (final_balance - self.initial_balance) / self.initial_balance * 100
        closed_trades = [t for t in trades if t['type'] in ['SL', 'TRAIL_SL', 'TP', 'REVERSE']]
        winning_trades = [t for t in closed_trades if t.get('profit', 0) > 0]
        win_rate = len(winning_trades) / max(len(closed_trades), 1) * 100
        
        print(f"\n{'='*60}")
        print(f"BACKTEST COMPLETE - {self.strategy_name.upper()} STRATEGY")
        print(f"   Final Balance: ${final_balance:,.2f}")
        print(f"   Total Return:  {total_return:+.2f}%")
        print(f"   Win Rate:      {win_rate:.1f}%")
        print(f"   Total Trades:  {len(closed_trades)}")
        print(f"{'='*60}")
        
        # Plot
        plt.figure(figsize=(14, 7))
        plt.plot(df['time'][:len(equity)], equity, label='Equity Curve', color='green', linewidth=2)
        plt.title(f"Backtest: {self.symbol} | {self.strategy_name} | {total_return:+.2f}%")
        plt.xlabel("Time")
        plt.ylabel("Balance ($)")
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        
        os.makedirs("backtests", exist_ok=True)
        plt.savefig(f"backtests/{self.symbol}_{self.strategy_name}_backtest.png", dpi=150)
        plt.show()
        
        # Save trades
        pd.DataFrame(trades).to_csv(f"backtests/{self.symbol}_{self.strategy_name}_trades.csv", index=False)
        print(f"Trade log saved to backtests/{self.symbol}_{self.strategy_name}_trades.csv")

def _run_single_strategy_parallel(args):
    """Helper function for parallel execution"""
    runner = BacktestRunner(
        symbol=args['symbol'],
        initial_balance=args['initial_balance'],
        strategy_name=args['name'],
        **args['params']
    )
    return runner._run_backtest_core(args['df'], suppress_output=True)


if __name__ == "__main__":
    # Example usage
    runner = BacktestRunner(
        symbol="EURUSD",
        strategy_name="trend_following",
        lookback_fast=8,
        lookback_slow=21
    )
    runner.run_backtest(days=7)