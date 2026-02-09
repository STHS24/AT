import MetaTrader5 as mt5
import sys
import json
import os
import time
import signal
from datetime import datetime

# Import strategy system
from strategies import (
    SimpleStrategy,
    MAStrategy,
    RSIStrategy,
    MACDStrategy,
    StrategyManager
)

# Import AI mode
from AIT import AIMode

# Import risk management
from risk_manager import RiskManager

# Import logging and analytics
from trade_logger import TradeLogger
from analytics import PerformanceAnalytics

# ------------------------------
# GLOBAL STATE
# ------------------------------
running = True  # Flag for graceful shutdown


def signal_handler(sig, frame):
    """Handle CTRL+C for graceful shutdown."""
    global running
    print("\n\n⚠️  Shutdown signal received. Closing positions and exiting gracefully...")
    running = False


# Register signal handler
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ------------------------------
# CONFIGURATION
# ------------------------------
CONFIG_PATH = os.path.join("config", "settings.json")
LOG_PATH = os.path.join("logs", "trades.log")

# Load config
try:
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
except FileNotFoundError:
    print("❌ settings.json not found. Please create config/settings.json")
    sys.exit(1)

SYMBOL = config.get("symbol", "EURUSD")
VOLUME = float(config.get("volume", 0.1))
DEVIATION = int(config.get("deviation", 50))
ANALYSIS_INTERVAL = int(config.get("analysis_interval_seconds", 5))  # How often to analyze market
TRADE_INTERVAL = int(config.get("trade_interval_seconds", 60))  # Cooldown between trades
ENABLE_URGENT_BYPASS = config.get("enable_urgent_bypass", True)  # Allow urgent trades
MAX_CONCURRENT_TRADES = int(config.get("max_concurrent_trades", 3))
ENABLE_CONTINUOUS = config.get("enable_continuous_trading", False)

# Track last trade time for cooldown
last_trade_time = 0

# Ensure logs folder exists
os.makedirs("logs", exist_ok=True)


# ------------------------------
# STRATEGY INITIALIZATION
# ------------------------------
def initialize_strategies():
    """
    Initialize trading strategies from configuration.

    Returns:
        StrategyManager: Configured strategy manager
    """
    strategy_config = config.get("strategy_config", {})
    combination_method = strategy_config.get("combination_method", "majority")

    # Map timeframe strings to MT5 constants
    timeframe_map = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1
    }

    # Create strategy manager
    manager = StrategyManager(method=combination_method)

    # Strategy class mapping (only technical strategies)
    strategy_classes = {
        "SimpleStrategy": SimpleStrategy,
        "MAStrategy": MAStrategy,
        "RSIStrategy": RSIStrategy,
        "MACDStrategy": MACDStrategy
    }

    # Initialize each configured strategy
    for strategy_name, strategy_class in strategy_classes.items():
        strategy_settings = strategy_config.get(strategy_name, {})

        if not strategy_settings:
            continue

        # Get parameters and convert timeframe strings
        params = strategy_settings.get("params", {}).copy()
        if "timeframe" in params and isinstance(params["timeframe"], str):
            params["timeframe"] = timeframe_map.get(params["timeframe"], mt5.TIMEFRAME_M5)

        # Create strategy instance
        strategy = strategy_class(params)

        # Set enabled state
        if not strategy_settings.get("enabled", True):
            strategy.disable()

        # Set weight
        weight = strategy_settings.get("weight", 1.0)
        strategy.set_weight(weight)

        # Add to manager
        manager.add_strategy(strategy)

    print(f"\n[Config] Strategy Manager initialized: {manager}")
    print(f"[Config] Active strategies: {len([s for s in manager.strategies if s.enabled])}/{len(manager.strategies)}")

    return manager


# Initialize Risk Manager
RISK_MANAGER = RiskManager(config)
print(f"[Config] Risk Manager initialized")
print(f"[Config] Risk per trade: {RISK_MANAGER.risk_percentage}%")
print(f"[Config] SL/TP method: {RISK_MANAGER.sl_method}/{RISK_MANAGER.tp_method}")
print(f"[Config] Daily limits: Loss=${RISK_MANAGER.daily_loss_limit}, Profit=${RISK_MANAGER.daily_profit_target}")

