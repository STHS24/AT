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

    def get_position_management_decision(self, market_context: Dict[str, Any],
                                        temperature: float = 0.7) -> Optional[Dict[str, Any]]:
        """
        Get position management decision from LLM.

        Args:
            market_context: Dictionary containing position and market data
            temperature: LLM temperature (0.0-1.0)

        Returns:
            Dictionary with action (HOLD/CLOSE/CLOSE_PARTIAL), reasoning, and confidence
        """
        # Build position management system prompt
        system_prompt = self._build_position_management_system_prompt()

        # Build user prompt from market context
        user_prompt = self._build_position_prompt(market_context)

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
        return self._parse_position_response(response_data)

    def _build_default_system_prompt(self) -> str:
        """Build compact system prompt for trading AI (optimized for tokens)."""
        return """Forex AI. Analyze, decide BUY/SELL/NONE.

JSON:
{
    "decision": "BUY"|"SELL"|"NONE",
    "reasoning": "Brief explanation",
    "confidence": 0.0-1.0,
    "key_factors": ["factor1", "factor2"],
    "urgent": true|false
}

Rules:
- BUY/SELL only if confidence > 0.7
- urgent=true ONLY for breakouts, critical levels, extreme volatility
- Consider indicators, trends, risk, positions
- Be conservative
"""
    
    def _build_user_prompt(self, market_context: Dict[str, Any]) -> str:
        """
        Build compact user prompt from market context (optimized for token usage).

        Args:
            market_context: Market data and trading context

        Returns:
            Formatted prompt string
        """
        parts = []

        # Symbol and price (compact)
        if "symbol" in market_context:
            parts.append(f"{market_context['symbol']}")

        if "current_price" in market_context:
            p = market_context["current_price"]
            parts.append(f"Price: {p.get('bid')}/{p.get('ask')} (spread {p.get('spread')}p)")

        # Technical indicators (compact)
        if "indicators" in market_context:
            ind = market_context["indicators"]
            ind_parts = []

            # RSI
            if "RSI_14" in ind:
                rsi = ind["RSI_14"]
                ind_parts.append(f"RSI:{rsi.get('value')}({rsi.get('status')})")

            # MACD
            if "MACD" in ind:
                macd = ind["MACD"]
                ind_parts.append(f"MACD:{macd.get('histogram'):.5f}({macd.get('status')})")

            # Moving Averages
            if "MA_20" in ind:
                ma20 = ind["MA_20"]
                ind_parts.append(f"MA20:{ma20.get('position')}")
            if "MA_50" in ind:
                ma50 = ind["MA_50"]
                ind_parts.append(f"MA50:{ma50.get('position')}")

            # ATR
            if "ATR_14" in ind:
                atr = ind["ATR_14"]
                ind_parts.append(f"ATR:{atr.get('pips')}p({atr.get('volatility')})")

            # Bollinger Bands
            if "Bollinger_Bands" in ind:
                bb = ind["Bollinger_Bands"]
                ind_parts.append(f"BB:{bb.get('position')}")

            if ind_parts:
                parts.append(f"Indicators: {', '.join(ind_parts)}")

        # Price action (compact)
        if "price_action" in market_context:
            pa = market_context["price_action"]
            pa_parts = []
            for tf, data in pa.items():
                trend = data.get('trend', 'N/A')
                change = data.get('change_pct', 0)
                pa_parts.append(f"{tf}:{trend}({change:+.2f}%)")
            if pa_parts:
                parts.append(f"Trends: {', '.join(pa_parts)}")

        # Positions (compact)
        if "positions" in market_context:
            pos = market_context["positions"]
            if pos:
                pos_parts = []
                for p in pos:
                    pos_parts.append(f"{p.get('type')} {p.get('volume')}@{p.get('price')} P/L:{p.get('pips'):.1f}p")
                parts.append(f"Positions: {', '.join(pos_parts)}")
            else:
                parts.append("Positions: None")

        # Account (compact)
        if "account" in market_context:
            acc = market_context["account"]
            parts.append(f"Account: Bal ${acc.get('balance', 0):.0f}, Eq ${acc.get('equity', 0):.0f}, DayPL ${acc.get('daily_pnl', 0):.2f}")

        # Risk (compact)
        if "risk_constraints" in market_context:
            risk = market_context["risk_constraints"]
            parts.append(f"Risk: {risk.get('risk_percentage', 0):.1f}%/trade, {risk.get('current_open_trades', 0)}/{risk.get('max_concurrent_trades', 0)} trades, ${risk.get('daily_loss_remaining', 0):.0f} remaining")

        # Decision request
        parts.append("\nDecide: BUY/SELL/NONE? Respond JSON.")

        return "\n".join(parts)

    def _build_position_management_system_prompt(self) -> str:
        """Build compact system prompt for position management (optimized for tokens)."""
        return """Position management AI. Decide: HOLD/CLOSE/CLOSE_PARTIAL.

JSON:
{
    "action": "HOLD"|"CLOSE"|"CLOSE_PARTIAL",
    "reasoning": "Brief explanation",
    "confidence": 0.0-1.0,
    "partial_percentage": 0.5 (if CLOSE_PARTIAL)
}

Rules:
- HOLD if conditions favorable
- CLOSE if trend reversed or target hit
- CLOSE_PARTIAL to lock profit, keep upside
- Confidence > 0.7 for closing
- Be conservative
"""

    def _build_position_prompt(self, market_context: Dict[str, Any]) -> str:
        """
        Build compact position analysis prompt (optimized for tokens).

        Args:
            market_context: Position and market data

        Returns:
            Formatted prompt string
        """
        parts = []

        # Position details (compact)
        if "position" in market_context:
            pos = market_context["position"]
            parts.append(f"Position #{pos.get('ticket')}: {pos.get('type')} {pos.get('volume')}lots @{pos.get('price_open')} → {pos.get('price_current')}")
            parts.append(f"SL:{pos.get('sl')} TP:{pos.get('tp')} P/L:${pos.get('profit', 0):.2f}({pos.get('pips', 0):.1f}p) Duration:{pos.get('duration')}")

        # Current market (compact)
        if "current_price" in market_context:
            p = market_context["current_price"]
            parts.append(f"Market: {p.get('bid')}/{p.get('ask')} (spread {p.get('spread')}p)")

        # Technical indicators (compact)
        if "indicators" in market_context:
            ind = market_context["indicators"]
            ind_parts = []

            if "RSI_14" in ind:
                rsi = ind["RSI_14"]
                ind_parts.append(f"RSI:{rsi.get('value')}({rsi.get('status')})")
            if "MACD" in ind:
                macd = ind["MACD"]
                ind_parts.append(f"MACD:{macd.get('histogram'):.5f}({macd.get('status')})")
            if "MA_20" in ind:
                ind_parts.append(f"MA20:{ind['MA_20'].get('position')}")
            if "MA_50" in ind:
                ind_parts.append(f"MA50:{ind['MA_50'].get('position')}")
            if "ATR_14" in ind:
                atr = ind["ATR_14"]
                ind_parts.append(f"ATR:{atr.get('pips')}p({atr.get('volatility')})")
            if "Bollinger_Bands" in ind:
                ind_parts.append(f"BB:{ind['Bollinger_Bands'].get('position')}")

            if ind_parts:
                parts.append(f"Indicators: {', '.join(ind_parts)}")

        # Price action (compact)
        if "price_action" in market_context:
            pa = market_context["price_action"]
            pa_parts = []
            for tf, data in pa.items():
                pa_parts.append(f"{tf}:{data.get('trend')}({data.get('change_pct', 0):+.2f}%)")
            if pa_parts:
                parts.append(f"Trends: {', '.join(pa_parts)}")

        # Account (compact)
        if "account" in market_context:
            acc = market_context["account"]
            parts.append(f"Account: Bal ${acc.get('balance', 0):.0f}, Eq ${acc.get('equity', 0):.0f}, DayPL ${acc.get('daily_pnl', 0):.2f}")

        # Decision request
        parts.append("\nHOLD/CLOSE/CLOSE_PARTIAL? Respond JSON.")

        return "\n".join(parts)

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
                    # Check for Retry-After header
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        wait_time = int(retry_after)
                    else:
                        wait_time = min(2 ** attempt, 30)  # Exponential backoff, max 30s

                    print(f"[LLMClient] ⚠️  Rate limited. Waiting {wait_time}s before retry {attempt + 1}/{self.max_retries}")
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
                "urgent": bool(decision_data.get("urgent", False)),
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

    def _parse_position_response(self, response_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse and validate position management LLM response.

        Args:
            response_data: Raw API response

        Returns:
            Parsed position decision or None if invalid
        """
        try:
            # Extract message content
            if "choices" not in response_data or len(response_data["choices"]) == 0:
                print("[LLMClient] No choices in response")
                return None

            content = response_data["choices"][0]["message"]["content"]

            # Try to parse JSON from content
            json_str = content.strip()

            # Remove markdown code blocks if present
            if json_str.startswith("```"):
                lines = json_str.split("\n")
                json_str = "\n".join(lines[1:-1]) if len(lines) > 2 else json_str
                json_str = json_str.replace("```json", "").replace("```", "").strip()

            # Try to extract JSON object if there's extra text
            start_idx = json_str.find("{")
            end_idx = json_str.rfind("}")

            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = json_str[start_idx:end_idx + 1]

            # Parse JSON
            decision_data = json.loads(json_str)

            # Validate required fields
            if "action" not in decision_data:
                print("[LLMClient] Missing 'action' field in response")
                return None

            # Validate action value
            action = decision_data["action"].upper()
            if action not in ["HOLD", "CLOSE", "CLOSE_PARTIAL"]:
                print(f"[LLMClient] Invalid action value: {action}")
                return None

            # Ensure all fields are present
            result = {
                "action": action,
                "reasoning": decision_data.get("reasoning", "No reasoning provided"),
                "confidence": float(decision_data.get("confidence", 0.5)),
                "partial_percentage": float(decision_data.get("partial_percentage", 0.5)),
                "timestamp": datetime.now().isoformat()
            }

            # Validate partial_percentage range
            if result["partial_percentage"] < 0.0 or result["partial_percentage"] > 1.0:
                result["partial_percentage"] = 0.5  # Default to 50%

            return result

        except json.JSONDecodeError as e:
            print(f"[LLMClient] Failed to parse JSON response: {e}")
            print(f"[LLMClient] Raw content: {content[:200]}...")
            return None

        except Exception as e:
            print(f"[LLMClient] Error parsing position response: {e}")
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

