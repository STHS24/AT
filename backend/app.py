"""
FastAPI Application for TraderBot

Provides REST API and WebSocket endpoints for controlling and monitoring the trading bot.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta
from typing import List, Optional
import MetaTrader5 as mt5

from backend.database import init_db, close_db, get_db, Trade
from backend.schemas import (
    BotStatusResponse, BotStartRequest, BotStartResponse, BotStopResponse,
    AccountStatsResponse, PositionResponse, TradeHistoryResponse,
    TradeHistoryListResponse, StrategyInfo, StrategyStatsResponse
)
from backend.websocket_manager import manager as ws_manager
from backend.bot_manager import bot_manager

# Create FastAPI app
app = FastAPI(
    title="TraderBot API",
    description="REST API and WebSocket interface for MetaTrader 5 trading bot",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    await init_db()
    print("[API] FastAPI application started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    # Stop bot if running
    if bot_manager.is_running:
        bot_manager.stop()
    
    await close_db()
    print("[API] FastAPI application stopped")


# ============================================
# Bot Control Endpoints
# ============================================

@app.post("/bot/start", response_model=BotStartResponse, tags=["Bot Control"])
async def start_bot(request: BotStartRequest):
    """
    Start the trading bot.
    
    - **symbol**: Trading symbol (optional, uses config default)
    - **trade_interval**: Trade interval in seconds (optional, uses config default)
    """
    result = bot_manager.start(
        symbol=request.symbol,
        trade_interval=request.trade_interval
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return BotStartResponse(
        success=result["success"],
        message=result["message"],
        started_at=result.get("started_at")
    )


@app.post("/bot/stop", response_model=BotStopResponse, tags=["Bot Control"])
async def stop_bot():
    """Stop the trading bot."""
    result = bot_manager.stop()
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return BotStopResponse(
        success=result["success"],
        message=result["message"],
        stopped_at=result.get("stopped_at"),
        total_trades=result.get("total_trades", 0),
        total_profit=result.get("total_profit", 0.0)
    )


@app.get("/bot/status", response_model=BotStatusResponse, tags=["Bot Control"])
async def get_bot_status():
    """Get current bot status."""
    status = bot_manager.get_status()
    return BotStatusResponse(**status)


# ============================================
# Account & Statistics Endpoints
# ============================================

@app.get("/stats/account", response_model=AccountStatsResponse, tags=["Statistics"])
async def get_account_stats():
    """Get MT5 account statistics."""
    account_info = mt5.account_info()
    
    if account_info is None:
        raise HTTPException(status_code=503, detail="MT5 not connected or account info unavailable")
    
    return AccountStatsResponse(
        balance=account_info.balance,
        equity=account_info.equity,
        margin=account_info.margin,
        free_margin=account_info.margin_free,
        margin_level=account_info.margin_level if account_info.margin > 0 else 0,
        profit=account_info.profit,
        currency=account_info.currency,
        leverage=account_info.leverage,
        server=account_info.server,
        company=account_info.company
    )


@app.get("/stats/positions", response_model=List[PositionResponse], tags=["Statistics"])
async def get_positions():
    """Get current open positions."""
    positions = mt5.positions_get()
    
    if positions is None:
        return []
    
    result = []
    for pos in positions:
        result.append(PositionResponse(
            ticket=pos.ticket,
            symbol=pos.symbol,
            type="BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL",
            volume=pos.volume,
            price_open=pos.price_open,
            price_current=pos.price_current,
            sl=pos.sl,
            tp=pos.tp,
            profit=pos.profit,
            swap=pos.swap,
            commission=pos.commission,
            time=datetime.fromtimestamp(pos.time),
            comment=pos.comment
        ))
    
    return result


@app.get("/stats/strategies", response_model=StrategyStatsResponse, tags=["Statistics"])
async def get_strategy_stats():
    """Get strategy configuration and recent signals."""
    if not bot_manager.strategy_manager:
        raise HTTPException(status_code=400, detail="Bot not running, strategy manager not initialized")
    
    strategies = []
    for strategy in bot_manager.strategy_manager.strategies:
        info = strategy.get_info()
        strategies.append(StrategyInfo(**info))
    
    # Get recent signals from history
    recent_signals = bot_manager.strategy_manager.signal_history[-10:] if hasattr(bot_manager.strategy_manager, 'signal_history') else []
    
    return StrategyStatsResponse(
        combination_method=bot_manager.strategy_manager.method,
        strategies=strategies,
        recent_signals=recent_signals
    )


# ============================================
# Trade History Endpoints
# ============================================

@app.get("/history/trades", response_model=TradeHistoryListResponse, tags=["History"])
async def get_trade_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status (OPEN, CLOSED, FAILED)"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get trade history with pagination and filters.
    
    - **page**: Page number (starts at 1)
    - **page_size**: Number of items per page (max 200)
    - **status**: Filter by trade status
    - **symbol**: Filter by trading symbol
    """
    # Build query
    query = select(Trade)
    
    if status:
        query = query.where(Trade.status == status)
    if symbol:
        query = query.where(Trade.symbol == symbol)
    
    # Get total count
    count_query = select(func.count()).select_from(Trade)
    if status:
        count_query = count_query.where(Trade.status == status)
    if symbol:
        count_query = count_query.where(Trade.symbol == symbol)
    
    result = await db.execute(count_query)
    total = result.scalar()
    
    # Get paginated results
    query = query.order_by(desc(Trade.timestamp)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    trades = result.scalars().all()
    
    # Convert to response models
    trade_responses = [
        TradeHistoryResponse(
            id=trade.id,
            timestamp=trade.timestamp,
            symbol=trade.symbol,
            action=trade.action,
            ticket=trade.ticket,
            volume=trade.volume,
            entry_price=trade.entry_price,
            exit_price=trade.exit_price,
            sl=trade.sl,
            tp=trade.tp,
            profit=trade.profit,
            commission=trade.commission,
            swap=trade.swap,
            duration_seconds=trade.duration_seconds,
            status=trade.status,
            strategy=trade.strategy,
            risk_reward_ratio=trade.risk_reward_ratio
        )
        for trade in trades
    ]
    
    total_pages = (total + page_size - 1) // page_size
    
    return TradeHistoryListResponse(
        trades=trade_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


# ============================================
# WebSocket Endpoint
# ============================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.
    
    Broadcasts:
    - Price updates
    - Trade executions
    - Log events
    - Bot status changes
    """
    await ws_manager.connect(websocket)
    
    try:
        # Send initial status
        status = bot_manager.get_status()
        await websocket.send_json({
            "type": "bot_status",
            "data": status,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep connection alive and listen for client messages
        while True:
            # Wait for messages from client (ping/pong, etc.)
            data = await websocket.receive_text()
            
            # Echo back for ping/pong
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"[WebSocket] Error: {e}")
        await ws_manager.disconnect(websocket)


# ============================================
# Health Check
# ============================================

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "bot_running": bot_manager.is_running,
        "websocket_connections": ws_manager.get_connection_count()
    }


@app.get("/", tags=["System"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "TraderBot API",
        "version": "1.0.0",
        "docs": "/docs",
        "websocket": "/ws",
        "status": "operational"
    }

