# backtest/backtrader_engine.py
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, Optional
import time
import array

try:
    import backtrader as bt
except ImportError as e:
    raise ImportError("Backtrader is required. Install with: pip install backtrader") from e

from backtest.strategies.strategy_manager import StrategyManager


@dataclass
class BTConfig:
    symbol: str = "EURUSD"
    stake: float = 10000  # units
    commission: float = 0.0002  # 2 bps per trade
    slippage: float = 0.0001  # 1 pip equivalent in price units (approx)
    sl_pips: float = 0.001
    tp_pips: float = 0.002
    cash: float = 10000


class FixedStakeSizer(bt.Sizer):
    params = (('stake', 10000),)

    def _getsizing(self, comminfo, cash, data, isbuy):
        return self.params.stake


class StrategyAdapter(bt.Strategy):
    params = dict(
        strategy_name="trend_following",
        strategy_params={},
        sl_pips=0.001,
        tp_pips=0.002,
        window=20,  # Reduced from 50 for performance
    )

    def __init__(self):
        # Initialize manager once
        self.manager = StrategyManager(
            strategy_name=self.p.strategy_name,
            **self.p.strategy_params,
        )
        self.data_close = self.datas[0].close
        self.data_high = self.datas[0].high
        self.data_low = self.datas[0].low
        self.orders = []
        
        # Performance optimizations
        self.last_window_len = 0
        self.cached_window = None
        self.progress_interval = 1000
        
        print(f"🚀 StrategyAdapter initialized with window={self.p.window}")

    def _convert_array_to_float(self, arr):
        """Convert array.array to list of floats efficiently"""
        return [float(x) for x in arr]

    def _build_window_efficiently(self):
        """Build window DataFrame efficiently handling array.array types"""
        lookback = self.p.window
        
        try:
            # Get data as arrays and convert to lists of floats
            times_array = self.datas[0].datetime.get(size=lookback)
            closes_array = self.datas[0].close.get(size=lookback)
            
            # Convert to proper types
            times = [bt.num2date(t) for t in times_array]
            closes = self._convert_array_to_float(closes_array)
            
            # Create base DataFrame
            window = pd.DataFrame({
                'time': pd.to_datetime(times),
                'close': closes,
            })
            
            # Only add other columns if strategy actually needs them
            # For RSI strategy, we only need close prices
            if self.p.strategy_name not in ['rsi', 'moving_average']:  # Add other simple strategies
                window['open'] = self._convert_array_to_float(self.datas[0].open.get(size=lookback))
                window['high'] = self._convert_array_to_float(self.datas[0].high.get(size=lookback))
                window['low'] = self._convert_array_to_float(self.datas[0].low.get(size=lookback))
                window['volume'] = self._convert_array_to_float(self.datas[0].volume.get(size=lookback))
            
            return window
            
        except Exception as e:
            print(f"❌ Error building window: {e}")
            # Fallback to original method but more efficient
            return self._build_window_fallback(lookback)

    def _build_window_fallback(self, lookback):
        """Fallback window builder - more robust but slower"""
        rel_start, rel_end = -lookback, 0
        
        times = [bt.num2date(self.datas[0].datetime[i]) for i in range(rel_start, rel_end)]
        closes = [float(self.datas[0].close[i]) for i in range(rel_start, rel_end)]
        
        window = pd.DataFrame({
            'time': pd.to_datetime(times),
            'close': closes,
        })
        
        # Only add full OHLCV if needed
        if self.p.strategy_name not in ['rsi', 'moving_average']:
            window['open'] = [float(self.datas[0].open[i]) for i in range(rel_start, rel_end)]
            window['high'] = [float(self.datas[0].high[i]) for i in range(rel_start, rel_end)]
            window['low'] = [float(self.datas[0].low[i]) for i in range(rel_start, rel_end)]
            window['volume'] = [float(self.datas[0].volume[i]) for i in range(rel_start, rel_end)]
        
        return window

    def _get_signal_fast(self):
        """Get signal with minimal data processing"""
        if len(self.data) < self.p.window:
            return None
            
        # Only rebuild window if data has changed significantly
        current_len = len(self.data)
        if (self.cached_window is None or 
            len(self.cached_window) != self.p.window or
            current_len - self.last_window_len >= self.p.window):
            
            self.cached_window = self._build_window_efficiently()
            self.last_window_len = current_len
        
        try:
            return self.manager.get_signal(self.cached_window)
        except Exception as e:
            if len(self.data) % 500 == 0:  # Don't spam errors
                print(f"⚠️  Signal error at bar {len(self.data)}: {e}")
            return None

    def next(self):
        # Progress indicator
        if len(self.data) % self.progress_interval == 0:
            print(f"📊 Processing bar {len(self.data)}/{len(self.data_close)}...")
        
        # Skip if pending orders
        if any(o.status in [bt.Order.Submitted, bt.Order.Accepted] for o in self.orders):
            return

        # Get signal efficiently
        signal = self._get_signal_fast()
        if signal not in ['BUY', 'SELL']:
            return

        price = float(self.data_close[0])
        sl = price - self.p.sl_pips
        tp = price + self.p.tp_pips

        position_size = self.broker.getposition(self.datas[0]).size

        if position_size == 0:
            if signal == 'BUY':
                parent = self.buy(size=self.sizer.params.stake)
                self.sell(exectype=bt.Order.Stop, price=sl, parent=parent)
                self.sell(exectype=bt.Order.Limit, price=tp, parent=parent)
                if len(self.data) % 10 == 0:  # Reduce logging frequency
                    print(f"✅ BUY signal @ {price:.5f}")
            elif signal == 'SELL':
                parent = self.sell(size=self.sizer.params.stake)
                self.buy(exectype=bt.Order.Stop, price=tp, parent=parent)
                self.buy(exectype=bt.Order.Limit, price=sl, parent=parent)
                if len(self.data) % 10 == 0:
                    print(f"✅ SELL signal @ {price:.5f}")
        else:
            # Reverse logic - only close if opposite signal
            if (position_size > 0 and signal == 'SELL') or (position_size < 0 and signal == 'BUY'):
                self.close()
                if len(self.data) % 10 == 0:
                    print(f"🔄 Reversing position @ {price:.5f}")

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Margin, order.Rejected]:
            # Prune completed/canceled orders
            self.orders = [o for o in self.orders if o.status not in [
                order.Completed, order.Canceled, order.Margin, order.Rejected]]
            
            if order.status == order.Completed and len(self.data) % 20 == 0:
                print(f"🎯 Order completed: {order.ordtypename()} {order.size} units")