# Initialize AI Mode
AI_MODE = None
ai_mode_config = config.get("ai_mode", {})
if ai_mode_config.get("enabled", False):
    try:
        AI_MODE = AIMode(ai_mode_config, RISK_MANAGER)
    except Exception as e:
        print(f"[Config] ⚠️  Failed to initialize AI Mode: {e}")
        print(f"[Config] Will use fallback strategies")

# Initialize strategy manager (fallback)
STRATEGY_MANAGER = initialize_strategies()

# Initialize Trade Logger and Analytics
TRADE_LOGGER = TradeLogger()
ANALYTICS = PerformanceAnalytics()
print(f"[Config] Trade Logger and Analytics initialized")

# ------------------------------
# HELPER FUNCTIONS
# ------------------------------
def initialize_mt5():
    """Initialize MT5 connection and validate account."""
    print("🔌 Initializing MetaTrader 5...")

    if not mt5.initialize():
        print("❌ MT5 initialization failed:", mt5.last_error())
        return False

    account_info = mt5.account_info()
    if account_info is None:
        print("❌ Could not retrieve account info. Is MetaTrader 5 logged in?")
        return False

    print(f"✅ Connected to account #{account_info.login} | Balance: {account_info.balance:.2f}\n")
    return True


def prepare_symbol(symbol):
    """Prepare and validate trading symbol."""
    if not mt5.symbol_select(symbol, True):
        print(f"❌ Could not select symbol {symbol}")
        return False

    symbol_info = mt5.symbol_info(symbol)
    if not symbol_info:
        print(f"❌ Symbol {symbol} not found.")
        return False

    print(f"✅ Symbol {symbol} ready for trading.\n")
    return True


def get_open_positions(symbol=None):
    """
    Get open positions, optionally filtered by symbol.

    Args:
        symbol: Optional symbol to filter positions

    Returns:
        List of open positions
    """
    if symbol:
        positions = mt5.positions_get(symbol=symbol)
    else:
        positions = mt5.positions_get()

    return positions if positions is not None else []


def has_open_position(symbol):
    """
    Check if there's already an open position for the symbol.

    Args:
        symbol: Trading symbol to check

    Returns:
        Boolean indicating if position exists
    """
    positions = get_open_positions(symbol)
    return len(positions) > 0


def can_open_new_trade():
    """
    Check if we can open a new trade based on max concurrent trades limit.

    Returns:
        Boolean indicating if new trade can be opened
    """
    all_positions = get_open_positions()
    return len(all_positions) < MAX_CONCURRENT_TRADES

def log_trade(action, result, volume, price, sl, tp, strategy="Combined"):
    """
    Log trade execution using enhanced logger.

    Args:
        action: Trade action (BUY/SELL)
        result: MT5 order result
        volume: Trade volume
        price: Entry price
        sl: Stop loss
        tp: Take profit
        strategy: Strategy name
    """
    # Use new enhanced logger
    TRADE_LOGGER.log_trade_open(
        symbol=SYMBOL,
        action=action,
        result=result,
        volume=volume,
        entry_price=price,
        sl=sl,
        tp=tp,
        strategy=strategy
    )

    # Also keep old format for backward compatibility
    with open(LOG_PATH, "a") as f:
        f.write(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
            f"{action:<12} | "
            f"{result.order:<12} | "
            f"Price: {price:.5f} | SL: {sl:.5f} | TP: {tp:.5f} | Retcode: {result.retcode}\n"
        )


