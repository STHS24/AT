"""
Market Analyzer for collecting and formatting market data.

Gathers comprehensive market information including price data, technical indicators,
positions, account status, and risk metrics for AI-powered trading decisions.
"""

import MetaTrader5 as mt5
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime


class MarketAnalyzer:
    """
    Collects and formats market data for AI analysis.
    
    Provides comprehensive market context including:
    - Current price and multi-timeframe data
    - Technical indicators (RSI, MACD, MA, ATR, Bollinger Bands)
    - Current positions and P/L
    - Account status and risk metrics
    """
    
    def __init__(self, risk_manager=None):
        """
        Initialize Market Analyzer.
        
        Args:
            risk_manager: Optional RiskManager instance for risk metrics
        """
        self.risk_manager = risk_manager
    
    def get_market_context(self, symbol: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get comprehensive market context for AI decision making.
        
        Args:
            symbol: Trading symbol (e.g., "EURUSD")
            config: Configuration dictionary with risk settings
            
        Returns:
            Dictionary containing all market data and context
        """
        context = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "current_price": self._get_current_price(symbol),
            "indicators": self._get_technical_indicators(symbol),
            "price_action": self._get_price_action(symbol),
            "positions": self._get_current_positions(symbol),
            "account": self._get_account_status(),
            "risk_constraints": self._get_risk_constraints(config)
        }
        
        return context
    
    def _get_current_price(self, symbol: str) -> Dict[str, Any]:
        """Get current price information."""
        tick = mt5.symbol_info_tick(symbol)
        
        if tick is None:
            return {"error": "Could not get tick data"}
        
        symbol_info = mt5.symbol_info(symbol)
        point = symbol_info.point if symbol_info else 0.00001
        
        spread_pips = (tick.ask - tick.bid) / (point * 10)
        
        return {
            "bid": round(tick.bid, 5),
            "ask": round(tick.ask, 5),
            "spread": round(spread_pips, 1),
            "time": datetime.fromtimestamp(tick.time).isoformat()
        }
    
    def _get_technical_indicators(self, symbol: str) -> Dict[str, Any]:
        """Calculate technical indicators."""
        indicators = {}
        
        # Get data for different timeframes
        m5_data = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 100)
        m15_data = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 100)
        
        if m5_data is not None and len(m5_data) >= 50:
            closes = m5_data['close']
            highs = m5_data['high']
            lows = m5_data['low']
            
            # RSI (14 period)
            rsi = self._calculate_rsi(closes, 14)
            if len(rsi) > 0:
                indicators["RSI_14"] = {
                    "value": round(rsi[-1], 2),
                    "status": self._get_rsi_status(rsi[-1])
                }
            
            # MACD (12, 26, 9)
            macd_line, signal_line, histogram = self._calculate_macd(closes, 12, 26, 9)
            if len(macd_line) > 1:
                indicators["MACD"] = {
                    "macd": round(macd_line[-1], 5),
                    "signal": round(signal_line[-1], 5),
                    "histogram": round(histogram[-1], 5),
                    "status": "Bullish" if histogram[-1] > 0 else "Bearish"
                }
            
            # Moving Averages
            ma_20 = np.mean(closes[-20:])
            ma_50 = np.mean(closes[-50:]) if len(closes) >= 50 else None
            current_price = closes[-1]
            
            indicators["MA_20"] = {
                "value": round(ma_20, 5),
                "position": "Above" if current_price > ma_20 else "Below"
            }
            
            if ma_50 is not None:
                indicators["MA_50"] = {
                    "value": round(ma_50, 5),
                    "position": "Above" if current_price > ma_50 else "Below"
                }
            
            # ATR (14 period) for volatility
            atr = self._calculate_atr(highs, lows, closes, 14)
            if atr is not None:
                symbol_info = mt5.symbol_info(symbol)
                point = symbol_info.point if symbol_info else 0.00001
                atr_pips = atr / (point * 10)
                
                indicators["ATR_14"] = {
                    "value": round(atr, 5),
                    "pips": round(atr_pips, 1),
                    "volatility": self._get_volatility_status(atr_pips)
                }
            
            # Bollinger Bands (20, 2)
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(closes, 20, 2)
            if bb_upper is not None:
                bb_position = self._get_bb_position(current_price, bb_upper, bb_middle, bb_lower)
                indicators["Bollinger_Bands"] = {
                    "upper": round(bb_upper, 5),
                    "middle": round(bb_middle, 5),
                    "lower": round(bb_lower, 5),
                    "position": bb_position
                }
        
        return indicators
    
    def _get_price_action(self, symbol: str) -> Dict[str, Any]:
        """Get price action across multiple timeframes."""
        price_action = {}
        
        timeframes = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "H1": mt5.TIMEFRAME_H1
        }
        
        for tf_name, tf_const in timeframes.items():
            rates = mt5.copy_rates_from_pos(symbol, tf_const, 0, 10)
            
            if rates is not None and len(rates) >= 3:
                current = rates[-1]
                prev = rates[-2]
                
                change = current['close'] - prev['close']
                change_pct = (change / prev['close']) * 100
                
                # Determine trend
                closes = rates['close']
                if closes[-1] > closes[-3]:
                    trend = "Uptrend"
                elif closes[-1] < closes[-3]:
                    trend = "Downtrend"
                else:
                    trend = "Sideways"
                
                price_action[tf_name] = {
                    "close": round(current['close'], 5),
                    "change": round(change, 5),
                    "change_pct": round(change_pct, 3),
                    "trend": trend,
                    "high": round(current['high'], 5),
                    "low": round(current['low'], 5)
                }
        
        return price_action
    
    def _get_current_positions(self, symbol: str) -> List[Dict[str, Any]]:
        """Get current open positions for the symbol."""
        positions = mt5.positions_get(symbol=symbol)
        
        if positions is None or len(positions) == 0:
            return []
        
        position_list = []
        symbol_info = mt5.symbol_info(symbol)
        point = symbol_info.point if symbol_info else 0.00001
        
        for pos in positions:
            pos_type = "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL"
            
            # Calculate pips
            if pos.type == mt5.ORDER_TYPE_BUY:
                pips = (pos.price_current - pos.price_open) / (point * 10)
            else:
                pips = (pos.price_open - pos.price_current) / (point * 10)
            
            position_list.append({
                "ticket": pos.ticket,
                "type": pos_type,
                "volume": pos.volume,
                "price": round(pos.price_open, 5),
                "current_price": round(pos.price_current, 5),
                "sl": round(pos.sl, 5) if pos.sl > 0 else None,
                "tp": round(pos.tp, 5) if pos.tp > 0 else None,
                "profit": round(pos.profit, 2),
                "pips": round(pips, 1)
            })
        
        return position_list
    
    def _get_account_status(self) -> Dict[str, Any]:
        """Get account information."""
        account_info = mt5.account_info()
        
        if account_info is None:
            return {"error": "Could not get account info"}
        
        # Get daily P/L if risk manager available
        daily_pnl = 0
        if self.risk_manager:
            daily_pnl = self.risk_manager.get_daily_pnl()
        
        return {
            "balance": round(account_info.balance, 2),
            "equity": round(account_info.equity, 2),
            "margin": round(account_info.margin, 2),
            "margin_free": round(account_info.margin_free, 2),
            "margin_level": round(account_info.margin_level, 2) if account_info.margin > 0 else 0,
            "daily_pnl": round(daily_pnl, 2)
        }
    
    def _get_risk_constraints(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get risk management constraints."""
        risk_config = config.get("risk_management", {})
        
        constraints = {
            "risk_percentage": risk_config.get("risk_percentage", 1.0),
            "daily_loss_limit": risk_config.get("daily_loss_limit", 500.0),
            "daily_profit_target": risk_config.get("daily_profit_target", 1000.0),
            "max_concurrent_trades": config.get("max_concurrent_trades", 3),
            "current_open_trades": len(mt5.positions_get() or [])
        }
        
        # Calculate remaining limits
        if self.risk_manager:
            daily_pnl = self.risk_manager.get_daily_pnl()
            constraints["daily_pnl"] = round(daily_pnl, 2)
            constraints["daily_loss_remaining"] = round(constraints["daily_loss_limit"] + daily_pnl, 2)
            constraints["daily_profit_remaining"] = round(constraints["daily_profit_target"] - daily_pnl, 2)
        
        return constraints
    
    # Technical indicator calculation methods
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate RSI indicator."""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gains = np.zeros(len(gains))
        avg_losses = np.zeros(len(losses))
        
        if len(gains) < period:
            return np.array([])
        
        avg_gains[period - 1] = np.mean(gains[:period])
        avg_losses[period - 1] = np.mean(losses[:period])
        
        for i in range(period, len(gains)):
            avg_gains[i] = (avg_gains[i - 1] * (period - 1) + gains[i]) / period
            avg_losses[i] = (avg_losses[i - 1] * (period - 1) + losses[i]) / period
        
        rsi = np.zeros(len(avg_gains))
        for i in range(period - 1, len(avg_gains)):
            if avg_losses[i] == 0:
                rsi[i] = 100
            else:
                rs = avg_gains[i] / avg_losses[i]
                rsi[i] = 100 - (100 / (1 + rs))
        
        return rsi[period - 1:]
    
    def _calculate_macd(self, prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9):
        """Calculate MACD indicator."""
        fast_ema = self._calculate_ema(prices, fast)
        slow_ema = self._calculate_ema(prices, slow)
        
        macd_line = fast_ema - slow_ema
        signal_line = self._calculate_ema(macd_line[slow - 1:], signal)
        
        # Pad signal line
        signal_padded = np.zeros_like(macd_line)
        signal_padded[slow - 1:] = signal_line
        
        histogram = macd_line - signal_padded
        
        return macd_line, signal_padded, histogram
    
    def _calculate_ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average."""
        ema = np.zeros_like(data, dtype=float)
        multiplier = 2 / (period + 1)
        
        ema[period - 1] = np.mean(data[:period])
        
        for i in range(period, len(data)):
            ema[i] = (data[i] - ema[i-1]) * multiplier + ema[i-1]
        
        return ema
    
    def _calculate_atr(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> Optional[float]:
        """Calculate Average True Range."""
        if len(highs) < period + 1:
            return None
        
        tr = np.maximum(
            highs[1:] - lows[1:],
            np.maximum(
                np.abs(highs[1:] - closes[:-1]),
                np.abs(lows[1:] - closes[:-1])
            )
        )
        
        return np.mean(tr[-period:])
    
    def _calculate_bollinger_bands(self, prices: np.ndarray, period: int = 20, std_dev: float = 2.0):
        """Calculate Bollinger Bands."""
        if len(prices) < period:
            return None, None, None
        
        middle = np.mean(prices[-period:])
        std = np.std(prices[-period:])
        
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        
        return upper, middle, lower
    
    # Helper methods for status interpretation
    
    def _get_rsi_status(self, rsi: float) -> str:
        """Get RSI status description."""
        if rsi >= 70:
            return "Overbought"
        elif rsi <= 30:
            return "Oversold"
        else:
            return "Neutral"
    
    def _get_volatility_status(self, atr_pips: float) -> str:
        """Get volatility status description."""
        if atr_pips > 20:
            return "High"
        elif atr_pips > 10:
            return "Medium"
        else:
            return "Low"
    
    def _get_bb_position(self, price: float, upper: float, middle: float, lower: float) -> str:
        """Get Bollinger Band position description."""
        if price >= upper:
            return "Above upper band (overbought)"
        elif price <= lower:
            return "Below lower band (oversold)"
        elif price > middle:
            return "Above middle (bullish zone)"
        else:
            return "Below middle (bearish zone)"

