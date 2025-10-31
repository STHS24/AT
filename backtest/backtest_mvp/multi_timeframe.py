# backtest/backtest_mvp/multi_timeframe.py
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from strategy import trade_decision

def multi_timeframe_confirmation(symbol, primary_tf=1, confirm_tf=5):
    """
    Get primary signal and require higher timeframe confirmation.
    Returns confirmed signal or 'HOLD' if no confirmation.
    """
    primary_signal = trade_decision(symbol)
    
    if primary_signal == 'HOLD':
        return 'HOLD'
    
    # Fetch higher timeframe data for confirmation
    if not mt5.initialize():
        return primary_signal  # Fallback to primary if MT5 fails
    
    try:
        # Get confirmation timeframe data (M5)
        confirm_rates = mt5.copy_rates_from_pos(symbol, confirm_tf, 0, 50)
        if confirm_rates is None or len(confirm_rates) < 20:
            return primary_signal  # Fallback
            
        confirm_df = pd.DataFrame(confirm_rates)
        
        # Simple trend confirmation: price above/below EMA
        ema_period = 20
        confirm_df['ema'] = confirm_df['close'].ewm(span=ema_period).mean()
        
        current_close = confirm_df['close'].iloc[-1]
        current_ema = confirm_df['ema'].iloc[-1]
        
        # Confirm signals with higher timeframe trend
        if primary_signal == 'BUY' and current_close > current_ema:
            return 'BUY'
        elif primary_signal == 'SELL' and current_close < current_ema:
            return 'SELL'
        else:
            return 'HOLD'  # No confirmation
            
    except Exception as e:
        print(f"MTF confirmation error: {e}")
        return primary_signal  # Fallback to primary signal
    finally:
        mt5.shutdown()

# Make sure the function is available for import
__all__ = ['multi_timeframe_confirmation']