def execute_trade(symbol, action):
    """
    Execute a trade based on the action signal with risk management.

    Args:
        symbol: Trading symbol
        action: Trade action ('BUY' or 'SELL')

    Returns:
        Boolean indicating success
    """
    # Check if trading is allowed (daily limits)
    can_trade, reason = RISK_MANAGER.can_trade()
    if not can_trade:
        print(f"🚫 Trading disabled: {reason}")
        return False

    print(f"📤 Sending {action} trade request...")

    # Get latest prices
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print(f"❌ Could not get tick data for {symbol}")
        return False

    price = tick.ask if action == "BUY" else tick.bid

    # Calculate SL/TP using Risk Manager
    sl, tp = RISK_MANAGER.calculate_sl_tp(symbol, action, price)

    # Calculate SL distance in pips for lot sizing
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"❌ Could not get symbol info for {symbol}")
        return False

    point = symbol_info.point
    sl_distance_pips = abs(price - sl) / (point * 10)  # Convert to pips

    # Calculate optimal lot size (if dynamic sizing enabled)
    if config.get("risk_management", {}).get("enable_dynamic_lot_sizing", False):
        volume = RISK_MANAGER.calculate_lot_size(symbol, sl_distance_pips)
        print(f"💰 Dynamic lot size: {volume} (Risk: {RISK_MANAGER.risk_percentage}%, SL: {sl_distance_pips:.1f} pips)")
    else:
        volume = VOLUME
        print(f"💰 Fixed lot size: {volume}")

    # Validate trade
    is_valid, validation_reason = RISK_MANAGER.validate_trade(symbol, action, volume)
    if not is_valid:
        print(f"🚫 Trade validation failed: {validation_reason}")
        return False

    # Determine order type
    order_type = mt5.ORDER_TYPE_BUY if action == "BUY" else mt5.ORDER_TYPE_SELL

    # Build order request
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": DEVIATION,
        "magic": 123456,
        "comment": f"Python MT5 Bot {action}",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    # Execute order
    result = mt5.order_send(request)

    if result is None:
        print("❌ Order send failed - no result returned")
        return False

    print(f"\nTrade Result: {result}")

    # Log and report result
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"\n✅ {action} executed successfully!")
        print(f"   Ticket: {result.order}")
        print(f"   Price:  {result.price}")
        print(f"   SL:     {sl}")
        print(f"   TP:     {tp}")

        # Get strategy name from manager
        strategy_name = STRATEGY_MANAGER.method.upper()
        log_trade(action, result, volume, price, sl, tp, strategy=strategy_name)
        return True
    else:
        print(f"\n❌ {action} failed! Code {result.retcode}: {result.comment}")
        log_trade(f"{action}_FAILED", result, volume, price, sl, tp, strategy="FAILED")
        return False


def close_position(position, volume=None, reason="Manual close"):
    """
    Close an open position (fully or partially).

    Args:
        position: MT5 position object
        volume: Volume to close (None = close all)
        reason: Reason for closing

    Returns:
        bool: True if closed successfully, False otherwise
    """
    tick = mt5.symbol_info_tick(position.symbol)
    if tick is None:
        print(f"❌ Could not get tick data for {position.symbol}")
        return False

    # Determine close volume
    close_volume = volume if volume is not None else position.volume
    is_partial = close_volume < position.volume

    # Determine close price and order type
    if position.type == mt5.ORDER_TYPE_BUY:
        close_price = tick.bid
        order_type = mt5.ORDER_TYPE_SELL
        action_str = "CLOSE_BUY"
    else:
        close_price = tick.ask
        order_type = mt5.ORDER_TYPE_BUY
        action_str = "CLOSE_SELL"

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": position.symbol,
        "volume": close_volume,
        "type": order_type,
        "position": position.ticket,
        "price": close_price,
        "deviation": DEVIATION,
        "magic": 234000,
        "comment": f"AI: {reason}" if "AI" in reason else "python script close",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    result = mt5.order_send(request)

    if result.retcode == mt5.TRADE_RETCODE_DONE:
        profit = position.profit * (close_volume / position.volume)
        commission = (position.commission if hasattr(position, 'commission') else 0) * (close_volume / position.volume)
        swap = (position.swap if hasattr(position, 'swap') else 0) * (close_volume / position.volume)

        if is_partial:
            print(f"✅ Position #{position.ticket} partially closed ({close_volume}/{position.volume} lots) | Profit: {profit:.2f}")
            print(f"   Reason: {reason}")
        else:
            print(f"✅ Position #{position.ticket} closed | Profit: {profit:.2f}")
            print(f"   Reason: {reason}")

        # Log trade close
        TRADE_LOGGER.log_trade_close(
            ticket=position.ticket,
            exit_price=close_price,
            profit=profit,
            commission=commission,
            swap=swap
        )

        # Update daily P/L tracking
        RISK_MANAGER.update_daily_pnl(profit)

        return True
    else:
        print(f"❌ Failed to close position #{position.ticket} | Code: {result.retcode}")
        return False


