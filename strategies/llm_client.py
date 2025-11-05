"""
LLM Client for OpenRouter API integration.

Handles communication with the OpenRouter API for AI-powered trading decisions.
Includes error handling, retry logic, and response parsing.
"""

import requests
import json
import time
from typing import Dict, Optional, Any
from datetime import datetime


class LLMClient:
    """
    Client for interacting with OpenRouter API.
    
    Provides methods to send trading context to LLM and receive decisions.
    """
    
    def __init__(self, api_key: str, model: str = "deepseek/deepseek-chat-v3.1:free", 
                 timeout: int = 30, max_retries: int = 3):
        """
        Initialize LLM Client.
        
        Args:
            api_key: OpenRouter API key
            model: Model identifier (default: deepseek-chat-v3.1:free)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Request headers
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/STHS24/AT",
            "X-Title": "TraderBot AI Strategy"
        }
        
        # Statistics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_tokens_used = 0
        
    def get_trading_decision(self, market_context: Dict[str, Any], 
                            system_prompt: Optional[str] = None,
                            temperature: float = 0.7) -> Optional[Dict[str, Any]]:
        """
        Get trading decision from LLM based on market context.
        
        Args:
            market_context: Dictionary containing market data and trading context
            system_prompt: Optional custom system prompt
            temperature: LLM temperature (0.0-1.0, higher = more creative)
            
        Returns:
            Dictionary with decision, reasoning, and confidence, or None if failed
        """
        # Build system prompt
        if system_prompt is None:
            system_prompt = self._build_default_system_prompt()
        
        # Build user prompt from market context
        user_prompt = self._build_user_prompt(market_context)
        
        # Prepare request payload
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": 1000
        }
        
        # Make API call with retry logic
        response_data = self._make_request_with_retry(payload)
        
        if response_data is None:
            return None
        
        # Parse and validate response
        return self._parse_trading_response(response_data)
    
    def _build_default_system_prompt(self) -> str:
        """Build default system prompt for trading AI."""
        return """You are an expert forex trading AI assistant with deep knowledge of technical analysis, risk management, and market psychology.

Your role is to analyze market data and provide trading decisions (BUY, SELL, or NONE) based on:
- Technical indicators (RSI, MACD, Moving Averages, ATR, Bollinger Bands)
- Price action and trends across multiple timeframes
- Current positions and risk exposure
- Market volatility and conditions

You must respond in valid JSON format with the following structure:
{
    "decision": "BUY" | "SELL" | "NONE",
    "reasoning": "Detailed explanation of your analysis and decision",
    "confidence": 0.0-1.0,
    "key_factors": ["factor1", "factor2", "factor3"]
}

