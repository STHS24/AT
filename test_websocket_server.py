"""
Test WebSocket Server for TraderBot Dashboard

This script creates a WebSocket server that sends mock trading data
to test the TraderDashboard application.

Usage:
    pip install websockets
    python test_websocket_server.py

Then run the dashboard:
    cd TraderDashboard
    dotnet run
"""

import asyncio
import json
import random
import websockets
from datetime import datetime

# Initial state
balance = 10000.0
equity = 10000.0
profit = 0.0
positions = []
status = "running"

# Sample symbols
SYMBOLS = ["BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "USDJPY"]

def generate_mock_data():
    """Generate mock trading data"""
    global balance, equity, profit, positions
    
    # Randomly update equity (simulate market movement)
    equity_change = random.uniform(-50, 100)
    equity += equity_change
    profit = equity - balance
    
    # Randomly add/remove positions
    if random.random() > 0.7 and len(positions) < 5:
        # Add new position
        new_position = {
            "symbol": random.choice(SYMBOLS),
            "side": random.choice(["long", "short"]),
            "profit": round(random.uniform(-20, 50), 2)
        }
        positions.append(new_position)
    elif random.random() > 0.8 and positions:
        # Close a position
        positions.pop(0)
    
    # Update existing positions
    for pos in positions:
        pos["profit"] += random.uniform(-5, 10)
        pos["profit"] = round(pos["profit"], 2)
    
    # Generate random actions
    actions = []
    if random.random() > 0.5:
        actions.append(f"Analyzing {random.choice(SYMBOLS)}")
    if random.random() > 0.7:
        actions.append(f"Placed {random.choice(['buy', 'sell'])} order on {random.choice(SYMBOLS)}")
    if random.random() > 0.6:
        actions.append("Waiting for next signal...")
    
    # Generate random logs
    logs = []
    log_templates = [
        "🧠 Thinking: Evaluating market conditions",
        "📊 Action: Signal detected on {}",
        "💤 Waiting 30s before next action",
        "✅ Trade executed successfully",
        "⚠️ Risk check: Position size validated",
        "📈 Market trend: {} detected",
        "🎯 Strategy: {} signal confirmed"
    ]
    
    for _ in range(random.randint(1, 3)):
        template = random.choice(log_templates)
        if "{}" in template:
            logs.append(template.format(random.choice(SYMBOLS + ["Bullish", "Bearish", "MA", "RSI", "MACD"])))
        else:
            logs.append(template)
    
    return {
        "status": status,
        "balance": round(balance, 2),
        "equity": round(equity, 2),
        "profit": round(profit, 2),
        "positions": positions.copy(),
        "actions": actions,
        "logs": logs
    }

async def handle_client(websocket):
    """Handle WebSocket client connection"""
    client_address = websocket.remote_address
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔌 Client connected: {client_address}")
    
    try:
        # Send initial data
        initial_data = generate_mock_data()
        await websocket.send(json.dumps(initial_data))
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📤 Sent initial data to {client_address}")
        
        # Create tasks for sending and receiving
        async def send_updates():
            """Send periodic updates to client"""
            while True:
                await asyncio.sleep(2)  # Send update every 2 seconds
                data = generate_mock_data()
                await websocket.send(json.dumps(data))
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 📤 Sent update to {client_address}")
        
        async def receive_commands():
            """Receive commands from client"""
            global status
            async for message in websocket:
                try:
                    command_data = json.loads(message)
                    command = command_data.get("command", "")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 📥 Received command: {command}")
                    
                    if command == "pause":
                        status = "paused"
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏸️  Bot paused")
                    elif command == "resume":
                        status = "running"
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] ▶️  Bot resumed")
                    elif command == "stop":
                        status = "stopped"
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏹️  Bot stopped")
                    
                    # Send immediate update with new status
                    data = generate_mock_data()
                    await websocket.send(json.dumps(data))
                    
                except json.JSONDecodeError:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Invalid JSON received")
        
        # Run both tasks concurrently
        await asyncio.gather(
            send_updates(),
            receive_commands()
        )
        
    except websockets.exceptions.ConnectionClosed:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔌 Client disconnected: {client_address}")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error: {e}")

async def main():
    """Start WebSocket server"""
    host = "localhost"
    port = 5000
    
    print("="*60)
    print("🚀 TraderBot Dashboard Test Server")
    print("="*60)
    print(f"📡 Starting WebSocket server on ws://{host}:{port}")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print("\n💡 Instructions:")
    print("   1. Keep this server running")
    print("   2. Open a new terminal")
    print("   3. Run: cd TraderDashboard && dotnet run")
    print("   4. The dashboard will connect automatically")
    print("\n⌨️  Press Ctrl+C to stop the server\n")
    print("="*60)
    
    async with websockets.serve(handle_client, host, port):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Server stopped by user")
        print("="*60)

