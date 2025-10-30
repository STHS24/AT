# Dashboard Integration Guide

This guide explains how to integrate the TraderBot Dashboard with your actual trading bot.

## Overview

The dashboard connects via WebSocket to `ws://localhost:5000` and expects JSON messages with bot status updates.

---

## Step 1: Install WebSocket Library

Add the `websockets` library to your Python environment:

```bash
pip install websockets
```

---

## Step 2: Create WebSocket Server Module

Create a new file `websocket_server.py` in your TraderBot directory:

```python
"""
WebSocket Server for TraderBot Dashboard
Broadcasts real-time bot status to connected clients
"""

import asyncio
import json
import websockets
from typing import Set
import MetaTrader5 as mt5

# Connected clients
clients: Set = set()

async def broadcast_status(status_data: dict):
    """Broadcast status to all connected clients"""
    if clients:
        message = json.dumps(status_data)
        await asyncio.gather(
            *[client.send(message) for client in clients],
            return_exceptions=True
        )

async def handle_client(websocket, path):
    """Handle new client connection"""
    clients.add(websocket)
    print(f"[Dashboard] Client connected. Total clients: {len(clients)}")
    
    try:
        async for message in websocket:
            # Handle commands from dashboard
            try:
                command_data = json.loads(message)
                command = command_data.get("command", "")
                
                if command == "pause":
                    # Set global flag to pause trading
                    global TRADING_ENABLED
                    TRADING_ENABLED = False
                    print("[Dashboard] Trading PAUSED by dashboard")
                    
                elif command == "resume":
                    TRADING_ENABLED = True
                    print("[Dashboard] Trading RESUMED by dashboard")
                    
                elif command == "stop":
                    TRADING_ENABLED = False
                    print("[Dashboard] Trading STOPPED by dashboard")
                    
            except json.JSONDecodeError:
                print("[Dashboard] Invalid command received")
                
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        clients.remove(websocket)
        print(f"[Dashboard] Client disconnected. Total clients: {len(clients)}")

async def start_websocket_server():
    """Start WebSocket server"""
    server = await websockets.serve(handle_client, "localhost", 5000)
    print("[Dashboard] WebSocket server started on ws://localhost:5000")
    return server

def get_current_status() -> dict:
    """Get current bot status for dashboard"""
    account_info = mt5.account_info()
    
    if account_info is None:
        return {
            "status": "error",
            "balance": 0.0,
            "equity": 0.0,
            "profit": 0.0,
            "positions": [],
            "actions": [],
            "logs": ["⚠️ MT5 connection error"]
        }
    
    # Get open positions
    positions = mt5.positions_get()
    position_list = []
    
    if positions:
        for pos in positions:
            position_list.append({
                "symbol": pos.symbol,
                "side": "long" if pos.type == mt5.ORDER_TYPE_BUY else "short",
                "profit": round(pos.profit, 2)
            })
    
    # Determine status
    status = "running" if TRADING_ENABLED else "paused"
    
    return {
        "status": status,
        "balance": round(account_info.balance, 2),
        "equity": round(account_info.equity, 2),
        "profit": round(account_info.profit, 2),
        "positions": position_list,
        "actions": RECENT_ACTIONS.copy(),
        "logs": RECENT_LOGS.copy()
    }
```

---

## Step 3: Modify main.py

Add the following changes to your `main.py`:

### **3.1: Add Imports**

```python
import asyncio
import websockets
from websocket_server import start_websocket_server, broadcast_status, get_current_status
```

### **3.2: Add Global Variables**

```python
# Dashboard integration
RECENT_ACTIONS = []
RECENT_LOGS = []
MAX_DASHBOARD_ITEMS = 10
```

### **3.3: Add Helper Functions**

```python
def add_dashboard_action(action: str):
    """Add action to dashboard feed"""
    RECENT_ACTIONS.insert(0, action)
    if len(RECENT_ACTIONS) > MAX_DASHBOARD_ITEMS:
        RECENT_ACTIONS.pop()

def add_dashboard_log(log: str):
    """Add log to dashboard feed"""
    RECENT_LOGS.insert(0, log)
    if len(RECENT_LOGS) > MAX_DASHBOARD_ITEMS:
        RECENT_LOGS.pop()

async def broadcast_dashboard_update():
    """Send update to dashboard"""
    try:
        status = get_current_status()
        await broadcast_status(status)
    except Exception as e:
        print(f"[Dashboard] Broadcast error: {e}")
```

### **3.4: Modify Main Loop**