Guidelines:
- Only recommend BUY/SELL when you have strong conviction (confidence > 0.7)
- Consider risk management and current exposure
- Explain your reasoning clearly
- Be conservative - it's better to wait than force a trade
- Consider multiple timeframes for confirmation
"""
    
    def _build_user_prompt(self, market_context: Dict[str, Any]) -> str:
        """
        Build user prompt from market context.
        
        Args:
            market_context: Market data and trading context
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        
        # Symbol and current price
        if "symbol" in market_context:
            prompt_parts.append(f"SYMBOL: {market_context['symbol']}")
        
        if "current_price" in market_context:
            price_data = market_context["current_price"]
            prompt_parts.append(f"\nCURRENT PRICE:")
            prompt_parts.append(f"  Bid: {price_data.get('bid', 'N/A')}")
            prompt_parts.append(f"  Ask: {price_data.get('ask', 'N/A')}")
            prompt_parts.append(f"  Spread: {price_data.get('spread', 'N/A')} pips")
        
        # Technical indicators
        if "indicators" in market_context:
            indicators = market_context["indicators"]
            prompt_parts.append(f"\nTECHNICAL INDICATORS:")
            
            for indicator_name, indicator_data in indicators.items():
                if isinstance(indicator_data, dict):
                    prompt_parts.append(f"  {indicator_name}:")
                    for key, value in indicator_data.items():
                        prompt_parts.append(f"    {key}: {value}")
                else:
                    prompt_parts.append(f"  {indicator_name}: {indicator_data}")
        
        # Price action
        if "price_action" in market_context:
            price_action = market_context["price_action"]
            prompt_parts.append(f"\nPRICE ACTION:")
            for timeframe, data in price_action.items():
                prompt_parts.append(f"  {timeframe}:")
                for key, value in data.items():
                    prompt_parts.append(f"    {key}: {value}")
        
        # Current positions
        if "positions" in market_context:
            positions = market_context["positions"]
            prompt_parts.append(f"\nCURRENT POSITIONS:")
            if positions:
                for pos in positions:
                    prompt_parts.append(f"  - {pos.get('type', 'N/A')} {pos.get('volume', 'N/A')} lots @ {pos.get('price', 'N/A')}")
                    prompt_parts.append(f"    P/L: ${pos.get('profit', 0):.2f} ({pos.get('pips', 0):.1f} pips)")
            else:
                prompt_parts.append("  No open positions")
        
        # Account status
        if "account" in market_context:
            account = market_context["account"]
            prompt_parts.append(f"\nACCOUNT STATUS:")
            prompt_parts.append(f"  Balance: ${account.get('balance', 0):.2f}")
            prompt_parts.append(f"  Equity: ${account.get('equity', 0):.2f}")
            prompt_parts.append(f"  Margin Free: ${account.get('margin_free', 0):.2f}")
            prompt_parts.append(f"  Daily P/L: ${account.get('daily_pnl', 0):.2f}")
        
        # Risk constraints
        if "risk_constraints" in market_context:
            risk = market_context["risk_constraints"]
            prompt_parts.append(f"\nRISK CONSTRAINTS:")
            prompt_parts.append(f"  Risk per trade: {risk.get('risk_percentage', 0):.1f}%")
            prompt_parts.append(f"  Daily loss limit: ${risk.get('daily_loss_limit', 0):.2f}")
            prompt_parts.append(f"  Daily loss remaining: ${risk.get('daily_loss_remaining', 0):.2f}")
            prompt_parts.append(f"  Max concurrent trades: {risk.get('max_concurrent_trades', 0)}")
            prompt_parts.append(f"  Current open trades: {risk.get('current_open_trades', 0)}")
        
        # Add decision request
        prompt_parts.append(f"\n{'='*60}")
        prompt_parts.append("Based on the above analysis, what trading action should be taken?")
        prompt_parts.append("Respond with a JSON object containing your decision, reasoning, confidence, and key factors.")
        
        return "\n".join(prompt_parts)
    
    def _make_request_with_retry(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Make API request with exponential backoff retry logic.
        
        Args:
            payload: Request payload
            
        Returns:
            Response data or None if all retries failed
        """
        self.total_requests += 1
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                # Check for successful response
                if response.status_code == 200:
                    self.successful_requests += 1
                    data = response.json()
                    
                    # Track token usage if available
                    if "usage" in data:
                        self.total_tokens_used += data["usage"].get("total_tokens", 0)
                    
                    return data
                
                # Handle rate limiting
                elif response.status_code == 429:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"[LLMClient] Rate limited. Waiting {wait_time}s before retry {attempt + 1}/{self.max_retries}")
                    time.sleep(wait_time)
                    continue
                
                # Handle other errors
                else:
                    print(f"[LLMClient] API error {response.status_code}: {response.text}")
                    if attempt < self.max_retries - 1:
                        time.sleep(1)
                        continue
                    
            except requests.exceptions.Timeout:
                print(f"[LLMClient] Request timeout on attempt {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                    continue
                    
            except requests.exceptions.RequestException as e:
                print(f"[LLMClient] Request error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                    continue
            
            except Exception as e:
                print(f"[LLMClient] Unexpected error: {e}")
                break
        
        # All retries failed
        self.failed_requests += 1
        return None
    
    def _parse_trading_response(self, response_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse and validate LLM response.
        
        Args:
            response_data: Raw API response
            
        Returns:
            Parsed trading decision or None if invalid
        """
        try:
            # Extract message content
            if "choices" not in response_data or len(response_data["choices"]) == 0:
                print("[LLMClient] No choices in response")
                return None
            
            content = response_data["choices"][0]["message"]["content"]
            
            # Try to parse JSON from content
            # Sometimes LLM adds markdown code blocks or extra text, so we need to extract JSON
            json_str = content.strip()

            # Remove markdown code blocks if present
            if json_str.startswith("```"):
                lines = json_str.split("\n")
                json_str = "\n".join(lines[1:-1]) if len(lines) > 2 else json_str
                json_str = json_str.replace("```json", "").replace("```", "").strip()

            # Try to extract JSON object if there's extra text
            # Find the first { and last } to extract just the JSON object
            start_idx = json_str.find("{")
            end_idx = json_str.rfind("}")

            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = json_str[start_idx:end_idx + 1]

            # Parse JSON
            decision_data = json.loads(json_str)
            
            # Validate required fields
            if "decision" not in decision_data:
                print("[LLMClient] Missing 'decision' field in response")
                return None
            
            # Validate decision value
            decision = decision_data["decision"].upper()
            if decision not in ["BUY", "SELL", "NONE"]:
                print(f"[LLMClient] Invalid decision value: {decision}")
                return None
            
            # Ensure all fields are present
            result = {
                "decision": decision,
                "reasoning": decision_data.get("reasoning", "No reasoning provided"),
                "confidence": float(decision_data.get("confidence", 0.5)),
                "key_factors": decision_data.get("key_factors", []),
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"[LLMClient] Failed to parse JSON response: {e}")
            print(f"[LLMClient] Raw content: {content[:200]}...")
            return None
            
        except Exception as e:
            print(f"[LLMClient] Error parsing response: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get client statistics.
        
        Returns:
            Dictionary with usage statistics
        """
        success_rate = (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0
        
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": f"{success_rate:.1f}%",
            "total_tokens_used": self.total_tokens_used,
            "model": self.model
        }
    
    def __str__(self) -> str:
        """String representation of the client."""
        stats = self.get_statistics()
        return f"LLMClient(model={self.model}, requests={stats['total_requests']}, success_rate={stats['success_rate']})"

