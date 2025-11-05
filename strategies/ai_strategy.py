"""
AI-Powered Trading Strategy using LLM.

Uses a Large Language Model to analyze market data and make trading decisions
based on comprehensive technical analysis, risk management, and market context.
"""

import json
from typing import Optional, Dict, Any
from datetime import datetime
from .base_strategy import BaseStrategy
from .llm_client import LLMClient
from .market_analyzer import MarketAnalyzer


class AIStrategy(BaseStrategy):
    """
    AI-powered trading strategy using LLM for decision making.
    
    Instead of using fixed technical indicator rules, this strategy:
    1. Collects comprehensive market data and context
    2. Sends it to an LLM for analysis
    3. Receives a trading decision with reasoning
    4. Filters decisions based on confidence threshold
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        Initialize AI Strategy.
        
        Args:
            params: Strategy parameters
                - api_key: OpenRouter API key (required)
                - model: LLM model to use (default: deepseek/deepseek-chat-v3.1:free)
                - confidence_threshold: Minimum confidence to trade (default: 0.7)
                - temperature: LLM temperature (default: 0.7)
                - timeout: API timeout in seconds (default: 30)
                - max_retries: Maximum API retry attempts (default: 3)
                - risk_manager: RiskManager instance (optional)
                - config: Full configuration dict (optional)
        """
        default_params = {
            "api_key": None,
            "model": "deepseek/deepseek-chat-v3.1:free",
            "confidence_threshold": 0.7,
            "temperature": 0.7,
            "timeout": 30,
            "max_retries": 3,
            "risk_manager": None,
            "config": {}
        }
        
        if params:
            default_params.update(params)
        
        super().__init__("AIStrategy", default_params)
        
        # Validate API key
        if not self.params.get("api_key"):
            raise ValueError("API key is required for AIStrategy")
        
        # Initialize LLM client
        self.llm_client = LLMClient(
            api_key=self.params["api_key"],
            model=self.params["model"],
            timeout=self.params["timeout"],
            max_retries=self.params["max_retries"]
        )
        
        # Initialize market analyzer
        self.market_analyzer = MarketAnalyzer(
            risk_manager=self.params.get("risk_manager")
        )
        
        # Decision history for logging and analysis
        self.decision_history = []
        
        print(f"[{self.name}] Initialized with model: {self.params['model']}")
        print(f"[{self.name}] Confidence threshold: {self.params['confidence_threshold']}")
    
    def generate_signal(self, symbol: str) -> str:
        """
        Generate trading signal using AI analysis.
        
        Args:
            symbol: Trading symbol (e.g., "EURUSD")
            
        Returns:
            str: "BUY", "SELL", or "NONE"
        """
        print(f"\n[{self.name}] 🤖 Analyzing market with AI...")
        
        # Collect market context
        try:
            market_context = self.market_analyzer.get_market_context(
                symbol, 
                self.params.get("config", {})
            )
        except Exception as e:
            print(f"[{self.name}] ❌ Error collecting market data: {e}")
            return "NONE"
        
        # Get AI decision
        try:
            decision_data = self.llm_client.get_trading_decision(
                market_context=market_context,
                temperature=self.params["temperature"]
            )
        except Exception as e:
            print(f"[{self.name}] ❌ Error getting AI decision: {e}")
            return "NONE"
        
        # Handle API failure
        if decision_data is None:
            print(f"[{self.name}] ❌ Failed to get AI decision (API error)")
            return "NONE"
        
        # Extract decision details
        decision = decision_data.get("decision", "NONE")
        reasoning = decision_data.get("reasoning", "No reasoning provided")
        confidence = decision_data.get("confidence", 0.0)
        key_factors = decision_data.get("key_factors", [])
        
        # Log decision
        self._log_decision(symbol, decision, reasoning, confidence, key_factors)
        
        # Apply confidence threshold
        confidence_threshold = self.params["confidence_threshold"]
        
        if decision in ["BUY", "SELL"]:
            if confidence < confidence_threshold:
                print(f"[{self.name}] ⚠️  AI suggested {decision} but confidence ({confidence:.2f}) below threshold ({confidence_threshold})")
                print(f"[{self.name}] 💭 Reasoning: {reasoning[:150]}...")
                return "NONE"
            else:
                print(f"[{self.name}] ✅ AI Decision: {decision} (Confidence: {confidence:.2f})")
                print(f"[{self.name}] 💭 Reasoning: {reasoning}")
                if key_factors:
                    print(f"[{self.name}] 🔑 Key Factors:")
                    for factor in key_factors:
                        print(f"[{self.name}]    - {factor}")
                return decision
        else:
            print(f"[{self.name}] ⏸️  AI Decision: NONE (Hold)")
            print(f"[{self.name}] 💭 Reasoning: {reasoning[:150]}...")
            return "NONE"
    
    def _log_decision(self, symbol: str, decision: str, reasoning: str, 
                     confidence: float, key_factors: list):
        """
        Log AI decision for analysis and debugging.
        
        Args:
            symbol: Trading symbol
            decision: Trading decision
            reasoning: AI reasoning
            confidence: Confidence score
            key_factors: Key factors in decision
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "decision": decision,
            "reasoning": reasoning,
            "confidence": confidence,
            "key_factors": key_factors,
            "model": self.params["model"]
        }
        
        self.decision_history.append(log_entry)
        
        # Keep only last 100 decisions in memory
        if len(self.decision_history) > 100:
            self.decision_history = self.decision_history[-100:]
        
        # Optionally save to file
        try:
            self._save_decision_to_file(log_entry)
        except Exception as e:
            print(f"[{self.name}] ⚠️  Could not save decision to file: {e}")
    
    def _save_decision_to_file(self, log_entry: Dict[str, Any]):
        """
        Save AI decision to log file.
        
        Args:
            log_entry: Decision log entry
        """
        import os
        
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_file = os.path.join(log_dir, "ai_decisions.jsonl")
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def get_decision_history(self, limit: int = 10) -> list:
        """
        Get recent decision history.
        
        Args:
            limit: Number of recent decisions to return
            
        Returns:
            List of recent decisions
        """
        return self.decision_history[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get AI strategy statistics.
        
        Returns:
            Dictionary with strategy statistics
        """
        # Count decisions
        total_decisions = len(self.decision_history)
        buy_count = sum(1 for d in self.decision_history if d["decision"] == "BUY")
        sell_count = sum(1 for d in self.decision_history if d["decision"] == "SELL")
        none_count = sum(1 for d in self.decision_history if d["decision"] == "NONE")
        
        # Average confidence
        confidences = [d["confidence"] for d in self.decision_history if d["decision"] in ["BUY", "SELL"]]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # LLM client stats
        llm_stats = self.llm_client.get_statistics()
        
        return {
            "strategy_name": self.name,
            "total_decisions": total_decisions,
            "buy_signals": buy_count,
            "sell_signals": sell_count,
            "hold_signals": none_count,
            "average_confidence": round(avg_confidence, 3),
            "confidence_threshold": self.params["confidence_threshold"],
            "llm_stats": llm_stats
        }
    
    def print_statistics(self):
        """Print strategy statistics to console."""
        stats = self.get_statistics()
        
        print(f"\n{'='*60}")
        print(f"📊 AI STRATEGY STATISTICS")
        print(f"{'='*60}")
        print(f"Model: {stats['llm_stats']['model']}")
        print(f"Total Decisions: {stats['total_decisions']}")
        print(f"  BUY Signals: {stats['buy_signals']}")
        print(f"  SELL Signals: {stats['sell_signals']}")
        print(f"  HOLD Signals: {stats['hold_signals']}")
        print(f"Average Confidence: {stats['average_confidence']:.2f}")
        print(f"Confidence Threshold: {stats['confidence_threshold']:.2f}")
        print(f"\nLLM API Stats:")
        print(f"  Total Requests: {stats['llm_stats']['total_requests']}")
        print(f"  Success Rate: {stats['llm_stats']['success_rate']}")
        print(f"  Total Tokens: {stats['llm_stats']['total_tokens_used']}")
        print(f"{'='*60}\n")
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get strategy information.
        
        Returns:
            dict: Strategy information including AI-specific details
        """
        base_info = super().get_info()
        base_info.update({
            "model": self.params["model"],
            "confidence_threshold": self.params["confidence_threshold"],
            "temperature": self.params["temperature"],
            "decisions_made": len(self.decision_history)
        })
        return base_info
    
    def __str__(self) -> str:
        """String representation of the strategy."""
        status = "enabled" if self.enabled else "disabled"
        return f"{self.name} (model: {self.params['model']}, confidence: {self.params['confidence_threshold']}, {status})"

