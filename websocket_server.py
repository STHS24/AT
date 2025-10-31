"""
WebSocket Server for TraderBot Dashboard
Broadcasts real-time bot status to connected clients
"""

import asyncio
import json
import websockets
from typing import Set
from datetime import datetime
import MetaTrader5 as mt5

# Connected clients
clients: Set = set()

# Global state for dashboard
RECENT_ACTIONS = []
RECENT_LOGS = []
MAX_DASHBOARD_ITEMS = 10

# Trading control flags (shared with main.py)
TRADING_PAUSED = False
SHUTDOWN_REQUESTED = False


async def broadcast_status(status_data: dict):
    """Broadcast status to all connected clients"""
    if clients:
        message = json.dumps(status_data)
        # Send to all clients, ignore errors for disconnected clients
        results = await asyncio.gather(
            *[client.send(message) for client in clients.copy()],
            return_exceptions=True
        )
        # Log any errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"[Dashboard] Error sending to client: {result}")


async def handle_client(websocket):
    """Handle new client connection"""
    clients.add(websocket)
    client_address = websocket.remote_address
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔌 Dashboard client connected: {client_address}")
    print(f"[Dashboard] Total clients: {len(clients)}")
    
    try:
        # Send initial status immediately
        from main import get_current_status
        initial_status = get_current_status()
        await websocket.send(json.dumps(initial_status))
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📤 Sent initial data to {client_address}")
        
        # Listen for commands from dashboard
        async for message in websocket:
            try:
                command_data = json.loads(message)
                command = command_data.get("command", "")
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 📥 Received command: {command}")

                global TRADING_PAUSED, SHUTDOWN_REQUESTED

                if command == "pause":
                    TRADING_PAUSED = True
                    add_dashboard_log("⏸️ Trading PAUSED by dashboard")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏸️  Trading PAUSED by dashboard")

                elif command == "resume":
                    TRADING_PAUSED = False
                    add_dashboard_log("▶️ Trading RESUMED by dashboard")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ▶️  Trading RESUMED by dashboard")

                elif command == "stop":
                    SHUTDOWN_REQUESTED = True
                    TRADING_PAUSED = True
                    add_dashboard_log("⏹️ Bot SHUTDOWN requested by dashboard")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏹️  Bot SHUTDOWN requested by dashboard")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🛑 Initiating graceful shutdown...")
                
                # Send immediate update with new status
                from main import get_current_status
                status = get_current_status()
                await websocket.send(json.dumps(status))
                
            except json.JSONDecodeError:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Invalid JSON received from dashboard")
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Error handling command: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔌 Dashboard client disconnected: {client_address}")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error in client handler: {e}")
    finally:
        clients.discard(websocket)
        print(f"[Dashboard] Total clients: {len(clients)}")


async def start_websocket_server():
    """Start WebSocket server"""
    try:
        server = await websockets.serve(handle_client, "localhost", 5000)
        print("="*80)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Dashboard WebSocket server started")
        print(f"[Dashboard] Listening on ws://localhost:5000")
        print(f"[Dashboard] Waiting for dashboard connections...")
        print("="*80)
        return server
    except OSError as e:
        if "address already in use" in str(e).lower():
            print("="*80)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Port 5000 already in use!")
            print("[Dashboard] Please stop any other WebSocket servers or test servers")
            print("[Dashboard] Or change the port in both websocket_server.py and MainWindow.axaml.cs")
            print("="*80)
        raise


def add_dashboard_action(action: str):
    """Add action to dashboard feed"""
    RECENT_ACTIONS.insert(0, action)
    if len(RECENT_ACTIONS) > MAX_DASHBOARD_ITEMS:
        RECENT_ACTIONS.pop()


def add_dashboard_log(log: str):
    """Add log to dashboard feed"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = f"[{timestamp}] {log}"
    RECENT_LOGS.insert(0, log_entry)
    if len(RECENT_LOGS) > MAX_DASHBOARD_ITEMS:
        RECENT_LOGS.pop()


async def broadcast_dashboard_update():
    """Send update to dashboard"""
    try:
        if clients:  # Only broadcast if there are connected clients
            from main import get_current_status
            status = get_current_status()
            await broadcast_status(status)
    except Exception as e:
        print(f"[Dashboard] Broadcast error: {e}")


def get_dashboard_status() -> str:
    """Get current dashboard status for display"""
    if TRADING_PAUSED:
        return "paused"
    return "running"


def is_trading_paused() -> bool:
    """Check if trading is paused by dashboard"""
    return TRADING_PAUSED


def is_shutdown_requested() -> bool:
    """Check if shutdown was requested by dashboard"""
    return SHUTDOWN_REQUESTED


def get_recent_actions() -> list:
    """Get recent actions for dashboard"""
    return RECENT_ACTIONS.copy()


def get_recent_logs() -> list:
    """Get recent logs for dashboard"""
    return RECENT_LOGS.copy()


def clear_dashboard_data():
    """Clear dashboard data (useful for testing)"""
    global RECENT_ACTIONS, RECENT_LOGS
    RECENT_ACTIONS.clear()
    RECENT_LOGS.clear()

