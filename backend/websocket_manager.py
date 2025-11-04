"""
WebSocket connection manager for broadcasting real-time updates.
"""

from fastapi import WebSocket
from typing import List, Dict, Any
from datetime import datetime
import json
import asyncio


class ConnectionManager:
    """Manages WebSocket connections and broadcasts messages."""
    
    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket):
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection to register
        """
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        print(f"[WebSocket] Client connected. Total connections: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to remove
        """
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        print(f"[WebSocket] Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: Message dictionary to broadcast
        """
        if not self.active_connections:
            return
        
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
        
        # Convert to JSON
        json_message = json.dumps(message, default=str)
        
        # Send to all connections
        disconnected = []
        async with self._lock:
            for connection in self.active_connections:
                try:
                    await connection.send_text(json_message)
                except Exception as e:
                    print(f"[WebSocket] Error sending to client: {e}")
                    disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            await self.disconnect(connection)
    
    async def broadcast_price_update(self, symbol: str, bid: float, ask: float, 
                                     last: float, volume: int, time: datetime):
        """
        Broadcast price update to all clients.
        
        Args:
            symbol: Trading symbol
            bid: Bid price
            ask: Ask price
            last: Last price
            volume: Volume
            time: Update time
        """
        message = {
            "type": "price_update",
            "data": {
                "symbol": symbol,
                "bid": bid,
                "ask": ask,
                "last": last,
                "volume": volume,
                "time": time.isoformat()
            }
        }
        await self.broadcast(message)
    
    async def broadcast_trade_execution(self, action: str, symbol: str, ticket: int,
                                       volume: float, price: float, sl: float, tp: float,
                                       strategy: str, success: bool, message_text: str):
        """
        Broadcast trade execution to all clients.
        
        Args:
            action: Trade action (BUY/SELL)
            symbol: Trading symbol
            ticket: Trade ticket
            volume: Trade volume
            price: Execution price
            sl: Stop loss
            tp: Take profit
            strategy: Strategy name
            success: Whether trade was successful
            message_text: Execution message
        """
        message = {
            "type": "trade_execution",
            "data": {
                "action": action,
                "symbol": symbol,
                "ticket": ticket,
                "volume": volume,
                "price": price,
                "sl": sl,
                "tp": tp,
                "strategy": strategy,
                "success": success,
                "message": message_text,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        await self.broadcast(message)
    
    async def broadcast_log_event(self, level: str, message_text: str, source: str = None):
        """
        Broadcast log event to all clients.
        
        Args:
            level: Log level (INFO, WARNING, ERROR)
            message_text: Log message
            source: Source of the log
        """
        message = {
            "type": "log_event",
            "data": {
                "level": level,
                "message": message_text,
                "source": source,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        await self.broadcast(message)
    
    async def broadcast_bot_status(self, is_running: bool, total_trades: int,
                                   total_profit: float, current_positions: int,
                                   daily_pnl: float, can_trade: bool, reason: str):
        """
        Broadcast bot status update to all clients.
        
        Args:
            is_running: Whether bot is running
            total_trades: Total number of trades
            total_profit: Total profit
            current_positions: Number of open positions
            daily_pnl: Daily P&L
            can_trade: Whether trading is allowed
            reason: Status reason
        """
        message = {
            "type": "bot_status",
            "data": {
                "is_running": is_running,
                "total_trades": total_trades,
                "total_profit": total_profit,
                "current_positions": current_positions,
                "daily_pnl": daily_pnl,
                "can_trade": can_trade,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        await self.broadcast(message)
    
    def get_connection_count(self) -> int:
        """
        Get the number of active connections.
        
        Returns:
            Number of active connections
        """
        return len(self.active_connections)


# Global connection manager instance
manager = ConnectionManager()