def manage_open_positions_with_ai(symbol):
    """
    Use AI to analyze and manage open positions.

    Args:
        symbol: Trading symbol
    """
    if not AI_MODE or not AI_MODE.enabled:
        return  # AI mode not enabled

    # Get open positions for this symbol
    positions = get_open_positions(symbol)

    if not positions:
        return  # No positions to manage

    print(f"\n{'='*60}")
    print(f"🔍 AI Position Management - Analyzing {len(positions)} position(s)")
    print(f"{'='*60}")

    for position in positions:
        try:
            # Get AI recommendation for this position
            decision = AI_MODE.manage_position(position, symbol, config)

            if not decision:
                continue

            action = decision.get("action", "HOLD")
            reasoning = decision.get("reasoning", "")
            confidence = decision.get("confidence", 0.0)

            if action == "CLOSE":
                print(f"\n🚨 AI recommends CLOSING position #{position.ticket}")
                print(f"   Confidence: {confidence:.2f}")
                print(f"   Reasoning: {reasoning[:150]}...")
                close_position(position, reason=f"AI Close: {reasoning[:50]}")

            elif action == "CLOSE_PARTIAL":
                partial_pct = decision.get("partial_percentage", 0.5)
                close_volume = round(position.volume * partial_pct, 2)

                print(f"\n⚠️  AI recommends PARTIAL CLOSE of position #{position.ticket}")
                print(f"   Closing: {partial_pct*100:.0f}% ({close_volume} lots)")
                print(f"   Confidence: {confidence:.2f}")
                print(f"   Reasoning: {reasoning[:150]}...")
                close_position(position, volume=close_volume, reason=f"AI Partial: {reasoning[:50]}")

            else:  # HOLD
                print(f"\n📊 AI recommends HOLDING position #{position.ticket}")
                print(f"   Current P/L: ${position.profit:.2f}")

        except Exception as e:
            print(f"❌ Error analyzing position #{position.ticket}: {e}")


