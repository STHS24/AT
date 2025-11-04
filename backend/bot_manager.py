"""
Bot Manager - Wraps existing trading bot logic for API control.

This module provides a clean interface to start/stop the bot and monitor its state
without modifying the core trading logic in main.py.
"""

import asyncio
import threading
import MetaTrader5 as mt5
from datetime import datetime
from typing import Optional, Dict, Any, List
import json
import os
import sys

# Add parent directory to path to import bot modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies import SimpleStrategy, MAStrategy, RSIStrategy, MACDStrategy, StrategyManager
from risk_manager import RiskManager
from trade_logger import TradeLogger
from analytics import PerformanceAnalytics
from backend.websocket_manager import manager as ws_manager


class BotManager:
    """Manages the trading bot lifecycle and state."""
    
    def __init__(self):
        """Initialize bot manager."""
        self.is_running = False
        self.bot_thread: Optional[threading.Thread] = None
        self.started_at: Optional[datetime] = None
        self.stopped_at: Optional[datetime] = None
        self.total_trades = 0
        self.total_profit = 0.0

        # Load configuration
        self.config = self._load_config()

        # Bot components (initialized when bot starts)
        self.strategy_manager: Optional[StrategyManager] = None
        self.risk_manager: Optional[RiskManager] = None
        self.trade_logger: Optional[TradeLogger] = None
        self.analytics: Optional[PerformanceAnalytics] = None

        # Control flag
        self._stop_flag = False

        # Event loop for async operations (set when bot starts)
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        
        print("[BotManager] Initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from settings.json."""
        config_path = os.path.join("config", "settings.json")
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[BotManager] Config file not found: {config_path}")
            return {}
    
    def _initialize_mt5(self) -> bool:
        """Initialize MT5 connection."""
        if not mt5.initialize():
            print("[BotManager] MT5 initialization failed")
            return False
        
        account_info = mt5.account_info()
        if account_info is None:
            print("[BotManager] Failed to get account info")
            mt5.shutdown()
            return False
        
        print(f"[BotManager] Connected to MT5 - Account: {account_info.login}")
        return True
    
    def _initialize_strategies(self) -> StrategyManager:
        """Initialize trading strategies from configuration."""
        strategy_config = self.config.get("strategy_config", {})
        combination_method = strategy_config.get("combination_method", "majority")
        
        # Timeframe mapping
        timeframe_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1
        }
        
        manager = StrategyManager(method=combination_method)
        
        # Strategy classes
        strategy_classes = {
            "SimpleStrategy": SimpleStrategy,
            "MAStrategy": MAStrategy,
            "RSIStrategy": RSIStrategy,
            "MACDStrategy": MACDStrategy
        }
        
        # Initialize enabled strategies
        for strategy_name, strategy_class in strategy_classes.items():
            strategy_cfg = strategy_config.get(strategy_name, {})
            if strategy_cfg.get("enabled", False):
                params = strategy_cfg.get("params", {})
                
                # Convert timeframe string to MT5 constant
                if "timeframe" in params:
                    params["timeframe"] = timeframe_map.get(params["timeframe"], mt5.TIMEFRAME_M5)
                
                strategy = strategy_class(params=params)
                strategy.set_weight(strategy_cfg.get("weight", 1.0))
                manager.add_strategy(strategy)
                print(f"[BotManager] Added strategy: {strategy_name}")
        
        return manager
    
    def _prepare_symbol(self, symbol: str) -> bool:
        """Prepare symbol for trading."""
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(f"[BotManager] Symbol {symbol} not found")
            return False
        
        if not symbol_info.visible:
            if not mt5.symbol_select(symbol, True):
                print(f"[BotManager] Failed to select {symbol}")
                return False
        
        return True
    
    def _get_open_positions(self) -> List[Any]:
        """Get list of open positions."""
        positions = mt5.positions_get()
        return list(positions) if positions else []
    
    def _can_open_new_trade(self) -> bool:
        """Check if we can open a new trade."""
        max_trades = self.config.get("max_concurrent_trades", 3)
        open_positions = len(self._get_open_positions())
        return open_positions < max_trades

    def _schedule_async(self, coro):
        """
        Schedule an async coroutine from the bot thread to run in the main event loop.
        This is thread-safe and allows the bot thread to call async WebSocket functions.

        Uses asyncio.run_coroutine_threadsafe() which is the correct way to schedule
        coroutines from a different thread into a specific event loop.
        """
        if self._event_loop and not self._event_loop.is_closed():
            try:
                # Schedule the coroutine in the main event loop and wait for result
                future = asyncio.run_coroutine_threadsafe(coro, self._event_loop)
                # Wait for completion with timeout to avoid blocking forever
                future.result(timeout=5.0)
            except Exception as e:
                print(f"[BotManager] Error scheduling async task: {e}")
        else:
            print("[BotManager] Warning: Event loop not available for async scheduling")

    async def _broadcast_price_update(self, symbol: str):
        """Broadcast current price to WebSocket clients."""
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            await ws_manager.broadcast_price_update(
                symbol=symbol,
                bid=tick.bid,
                ask=tick.ask,
                last=tick.last,
                volume=tick.volume,
                time=datetime.fromtimestamp(tick.time)
            )

    async def _broadcast_log(self, level: str, message: str):
        """Broadcast log message to WebSocket clients."""
        await ws_manager.broadcast_log_event(level, message, "BotManager")
    
    def _execute_trade(self, symbol: str, action: str) -> bool:
        """
        Execute a trade based on the action signal with risk management.
        This mirrors the logic from main.py but uses bot_manager's instances.
        """
        # Check if trading is allowed (daily limits)
        can_trade, reason = self.risk_manager.can_trade()
        if not can_trade:
            self._schedule_async(self._broadcast_log("WARNING", f"Trading disabled: {reason}"))
            return False

        self._schedule_async(self._broadcast_log("INFO", f"Sending {action} trade request..."))

        # Get latest prices
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            self._schedule_async(self._broadcast_log("ERROR", f"Could not get tick data for {symbol}"))
            return False

        price = tick.ask if action == "BUY" else tick.bid

        # Calculate SL/TP using Risk Manager
        sl, tp = self.risk_manager.calculate_sl_tp(symbol, action, price)

        # Calculate SL distance in pips for lot sizing
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            self._schedule_async(self._broadcast_log("ERROR", f"Could not get symbol info for {symbol}"))
            return False

        point = symbol_info.point
        sl_distance_pips = abs(price - sl) / (point * 10)  # Convert to pips

        # Calculate optimal lot size (if dynamic sizing enabled)
        if self.config.get("risk_management", {}).get("enable_dynamic_lot_sizing", False):
            volume = self.risk_manager.calculate_lot_size(symbol, sl_distance_pips)
            self._schedule_async(self._broadcast_log("INFO", f"Dynamic lot size: {volume} (Risk: {self.risk_manager.risk_percentage}%, SL: {sl_distance_pips:.1f} pips)"))
        else:
            volume = self.config.get("trading", {}).get("volume", 0.01)
            self._schedule_async(self._broadcast_log("INFO", f"Fixed lot size: {volume}"))

        # Validate trade
        is_valid, validation_reason = self.risk_manager.validate_trade(symbol, action, volume)
        if not is_valid:
            self._schedule_async(self._broadcast_log("WARNING", f"Trade validation failed: {validation_reason}"))
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
            "deviation": self.config.get("trading", {}).get("deviation", 20),
            "magic": 123456,
            "comment": f"Python MT5 Bot {action}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }

        # Execute order
        result = mt5.order_send(request)

        if result is None:
            self._schedule_async(self._broadcast_log("ERROR", "Order send failed - no result returned"))
            return False

        # Log and report result
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            self._schedule_async(self._broadcast_log("SUCCESS", f"{action} executed successfully! Ticket: {result.order}, Price: {result.price}"))

            # Get strategy name from manager
            strategy_name = self.strategy_manager.get_last_strategy_used() if hasattr(self.strategy_manager, 'get_last_strategy_used') else "Combined"

            # Log trade
            self.trade_logger.log_trade(
                action=action,
                symbol=symbol,
                volume=volume,
                price=result.price,
                sl=sl,
                tp=tp,
                ticket=result.order,
                strategy=strategy_name
            )

            # Update counters
            self.total_trades += 1

            # Broadcast trade execution
            self._schedule_async(ws_manager.broadcast_trade_execution(
                action=action,
                symbol=symbol,
                ticket=result.order,
                volume=volume,
                price=result.price,
                sl=sl,
                tp=tp,
                strategy=strategy_name,
                success=True,
                message_text=f"{action} executed successfully"
            ))

            return True
        else:
            error_msg = f"Order failed: {result.retcode} - {result.comment}"
            self._schedule_async(self._broadcast_log("ERROR", error_msg))

            # Broadcast failed trade
            self._schedule_async(ws_manager.broadcast_trade_execution(
                action=action,
                symbol=symbol,
                ticket=0,
                volume=volume,
                price=price,
                sl=sl,
                tp=tp,
                strategy="Combined",
                success=False,
                message_text=error_msg
            ))

            return False

    def _trading_iteration(self, symbol: str):
        """Perform one trading iteration."""
        # Get daily P/L status
        daily_pnl = self.risk_manager.get_daily_pnl()
        can_trade, reason = self.risk_manager.can_trade()

        # Broadcast status
        self._schedule_async(ws_manager.broadcast_bot_status(
            is_running=self.is_running,
            total_trades=self.total_trades,
            total_profit=self.total_profit,
            current_positions=len(self._get_open_positions()),
            daily_pnl=daily_pnl,
            can_trade=can_trade,
            reason=reason
        ))

        if not can_trade:
            self._schedule_async(self._broadcast_log("WARNING", f"Trading halted: {reason}"))
            return

        # Get strategy signal
        action = self.strategy_manager.generate_combined_signal(symbol)

        if action not in ["BUY", "SELL"]:
            return

        # Check if we can open new trade
        if not self._can_open_new_trade():
            self._schedule_async(self._broadcast_log("INFO", "Max concurrent trades reached"))
            return

        # Execute trade using actual MT5 order execution
        self._schedule_async(self._broadcast_log("INFO", f"Executing {action} trade for {symbol}"))
        success = self._execute_trade(symbol, action)

        if success:
            self._schedule_async(self._broadcast_log("SUCCESS", f"{action} trade executed successfully"))
        else:
            self._schedule_async(self._broadcast_log("ERROR", f"{action} trade execution failed"))
    
    def _bot_loop(self, symbol: str, interval: int):
        """Main bot loop running in separate thread."""
        print(f"[BotManager] Bot loop started for {symbol}")

        while not self._stop_flag:
            try:
                # Perform trading iteration
                self._trading_iteration(symbol)

                # Broadcast price update
                self._schedule_async(self._broadcast_price_update(symbol))

                # Sleep in small increments for responsive shutdown
                for _ in range(interval):
                    if self._stop_flag:
                        break
                    threading.Event().wait(1)

            except Exception as e:
                print(f"[BotManager] Error in bot loop: {e}")
                self._schedule_async(self._broadcast_log("ERROR", f"Bot error: {str(e)}"))

        print("[BotManager] Bot loop stopped")
    
    def start(self, symbol: Optional[str] = None, trade_interval: Optional[int] = None, event_loop: Optional[asyncio.AbstractEventLoop] = None) -> Dict[str, Any]:
        """
        Start the trading bot.

        Args:
            symbol: Trading symbol (uses config default if None)
            trade_interval: Trade interval in seconds (uses config default if None)
            event_loop: Event loop for async operations (required for WebSocket broadcasts)

        Returns:
            Dictionary with success status and message
        """
        if self.is_running:
            return {"success": False, "message": "Bot is already running"}

        # Store event loop reference for async operations
        self._event_loop = event_loop

        # Use config defaults if not provided
        symbol = symbol or self.config.get("symbol", "EURUSD")
        trade_interval = trade_interval or self.config.get("trade_interval_seconds", 60)

        # Initialize MT5
        if not self._initialize_mt5():
            return {"success": False, "message": "Failed to initialize MT5"}

        # Prepare symbol
        if not self._prepare_symbol(symbol):
            mt5.shutdown()
            return {"success": False, "message": f"Failed to prepare symbol {symbol}"}

        # Initialize components
        self.strategy_manager = self._initialize_strategies()
        self.risk_manager = RiskManager(self.config)
        self.trade_logger = TradeLogger()
        self.analytics = PerformanceAnalytics()

        # Start bot thread
        self._stop_flag = False
        self.is_running = True
        self.started_at = datetime.utcnow()

        self.bot_thread = threading.Thread(
            target=self._bot_loop,
            args=(symbol, trade_interval),
            daemon=True
        )
        self.bot_thread.start()

        print(f"[BotManager] Bot started - Symbol: {symbol}, Interval: {trade_interval}s")
        self._schedule_async(self._broadcast_log("INFO", f"Bot started - {symbol}"))

        return {
            "success": True,
            "message": f"Bot started successfully for {symbol}",
            "started_at": self.started_at
        }
    
    def stop(self) -> Dict[str, Any]:
        """
        Stop the trading bot.

        Returns:
            Dictionary with success status and message
        """
        if not self.is_running:
            return {"success": False, "message": "Bot is not running"}

        print("[BotManager] Stopping bot...")
        self._schedule_async(self._broadcast_log("INFO", "Stopping bot..."))

        # Set stop flag
        self._stop_flag = True
        self.is_running = False
        self.stopped_at = datetime.utcnow()

        # Wait for thread to finish
        if self.bot_thread and self.bot_thread.is_alive():
            self.bot_thread.join(timeout=10)

        # Shutdown MT5
        mt5.shutdown()

        print("[BotManager] Bot stopped")
        self._schedule_async(self._broadcast_log("INFO", "Bot stopped"))

        return {
            "success": True,
            "message": "Bot stopped successfully",
            "stopped_at": self.stopped_at,
            "total_trades": self.total_trades,
            "total_profit": self.total_profit
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current bot status.
        
        Returns:
            Dictionary with bot status information
        """
        uptime = None
        if self.is_running and self.started_at:
            uptime = int((datetime.utcnow() - self.started_at).total_seconds())
        
        # Get risk manager status if available
        daily_pnl = 0.0
        can_trade = True
        reason = "Bot not running"
        
        if self.risk_manager:
            daily_pnl = self.risk_manager.get_daily_pnl()
            can_trade, reason = self.risk_manager.can_trade()
        
        return {
            "is_running": self.is_running,
            "started_at": self.started_at,
            "uptime_seconds": uptime,
            "total_trades": self.total_trades,
            "total_profit": self.total_profit,
            "current_positions": len(self._get_open_positions()) if self.is_running else 0,
            "daily_pnl": daily_pnl,
            "can_trade": can_trade,
            "trade_status_reason": reason
        }


# Global bot manager instance
bot_manager = BotManager()

