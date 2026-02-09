"""
AI Mode Manager

Manages AI-powered trading mode that uses LLM to analyze market data
and make trading decisions. Uses strategies from strategies folder for analysis.
"""

import json
from typing import Optional, Dict, Any
from datetime import datetime
from .llm_client import LLMClient
from .market_analyzer import MarketAnalyzer


class AIMode:
    """
    AI Mode Manager for AI-powered trading.
    
    Uses LLM to analyze market data and make trading decisions.
    Collects data using strategies from the strategies folder.
    """
    
    def __init__(self, config: Dict[str, Any], risk_manager=None):
        """
        Initialize AI Mode.
        
        Args:
            config: AI mode configuration
            risk_manager: RiskManager instance
        """
        self.config = config
        self.risk_manager = risk_manager
        self.enabled = config.get("enabled", False)
        
        if not self.enabled:
            return
        
        # Get AI config
        ai_config = config.get("params", {})
        
        # Validate API key
        api_key = ai_config.get("api_key")
        if not api_key:
            raise ValueError("API key is required for AI mode")
        
        # Initialize LLM client
        self.llm_client = LLMClient(
            api_key=api_key,
            model=ai_config.get("model", "deepseek-reasoner"),
            timeout=ai_config.get("timeout", 30),
            max_retries=ai_config.get("max_retries", 3),
            base_url=ai_config.get("base_url", "https://api.deepseek.com/chat/completions"),
            thinking=ai_config.get("thinking", False),
            debug=ai_config.get("debug", False),
        )
        
        # Initialize market analyzer
        self.market_analyzer = MarketAnalyzer(risk_manager=risk_manager)
        
        # AI mode settings
        self.confidence_threshold = ai_config.get("confidence_threshold", 0.7)
        self.temperature = ai_config.get("temperature", 0.7)
        self.enable_position_management = ai_config.get("enable_position_management", True)
        self.min_hold_time_minutes = ai_config.get("min_hold_time_minutes", 5)
        
        # Track last decision for urgency
        self.last_decision_urgent = False
        
        print(f"[AIMode] ✅ AI Mode initialized")
        print(f"[AIMode]    Model: {ai_config.get('model')}")
        print(f"[AIMode]    Confidence threshold: {self.confidence_threshold}")
        print(f"[AIMode]    Position management: {self.enable_position_management}")
    
    def get_trading_signal(self, symbol: str, full_config: Dict[str, Any]) -> str:
        """
        Get trading signal from AI analysis.
        
        Args:
            symbol: Trading symbol
            full_config: Full bot configuration
            
        Returns:
            str: "BUY", "SELL", or "NONE"
        """
        if not self.enabled:
            return "NONE"
        
        print(f"\n[AIMode] 🤖 Analyzing market with AI...")
        
        # Collect market context
        try:
            market_context = self.market_analyzer.get_market_context(symbol, full_config)
        except Exception as e:
            print(f"[AIMode] ❌ Error collecting market data: {e}")
            return "NONE"
        
        # Get AI decision
        try:
            decision_data = self.llm_client.get_trading_decision(
                market_context=market_context,
                temperature=self.temperature
            )
        except Exception as e:
            print(f"[AIMode] ❌ Error getting AI decision: {e}")
            return "NONE"
        
        if not decision_data:
            print(f"[AIMode] ❌ Failed to get AI decision (API error)")
            return "NONE"
        
        # Extract decision details
        decision = decision_data.get("decision", "NONE")
        confidence = decision_data.get("confidence", 0.0)
        reasoning = decision_data.get("reasoning", "No reasoning provided")
        urgent = decision_data.get("urgent", False)
        
        # Store urgency flag
        self.last_decision_urgent = urgent
        
        # Log decision
        print(f"[AIMode] 💡 AI Decision: {decision}")
        print(f"[AIMode]    Confidence: {confidence:.2f}")
        print(f"[AIMode]    Urgent: {urgent}")
        print(f"[AIMode]    Reasoning: {reasoning}")
        
        # Filter by confidence threshold
        if decision in ["BUY", "SELL"] and confidence < self.confidence_threshold:
            print(f"[AIMode] ⚠️  Confidence {confidence:.2f} below threshold {self.confidence_threshold:.2f}, ignoring signal")
            return "NONE"
        
        return decision
    
    def manage_position(self, position, symbol: str, full_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze open position and decide whether to hold, close, or partially close.
        
        Args:
            position: MT5 position object
            symbol: Trading symbol
            full_config: Full bot configuration
            
        Returns:
            Dict with action, reasoning, confidence, and optional partial_percentage
        """
        if not self.enabled or not self.enable_position_management:
            return None
        
        # Get position analysis context
        try:
            position_context = self.market_analyzer.get_position_analysis_context(
                position, symbol, full_config
            )
        except Exception as e:
            print(f"[AIMode] ❌ Error collecting position data: {e}")
            return None
        
        # Check minimum hold time
        duration_minutes = position_context.get("position", {}).get("duration_minutes", 0)
        if duration_minutes < self.min_hold_time_minutes:
            return {"action": "HOLD", "reasoning": f"Position held for only {duration_minutes} minutes (min: {self.min_hold_time_minutes})", "confidence": 1.0}
        
        # Get AI position management decision
        try:
            decision_data = self.llm_client.get_position_management_decision(
                market_context=position_context,
                temperature=self.temperature
            )
        except Exception as e:
            print(f"[AIMode] ❌ Error getting position management decision: {e}")
            return None
        
        return decision_data
    
    def is_last_decision_urgent(self) -> bool:
        """Check if the last decision was marked as urgent."""
        return self.last_decision_urgent
    
    def get_stats(self) -> Dict[str, Any]:
        """Get AI mode statistics."""
        if not self.enabled:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "total_requests": self.llm_client.total_requests,
            "successful_requests": self.llm_client.successful_requests,
            "failed_requests": self.llm_client.failed_requests,
            "success_rate": (self.llm_client.successful_requests / self.llm_client.total_requests * 100) if self.llm_client.total_requests > 0 else 0
        }