def trading_iteration(symbol, force_execution=False):
    """
    Perform one trading iteration: check signal, validate, and execute if appropriate.

    Args:
        symbol: Trading symbol
        force_execution: If True, bypass trade cooldown (for urgent trades)
    """
    global last_trade_time

    print(f"\n{'='*60}")
    print(f"🔄 Trading iteration at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    # Display daily P/L status
    daily_pnl = RISK_MANAGER.get_daily_pnl()
    can_trade, reason = RISK_MANAGER.can_trade()
    print(f"📊 Daily P/L: ${daily_pnl:.2f} | Status: {reason}")

    if not can_trade:
        print(f"🚫 Trading halted: {reason}")
        return

    # First, manage existing positions with AI (if enabled)
    # Position management can always run (not subject to trade cooldown)
    if AI_MODE and AI_MODE.enabled:
        manage_open_positions_with_ai(symbol)

    # Check trade cooldown
    current_time = time.time()
    time_since_last_trade = current_time - last_trade_time
    cooldown_remaining = max(0, TRADE_INTERVAL - time_since_last_trade)

    if cooldown_remaining > 0 and not force_execution:
        print(f"⏳ Trade cooldown: {cooldown_remaining:.0f}s remaining (use urgent bypass if needed)")
        return

    # Get trading signal: AI mode first, fallback to strategies
    action = "NONE"

    if AI_MODE and AI_MODE.enabled:
        # Use AI mode
        action = AI_MODE.get_trading_signal(symbol, config)

    if action == "NONE":
        # Fallback to strategy manager
        print(f"[Trading] Using fallback strategies...")
        action = STRATEGY_MANAGER.generate_combined_signal(symbol)

    if action not in ["BUY", "SELL"]:
        print("⚠️  No trade signal from strategy.")
        return

    # Check existing positions on this symbol
    existing_positions = get_open_positions(symbol)

    if existing_positions:
        # Check if we have opposite positions to close
        for pos in existing_positions:
            pos_type = "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL"

            # If signal is opposite to position, close the position
            if (action == "BUY" and pos_type == "SELL") or (action == "SELL" and pos_type == "BUY"):
                print(f"🔄 Signal changed from {pos_type} to {action}. Closing position #{pos.ticket}...")
                close_position(pos)
            elif pos_type == action:
                print(f"ℹ️  Already have a {pos_type} position on {symbol}. Signal agrees.")
                # Check if we can add more positions
                if can_open_new_trade():
                    print(f"💡 Adding another {action} position (pyramiding)...")
                else:
                    print(f"⚠️  Max concurrent trades reached. Skipping additional position.")
                    return

    # Check if we can open new trade
    if not can_open_new_trade():
        open_count = len(get_open_positions())
        print(f"⚠️  Max concurrent trades reached ({open_count}/{MAX_CONCURRENT_TRADES}). Skipping trade.")
        return

    # Execute the trade
    success = execute_trade(symbol, action)

    # Update last trade time if trade was executed
    if success:
        last_trade_time = time.time()
        if force_execution:
            print("🚨 Urgent trade executed (bypassed cooldown)")


def run_single_trade():
    """Run a single trade execution (original behavior)."""
    if not initialize_mt5():
        sys.exit(1)

    if not prepare_symbol(SYMBOL):
        mt5.shutdown()
        sys.exit(1)

    trading_iteration(SYMBOL)

    print("\n🔚 MT5 connection closed.")
    mt5.shutdown()


def run_continuous_trading():
    """Run continuous trading loop with separate analysis and execution intervals."""
    global running

    if not initialize_mt5():
        sys.exit(1)

    if not prepare_symbol(SYMBOL):
        mt5.shutdown()
        sys.exit(1)

    print(f"\n🔁 Starting continuous trading mode...")
    print(f"   Analysis interval: {ANALYSIS_INTERVAL} seconds (constant market monitoring)")
    print(f"   Trade cooldown: {TRADE_INTERVAL} seconds (minimum time between trades)")
    print(f"   Urgent bypass: {'Enabled' if ENABLE_URGENT_BYPASS else 'Disabled'}")
    print(f"   Max concurrent trades: {MAX_CONCURRENT_TRADES}")
    print(f"   Press CTRL+C to stop gracefully\n")

    iteration_count = 0

    try:
        while running:
            iteration_count += 1

            # Check if AI detected urgent opportunity
            force_execution = False
            if ENABLE_URGENT_BYPASS and AI_MODE and AI_MODE.enabled and AI_MODE.is_last_decision_urgent():
                force_execution = True
                print("🚨 URGENT OPPORTUNITY DETECTED - Bypassing trade cooldown!")

            trading_iteration(SYMBOL, force_execution=force_execution)

            # Display open positions summary
            positions = get_open_positions()
            print(f"\n📊 Open positions: {len(positions)}/{MAX_CONCURRENT_TRADES}")

            if not running:
                break

            # Wait for next analysis iteration (much shorter than trade interval)
            print(f"\n⏳ Next analysis in {ANALYSIS_INTERVAL} seconds...")

            # Sleep in small increments to allow for responsive shutdown
            for _ in range(ANALYSIS_INTERVAL):
                if not running:
                    break
                time.sleep(1)

    except Exception as e:
        print(f"\n❌ Error in trading loop: {e}")

    finally:
        print(f"\n🔚 Shutting down after {iteration_count} iterations...")

        # Generate and display performance report
        try:
            print("\n" + "="*80)
            print("📊 GENERATING PERFORMANCE REPORT...")
            print("="*80)
            ANALYTICS.print_summary_report(days=7)
        except Exception as e:
            print(f"⚠️  Could not generate performance report: {e}")

        print("\n   Closing MT5 connection...")
        mt5.shutdown()
        print("✅ Shutdown complete.")


# ------------------------------
# MAIN EXECUTION
# ------------------------------
if __name__ == "__main__":
    if ENABLE_CONTINUOUS:
        run_continuous_trading()
    else:
        run_single_trade()