```python
async def trading_loop():
    """Main trading loop with dashboard updates"""
    iteration_count = 0
    
    while TRADING_ENABLED:
        try:
            iteration_count += 1
            print(f"\n{'='*80}")
            print(f"🔄 Iteration {iteration_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Check daily limits
            if not RISK_MANAGER.can_trade_today():
                add_dashboard_log("⚠️ Daily limit reached - trading disabled")
                await broadcast_dashboard_update()
                break
            
            # Get market data
            add_dashboard_log(f"📊 Analyzing {SYMBOL}")
            rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 500)
            
            if rates is None or len(rates) == 0:
                add_dashboard_log("⚠️ Failed to get market data")
                await broadcast_dashboard_update()
                await asyncio.sleep(TRADING_INTERVAL)
                continue
            
            # Get trading signal
            add_dashboard_action(f"Analyzing {SYMBOL}")
            signal = STRATEGY_MANAGER.get_combined_signal(rates)
            
            if signal != 0:
                add_dashboard_log(f"🎯 Signal detected: {'BUY' if signal > 0 else 'SELL'}")
                add_dashboard_action(f"Signal: {'BUY' if signal > 0 else 'SELL'} {SYMBOL}")
                
                # Execute trade
                result = execute_trade(signal)
                if result:
                    add_dashboard_log(f"✅ Trade executed successfully")
                else:
                    add_dashboard_log(f"⚠️ Trade execution failed")
            else:
                add_dashboard_log("💤 No signal - waiting")
                add_dashboard_action("Waiting for signal...")
            
            # Broadcast update to dashboard
            await broadcast_dashboard_update()
            
            # Wait for next iteration
            await asyncio.sleep(TRADING_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n⚠️  Keyboard interrupt detected...")
            break
        except Exception as e:
            add_dashboard_log(f"❌ Error: {str(e)}")
            await broadcast_dashboard_update()
            await asyncio.sleep(TRADING_INTERVAL)

async def main_async():
    """Async main function"""
    # Start WebSocket server
    websocket_server = await start_websocket_server()
    
    # Start trading loop
    await trading_loop()
    
    # Cleanup
    websocket_server.close()
    await websocket_server.wait_closed()

if __name__ == "__main__":
    try:
        # Initialize MT5
        if not mt5.initialize():
            print("❌ MT5 initialization failed")
            exit(1)
        
        # Run async main
        asyncio.run(main_async())
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    finally:
        mt5.shutdown()
        print("✅ Shutdown complete")
```

---

## Step 4: Test the Integration

### **Terminal 1: Start the Trading Bot**
```bash
python main.py
```

You should see:
```
[Dashboard] WebSocket server started on ws://localhost:5000
🔄 Iteration 1 - 2025-10-30 12:00:00
...
```

### **Terminal 2: Start the Dashboard**
```bash
cd TraderDashboard
dotnet run
```

The dashboard should connect automatically and display real-time data!

---

## Step 5: Verify Integration

Check that the following work:

- ✅ Dashboard shows current balance and equity
- ✅ Open positions appear in the table
- ✅ Equity chart updates in real-time
- ✅ Activity logs show bot actions
- ✅ START/PAUSE/STOP buttons control the bot
- ✅ Dashboard reconnects if bot restarts

---

## Troubleshooting

### Dashboard shows "Disconnected"
- Check that the bot is running
- Verify WebSocket server started (look for "[Dashboard] WebSocket server started")
- Check firewall settings

### No data updates
- Verify `broadcast_dashboard_update()` is called in the main loop
- Check for errors in bot console
- Ensure `get_current_status()` returns valid data

### Commands not working
- Verify `handle_client()` is processing commands
- Check that `TRADING_ENABLED` flag is being used
- Look for "[Dashboard] Trading PAUSED/RESUMED" messages

---

## Advanced: Custom Actions and Logs

You can add custom dashboard updates anywhere in your code:

```python
# Add action
add_dashboard_action("Checking risk limits")

# Add log
add_dashboard_log("🧠 Thinking: Evaluating market conditions")

# Broadcast immediately
await broadcast_dashboard_update()
```

---

## Performance Considerations

- Dashboard updates are sent every trading iteration
- WebSocket broadcasts are non-blocking
- Multiple dashboards can connect simultaneously
- Minimal performance impact on trading bot

---

## Security Notes

⚠️ **Important**: The current implementation uses `localhost` only.

For remote access:
1. Change `"localhost"` to `"0.0.0.0"` in `start_websocket_server()`
2. Add authentication (WebSocket headers, tokens)
3. Use WSS (WebSocket Secure) with SSL certificates
4. Implement rate limiting
5. Add IP whitelisting

---

## Next Steps

1. ✅ Test with mock server (`test_websocket_server.py`)
2. ✅ Integrate WebSocket server into `main.py`
3. ✅ Test with live bot
4. ✅ Customize actions and logs
5. ✅ Deploy and monitor!

---

## Summary

The dashboard integration requires:
1. WebSocket server in your bot (`websocket_server.py`)
2. Status broadcasting function
3. Command handling for START/PAUSE/STOP
4. Action and log tracking

Once integrated, you'll have a professional real-time monitoring dashboard for your trading bot! 🚀

