"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class BotStatusResponse(BaseModel):
    """Bot status response schema."""
    is_running: bool
    started_at: Optional[datetime] = None
    uptime_seconds: Optional[int] = None
    total_trades: int = 0
    total_profit: float = 0.0
    current_positions: int = 0
    daily_pnl: float = 0.0
    can_trade: bool = True
    trade_status_reason: str = ""


class BotStartRequest(BaseModel):
    """Bot start request schema."""
    symbol: Optional[str] = Field(None, description="Trading symbol (uses config default if not provided)")
    trade_interval: Optional[int] = Field(None, description="Trade interval in seconds")


class BotStartResponse(BaseModel):
    """Bot start response schema."""
    success: bool
    message: str
    started_at: Optional[datetime] = None


class BotStopResponse(BaseModel):
    """Bot stop response schema."""
    success: bool
    message: str
    stopped_at: Optional[datetime] = None
    total_trades: int = 0
    total_profit: float = 0.0


class AccountStatsResponse(BaseModel):
    """Account statistics response schema."""
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float
    profit: float
    currency: str
    leverage: int
    server: str
    company: str


class PositionResponse(BaseModel):
    """Position response schema."""
    ticket: int
    symbol: str
    type: str  # BUY or SELL
    volume: float
    price_open: float
    price_current: float
    sl: float
    tp: float
    profit: float
    swap: float
    commission: float
    time: datetime
    comment: str


class TradeHistoryResponse(BaseModel):
    """Trade history response schema."""
    id: int
    timestamp: datetime
    symbol: str
    action: str
    ticket: Optional[int]
    volume: float
    entry_price: float
    exit_price: Optional[float]
    sl: Optional[float]
    tp: Optional[float]
    profit: Optional[float]
    commission: Optional[float]
    swap: Optional[float]
    duration_seconds: Optional[int]
    status: str
    strategy: Optional[str]
    risk_reward_ratio: Optional[float]


class TradeHistoryListResponse(BaseModel):
    """Trade history list with pagination."""
    trades: List[TradeHistoryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class StrategyInfo(BaseModel):
    """Strategy information schema."""
    name: str
    enabled: bool
    weight: float
    params: Dict[str, Any]


class StrategyStatsResponse(BaseModel):
    """Strategy statistics response schema."""
    combination_method: str
    strategies: List[StrategyInfo]
    recent_signals: List[Dict[str, Any]]


class PriceUpdate(BaseModel):
    """Price update schema for WebSocket."""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: int
    time: datetime


class TradeExecution(BaseModel):
    """Trade execution schema for WebSocket."""
    action: str
    symbol: str
    ticket: Optional[int]
    volume: float
    price: float
    sl: float
    tp: float
    strategy: str
    timestamp: datetime
    success: bool
    message: str


class LogEvent(BaseModel):
    """Log event schema for WebSocket."""
    level: str  # INFO, WARNING, ERROR
    message: str
    timestamp: datetime
    source: Optional[str] = None


class WebSocketMessage(BaseModel):
    """Generic WebSocket message schema."""
    type: str  # price_update, trade_execution, log_event, bot_status
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

