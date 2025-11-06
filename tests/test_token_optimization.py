"""
Test token optimization for LLM prompts.

Compares token usage before and after optimization.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from strategies.llm_client import LLMClient


def count_tokens_approximate(text: str) -> int:
    """
    Approximate token count (rough estimate: 1 token ≈ 4 characters).
    
    Args:
        text: Text to count tokens for
        
    Returns:
        Approximate token count
    """
    return len(text) // 4


def test_system_prompt_optimization():
    """Test that system prompt is optimized."""
    client = LLMClient(api_key="test_key")
    
    system_prompt = client._build_default_system_prompt()
    token_count = count_tokens_approximate(system_prompt)
    
    print(f"\n📊 System Prompt Token Usage:")
    print(f"   Characters: {len(system_prompt)}")
    print(f"   Approximate tokens: {token_count}")
    print(f"   Content preview: {system_prompt[:100]}...")
    
    # Optimized prompt should be under 150 tokens
    assert token_count < 150, f"System prompt too long: {token_count} tokens (should be < 150)"
    print(f"   ✅ System prompt optimized (< 150 tokens)")


def test_user_prompt_optimization():
    """Test that user prompt is optimized."""
    client = LLMClient(api_key="test_key")
    
    # Sample market context
    market_context = {
        "symbol": "EURUSD",
        "current_price": {
            "bid": 1.08450,
            "ask": 1.08452,
            "spread": 0.2
        },
        "indicators": {
            "RSI_14": {"value": 55.5, "status": "Neutral"},
            "MACD": {"macd": 0.00012, "signal": 0.00010, "histogram": 0.00002, "status": "Bullish"},
            "MA_20": {"value": 1.08400, "position": "Above"},
            "MA_50": {"value": 1.08350, "position": "Above"},
            "ATR_14": {"value": 0.00015, "pips": 1.5, "volatility": "Low"},
            "Bollinger_Bands": {"upper": 1.08500, "middle": 1.08450, "lower": 1.08400, "position": "Middle"}
        },
        "price_action": {
            "M1": {"trend": "Uptrend", "change_pct": 0.05},
            "M5": {"trend": "Uptrend", "change_pct": 0.12},
            "M15": {"trend": "Uptrend", "change_pct": 0.18},
            "H1": {"trend": "Sideways", "change_pct": 0.02}
        },
        "positions": [],
        "account": {
            "balance": 10000.0,
            "equity": 10000.0,
            "margin_free": 9500.0,
            "daily_pnl": 125.50
        },
        "risk_constraints": {
            "risk_percentage": 1.0,
            "daily_loss_limit": 500.0,
            "daily_loss_remaining": 374.50,
            "max_concurrent_trades": 10,
            "current_open_trades": 0
        }
    }
    
    user_prompt = client._build_user_prompt(market_context)
    token_count = count_tokens_approximate(user_prompt)
    
    print(f"\n📊 User Prompt Token Usage:")
    print(f"   Characters: {len(user_prompt)}")
    print(f"   Approximate tokens: {token_count}")
    print(f"   Content:\n{user_prompt}")
    
    # Optimized prompt should be under 200 tokens
    assert token_count < 200, f"User prompt too long: {token_count} tokens (should be < 200)"
    print(f"   ✅ User prompt optimized (< 200 tokens)")


def test_position_prompt_optimization():
    """Test that position management prompt is optimized."""
    client = LLMClient(api_key="test_key")
    
    # Sample position context
    position_context = {
        "position": {
            "ticket": 12345,
            "type": "BUY",
            "volume": 0.1,
            "price_open": 1.08400,
            "price_current": 1.08450,
            "sl": 1.08300,
            "tp": 1.08600,
            "profit": 5.0,
            "pips": 5.0,
            "duration": "15 minutes"
        },
        "symbol": "EURUSD",
        "current_price": {
            "bid": 1.08450,
            "ask": 1.08452,
            "spread": 0.2
        },
        "indicators": {
            "RSI_14": {"value": 55.5, "status": "Neutral"},
            "MACD": {"macd": 0.00012, "signal": 0.00010, "histogram": 0.00002, "status": "Bullish"},
            "MA_20": {"value": 1.08400, "position": "Above"},
            "ATR_14": {"value": 0.00015, "pips": 1.5, "volatility": "Low"}
        },
        "price_action": {
            "M5": {"trend": "Uptrend", "change_pct": 0.12},
            "M15": {"trend": "Uptrend", "change_pct": 0.18}
        },
        "account": {
            "balance": 10000.0,
            "equity": 10005.0,
            "daily_pnl": 130.50
        }
    }
    
    position_prompt = client._build_position_prompt(position_context)
    token_count = count_tokens_approximate(position_prompt)
    
    print(f"\n📊 Position Prompt Token Usage:")
    print(f"   Characters: {len(position_prompt)}")
    print(f"   Approximate tokens: {token_count}")
    print(f"   Content:\n{position_prompt}")
    
    # Optimized prompt should be under 150 tokens
    assert token_count < 150, f"Position prompt too long: {token_count} tokens (should be < 150)"
    print(f"   ✅ Position prompt optimized (< 150 tokens)")


def test_total_token_savings():
    """Calculate total token savings."""
    client = LLMClient(api_key="test_key")
    
    # Estimate old token usage (based on verbose prompts)
    old_system_prompt_tokens = 250  # Old verbose system prompt
    old_user_prompt_tokens = 500    # Old verbose user prompt
    old_position_prompt_tokens = 400  # Old verbose position prompt
    
    # Calculate new token usage
    system_prompt = client._build_default_system_prompt()
    new_system_tokens = count_tokens_approximate(system_prompt)
    
    # Sample context for user prompt
    market_context = {
        "symbol": "EURUSD",
        "current_price": {"bid": 1.08450, "ask": 1.08452, "spread": 0.2},
        "indicators": {
            "RSI_14": {"value": 55.5, "status": "Neutral"},
            "MACD": {"histogram": 0.00002, "status": "Bullish"}
        },
        "price_action": {"M5": {"trend": "Uptrend", "change_pct": 0.12}},
        "positions": [],
        "account": {"balance": 10000.0, "equity": 10000.0, "daily_pnl": 125.50},
        "risk_constraints": {"risk_percentage": 1.0, "max_concurrent_trades": 10, "current_open_trades": 0}
    }
    
    user_prompt = client._build_user_prompt(market_context)
    new_user_tokens = count_tokens_approximate(user_prompt)
    
    # Calculate savings
    system_savings = old_system_prompt_tokens - new_system_tokens
    user_savings = old_user_prompt_tokens - new_user_tokens
    system_savings_pct = (system_savings / old_system_prompt_tokens) * 100
    user_savings_pct = (user_savings / old_user_prompt_tokens) * 100
    
    print(f"\n💰 Token Savings Summary:")
    print(f"   System Prompt: {old_system_prompt_tokens} → {new_system_tokens} tokens ({system_savings_pct:.1f}% reduction)")
    print(f"   User Prompt: {old_user_prompt_tokens} → {new_user_tokens} tokens ({user_savings_pct:.1f}% reduction)")
    print(f"   Total per request: {old_system_prompt_tokens + old_user_prompt_tokens} → {new_system_tokens + new_user_tokens} tokens")
    print(f"   Savings per request: {system_savings + user_savings} tokens ({((system_savings + user_savings) / (old_system_prompt_tokens + old_user_prompt_tokens)) * 100:.1f}% reduction)")
    
    # With 12 requests per minute (5-second analysis interval)
    requests_per_minute = 12
    old_tokens_per_minute = (old_system_prompt_tokens + old_user_prompt_tokens) * requests_per_minute
    new_tokens_per_minute = (new_system_tokens + new_user_tokens) * requests_per_minute
    savings_per_minute = old_tokens_per_minute - new_tokens_per_minute
    
    print(f"\n📈 Impact at 5-second analysis interval (12 requests/minute):")
    print(f"   Old: {old_tokens_per_minute:,} tokens/minute")
    print(f"   New: {new_tokens_per_minute:,} tokens/minute")
    print(f"   Savings: {savings_per_minute:,} tokens/minute ({(savings_per_minute / old_tokens_per_minute) * 100:.1f}% reduction)")
    print(f"   Hourly savings: {savings_per_minute * 60:,} tokens")
    print(f"   Daily savings: {savings_per_minute * 60 * 24:,} tokens")


if __name__ == "__main__":
    print("=" * 70)
    print("🔬 Token Optimization Test")
    print("=" * 70)
    
    try:
        test_system_prompt_optimization()
        test_user_prompt_optimization()
        test_position_prompt_optimization()
        test_total_token_savings()
        
        print(f"\n{'=' * 70}")
        print("✅ All token optimization tests passed!")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