def run_backtrader_with_df(df: pd.DataFrame,
                        strategy_name: str = "trend_following",
                        strategy_params: Optional[Dict[str, Any]] = None,
                        config: Optional[BTConfig] = None):
    """Run Backtrader using a pandas DataFrame and StrategyManager signals.

    Returns: cerebro, results, analyzers dict
    """
    if strategy_params is None:
        strategy_params = {}
    if config is None:
        config = BTConfig()

    # Ensure DataFrame has expected columns
    required = {'time', 'open', 'high', 'low', 'close', 'volume'}
    if not required.issubset(df.columns):
        raise ValueError(f"DataFrame must contain columns: {required}")

    print(f"🚀 Starting Backtrader backtest with {len(df)} bars...")
    
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(config.cash)
    cerebro.broker.setcommission(commission=config.commission)
    cerebro.broker.set_slippage_perc(perc=config.slippage)
    cerebro.addsizer(FixedStakeSizer, stake=config.stake)

    # Feed - optimize data loading
    df_bt = df.copy()
    df_bt = df_bt.rename(columns={'time': 'datetime'})
    df_bt.set_index('datetime', inplace=True)
    
    # Use faster data loading
    data = bt.feeds.PandasData(dataname=df_bt)
    cerebro.adddata(data, name=config.symbol)

    # Strategy with optimized parameters
    cerebro.addstrategy(
        StrategyAdapter,
        strategy_name=strategy_name,
        strategy_params=dict(strategy_params, symbol=config.symbol),
        sl_pips=config.sl_pips,
        tp_pips=config.tp_pips,
        window=20,  # Reduced from 50 for performance
    )

    # Analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='timereturn')

    # Run with timing
    start_time = time.time()
    print("⏳ Running backtest...")
    
    results = cerebro.run()
    
    end_time = time.time()
    print(f"✅ Backtest completed in {end_time - start_time:.2f} seconds")

    strat = results[0]
    analyzers = {
        'sharpe': strat.analyzers.sharpe.get_analysis(),
        'drawdown': strat.analyzers.drawdown.get_analysis(),
        'trades': strat.analyzers.trades.get_analysis(),
    }
    return cerebro, results, analyzers


# Simple version for RSI strategy that only needs close prices
class SimpleRSIStrategyAdapter(StrategyAdapter):
    """Optimized version for RSI strategy that only needs close prices"""
    
    def _build_window_efficiently(self):
        """Build minimal window with only close prices for RSI"""
        lookback = self.p.window
        
        # Get close prices efficiently
        closes_array = self.datas[0].close.get(size=lookback)
        closes = [float(x) for x in closes_array]
        
        # Create minimal DataFrame with only what RSI needs
        window = pd.DataFrame({
            'close': closes,
        })
        
        return window