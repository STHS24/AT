"""
Test DeepSeek API analysis using test.json market data.

This script loads market data from test.json and sends it to the DeepSeek API
to test the AI's trading decision-making capabilities.
"""

import sys
import os
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from strategies.llm_client import LLMClient


def load_test_data(json_path: str) -> dict:
    """
    Load test market data from JSON file.
    
    Args:
        json_path: Path to test.json file
        
    Returns:
        Dictionary with market data
    """
    with open(json_path, 'r') as f:
        return json.load(f)


def convert_to_market_context(test_data: dict) -> dict:
    """
    Convert test.json format to the market_context format expected by LLMClient.
    
    Args:
        test_data: Data from test.json
        
    Returns:
        Market context dictionary compatible with LLMClient
    """
    # Extract data from test.json structure
    price_data = test_data.get("price_data", {})
    indicators = test_data.get("technical_indicators", {})
    price_action = test_data.get("multi_timeframe_price_action", {})
    positions = test_data.get("open_positions", [])
    account = test_data.get("account_status", {})
    risk = test_data.get("risk_constraints", {})
    symbol_data = test_data.get("symbol", {})
    
    # Convert to market_context format
    market_context = {
        "symbol": symbol_data.get("pair", "EURUSD"),
        "timestamp": price_data.get("timestamp", ""),
        "current_price": {
            "bid": price_data.get("bid"),
            "ask": price_data.get("ask"),
            "spread": price_data.get("spread_pips")
        },
        "indicators": {
            "RSI_14": {
                "value": indicators.get("RSI_14", {}).get("value"),
                "status": indicators.get("RSI_14", {}).get("status")
            },
            "MACD": {
                "macd": indicators.get("MACD_12_26_9", {}).get("macd_line"),
                "signal": indicators.get("MACD_12_26_9", {}).get("signal_line"),
                "histogram": indicators.get("MACD_12_26_9", {}).get("histogram"),
                "status": indicators.get("MACD_12_26_9", {}).get("status")
            },
            "MA_20": {
                "value": indicators.get("moving_averages", {}).get("MA_20", {}).get("value"),
                "position": indicators.get("moving_averages", {}).get("MA_20", {}).get("position_vs_price")
            },
            "MA_50": {
                "value": indicators.get("moving_averages", {}).get("MA_50", {}).get("value"),
                "position": indicators.get("moving_averages", {}).get("MA_50", {}).get("position_vs_price")
            },
            "ATR_14": {
                "value": indicators.get("ATR_14", {}).get("value_price_units"),
                "pips": indicators.get("ATR_14", {}).get("value_pips"),
                "volatility": indicators.get("ATR_14", {}).get("volatility_status")
            },
            "Bollinger_Bands": {
                "upper": indicators.get("BollingerBands_20_2", {}).get("upper_band"),
                "middle": indicators.get("BollingerBands_20_2", {}).get("middle_band"),
                "lower": indicators.get("BollingerBands_20_2", {}).get("lower_band"),
                "position": indicators.get("BollingerBands_20_2", {}).get("position")
            }
        },
        "price_action": {}
    }
    
    # Convert price action
    for tf, data in price_action.items():
        market_context["price_action"][tf] = {
            "close": data.get("close"),
            "change": data.get("change"),
            "change_pct": data.get("change_percent"),
            "trend": data.get("trend"),
            "high": data.get("high"),
            "low": data.get("low")
        }
    
    # Convert positions
    market_context["positions"] = []
    for pos in positions:
        market_context["positions"].append({
            "ticket": pos.get("ticket"),
            "type": pos.get("type"),
            "volume": pos.get("volume_lots"),
            "price": pos.get("entry_price"),
            "current_price": pos.get("current_price"),
            "sl": pos.get("stop_loss"),
            "tp": pos.get("take_profit"),
            "profit": pos.get("profit_usd"),
            "pips": pos.get("profit_pips")
        })
    
    # Convert account
    market_context["account"] = {
        "balance": account.get("balance"),
        "equity": account.get("equity"),
        "margin": account.get("used_margin"),
        "margin_free": account.get("free_margin"),
        "margin_level": account.get("margin_level_percent"),
        "daily_pnl": account.get("daily_PL")
    }
    
    # Convert risk constraints
    market_context["risk_constraints"] = {
        "risk_percentage": risk.get("risk_percentage_per_trade"),
        "daily_loss_limit": risk.get("daily_loss_limit_usd"),
        "daily_profit_target": risk.get("daily_profit_target_usd"),
        "max_concurrent_trades": risk.get("max_concurrent_trades"),
        "current_open_trades": risk.get("current_open_trades"),
        "daily_loss_remaining": risk.get("daily_loss_remaining"),
        "daily_profit_remaining": risk.get("daily_profit_remaining")
    }
    
    return market_context


