"""
Database configuration and models for TraderBot backend.

Uses SQLAlchemy with async SQLite for storing trade history and bot state.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, Integer, DateTime, Text
from datetime import datetime
from typing import AsyncGenerator
import os

# Database URL
DATABASE_URL = "sqlite+aiosqlite:///./logs/traderbot.db"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class Trade(Base):
    """Trade model for storing trade history."""
    __tablename__ = "trades_api"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    action: Mapped[str] = mapped_column(String(10), nullable=False)  # BUY, SELL
    order_id: Mapped[int] = mapped_column(Integer, nullable=True)
    ticket: Mapped[int] = mapped_column(Integer, nullable=True)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    sl: Mapped[float] = mapped_column(Float, nullable=True)
    tp: Mapped[float] = mapped_column(Float, nullable=True)
    exit_price: Mapped[float] = mapped_column(Float, nullable=True)
    profit: Mapped[float] = mapped_column(Float, nullable=True)
    commission: Mapped[float] = mapped_column(Float, nullable=True, default=0.0)
    swap: Mapped[float] = mapped_column(Float, nullable=True, default=0.0)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN")  # OPEN, CLOSED, FAILED
    retcode: Mapped[int] = mapped_column(Integer, nullable=True)
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    strategy: Mapped[str] = mapped_column(String(50), nullable=True)
    risk_reward_ratio: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class BotState(Base):
    """Bot state model for storing current bot status."""
    __tablename__ = "bot_state"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    is_running: Mapped[bool] = mapped_column(Integer, nullable=False, default=0)  # SQLite uses 0/1 for bool
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    stopped_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    total_trades: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_profit: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session.
    
    Yields:
        AsyncSession: Database session
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[Database] Tables created successfully")


async def close_db():
    """Close database connections."""
    await engine.dispose()
    print("[Database] Connections closed")