def print_market_summary(test_data: dict):
    """Print a summary of the market data."""
    print("\n" + "="*70)
    print("📊 MARKET DATA SUMMARY")
    print("="*70)
    
    symbol = test_data.get("symbol", {}).get("pair", "UNKNOWN")
    sentiment = test_data.get("sentiment", "Unknown")
    price = test_data.get("price_data", {})
    
    print(f"\n🔹 Symbol: {symbol}")
    print(f"🔹 Overall Sentiment: {sentiment}")
    print(f"🔹 Price: {price.get('bid')}/{price.get('ask')} (spread: {price.get('spread_pips')}p)")
    
    # Technical indicators
    indicators = test_data.get("technical_indicators", {})
    print(f"\n📈 Technical Indicators:")
    print(f"   RSI: {indicators.get('RSI_14', {}).get('value')} ({indicators.get('RSI_14', {}).get('status')})")
    print(f"   MACD: {indicators.get('MACD_12_26_9', {}).get('histogram')} ({indicators.get('MACD_12_26_9', {}).get('status')})")
    print(f"   ATR: {indicators.get('ATR_14', {}).get('value_pips')}p ({indicators.get('ATR_14', {}).get('volatility_status')})")
    
    # Trends
    price_action = test_data.get("multi_timeframe_price_action", {})
    print(f"\n📉 Multi-Timeframe Trends:")
    for tf, data in price_action.items():
        print(f"   {tf}: {data.get('trend')} ({data.get('change_percent'):+.2f}%)")
    
    # Positions
    positions = test_data.get("open_positions", [])
    print(f"\n💼 Open Positions: {len(positions)}")
    for pos in positions:
        print(f"   #{pos.get('ticket')}: {pos.get('type')} {pos.get('volume_lots')}lots @{pos.get('entry_price')} | P/L: ${pos.get('profit_usd'):.2f} ({pos.get('profit_pips'):+.1f}p)")
    
    # Account
    account = test_data.get("account_status", {})
    print(f"\n💰 Account:")
    print(f"   Balance: ${account.get('balance'):.2f}")
    print(f"   Equity: ${account.get('equity'):.2f}")
    print(f"   Daily P/L: ${account.get('daily_PL'):.2f}")
    
    # Risk
    risk = test_data.get("risk_constraints", {})
    print(f"\n⚠️  Risk Status:")
    print(f"   Open Trades: {risk.get('current_open_trades')}/{risk.get('max_concurrent_trades')}")
    print(f"   Daily Loss Remaining: ${risk.get('daily_loss_remaining'):.2f}")
    print(f"   Daily Profit Remaining: ${risk.get('daily_profit_remaining'):.2f}")


def test_deepseek_api(json_path: str, api_key: str):
    """
    Test DeepSeek API with market data from test.json.
    
    Args:
        json_path: Path to test.json file
        api_key: DeepSeek API key
    """
    print("\n" + "="*70)
    print("🤖 DEEPSEEK API TEST")
    print("="*70)
    
    # Load test data
    print(f"\n📂 Loading test data from: {json_path}")
    test_data = load_test_data(json_path)
    
    # Print market summary
    print_market_summary(test_data)
    
    # Convert to market context
    print(f"\n🔄 Converting to market context format...")
    market_context = convert_to_market_context(test_data)
    
    # Initialize LLM client
    print(f"\n🔌 Initializing DeepSeek API client...")
    client = LLMClient(api_key=api_key)
    
    # Build and display the prompt
    print(f"\n📝 Building prompt for DeepSeek...")
    user_prompt = client._build_user_prompt(market_context)
    system_prompt = client._build_default_system_prompt()
    
    print(f"\n" + "-"*70)
    print("SYSTEM PROMPT:")
    print("-"*70)
    print(system_prompt)
    
    print(f"\n" + "-"*70)
    print("USER PROMPT:")
    print("-"*70)
    print(user_prompt)
    
    # Calculate token usage
    system_tokens = len(system_prompt) // 4
    user_tokens = len(user_prompt) // 4
    total_tokens = system_tokens + user_tokens
    
    print(f"\n" + "-"*70)
    print("TOKEN USAGE (approximate):")
    print("-"*70)
    print(f"   System prompt: ~{system_tokens} tokens")
    print(f"   User prompt: ~{user_tokens} tokens")
    print(f"   Total: ~{total_tokens} tokens")
    
    # Get AI decision
    print(f"\n🤖 Sending request to DeepSeek API...")
    print(f"   (This may take 5-10 seconds...)")
    
    try:
        decision = client.get_trading_decision(market_context)
        
        print(f"\n" + "="*70)
        print("✅ AI DECISION RECEIVED")
        print("="*70)
        
        if decision:
            print(f"\n🎯 Decision: {decision.get('decision', 'UNKNOWN')}")
            print(f"📊 Confidence: {decision.get('confidence', 0):.2f}")
            print(f"⚡ Urgent: {decision.get('urgent', False)}")
            print(f"\n💡 Reasoning:")
            print(f"   {decision.get('reasoning', 'No reasoning provided')}")
            
            if decision.get('key_factors'):
                print(f"\n🔑 Key Factors:")
                for i, factor in enumerate(decision.get('key_factors', []), 1):
                    print(f"   {i}. {factor}")
            
            # Analysis
            print(f"\n" + "-"*70)
            print("📊 ANALYSIS:")
            print("-"*70)
            
            ai_decision = decision.get('decision', 'NONE')
            confidence = decision.get('confidence', 0)
            urgent = decision.get('urgent', False)
            
            if ai_decision == "NONE":
                print("   ⏸️  AI recommends NO ACTION - waiting for better opportunity")
            elif ai_decision in ["BUY", "SELL"]:
                action_emoji = "🟢" if ai_decision == "BUY" else "🔴"
                urgency_text = "⚡ URGENT" if urgent else "📅 Normal"
                print(f"   {action_emoji} AI recommends {ai_decision} with {confidence:.0%} confidence")
                print(f"   {urgency_text} - {'Bypass cooldown' if urgent else 'Respect cooldown'}")
            
            # Compare with test data sentiment
            test_sentiment = test_data.get("sentiment", "Unknown")
            print(f"\n🔍 Comparison:")
            print(f"   Test data sentiment: {test_sentiment}")
            print(f"   AI decision: {ai_decision}")
            
            if (test_sentiment == "Bearish" and ai_decision == "SELL") or \
               (test_sentiment == "Bullish" and ai_decision == "BUY"):
                print(f"   ✅ AI decision MATCHES test sentiment!")
            elif ai_decision == "NONE":
                print(f"   ⚠️  AI chose to wait despite {test_sentiment} sentiment")
            else:
                print(f"   ❌ AI decision DIFFERS from test sentiment")
        else:
            print(f"\n❌ No decision received from API")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n" + "="*70)
    print("✅ TEST COMPLETE")
    print("="*70)
    
    return True


if __name__ == "__main__":
    # Get API key from environment or config
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        # Try to load from config
        config_path = Path(__file__).parent.parent / "config" / "settings.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Navigate through the strategy_config structure
                strategy_config = config.get("strategy_config", {})
                ai_strategy = strategy_config.get("AIStrategy", {})
                params = ai_strategy.get("params", {})
                api_key = params.get("api_key")

    if not api_key:
        print("\n❌ ERROR: No API key found!")
        print("   Set OPENROUTER_API_KEY environment variable or add to config/settings.json")
        sys.exit(1)
    
    # Path to test.json
    test_json_path = Path(__file__).parent.parent / "test.json"
    
    if not test_json_path.exists():
        print(f"❌ ERROR: test.json not found at {test_json_path}")
        sys.exit(1)
    
    # Run test
    success = test_deepseek_api(str(test_json_path), api_key)
    
    sys.exit(0 if success else 1)

