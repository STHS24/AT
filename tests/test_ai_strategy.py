"""
Unit tests for AI Strategy components.

Tests for LLMClient, MarketAnalyzer, and AIStrategy.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import numpy as np


class TestLLMClient:
    """Tests for LLM Client."""
    
    def test_llm_client_initialization(self):
        """Test LLM client initialization."""
        from strategies.llm_client import LLMClient
        
        client = LLMClient(
            api_key="test_key",
            model="test_model",
            timeout=30,
            max_retries=3
        )
        
        assert client.api_key == "test_key"
        assert client.model == "test_model"
        assert client.timeout == 30
        assert client.max_retries == 3
        assert client.total_requests == 0
    
    def test_build_user_prompt(self):
        """Test user prompt building."""
        from strategies.llm_client import LLMClient

        client = LLMClient(api_key="test_key")

        market_context = {
            "symbol": "EURUSD",
            "current_price": {"bid": 1.16000, "ask": 1.16005, "spread": 0.5},
            "indicators": {"RSI_14": {"value": 55.5, "status": "Neutral"}},
            "positions": [],
            "account": {"balance": 10000.0, "equity": 10000.0},
            "risk_constraints": {"risk_percentage": 1.0}
        }

        prompt = client._build_user_prompt(market_context)

        assert "EURUSD" in prompt
        assert "1.16" in prompt  # Check for price (may be formatted differently)
        assert "RSI_14" in prompt
        assert "balance" in prompt.lower()
    
    @patch('strategies.llm_client.requests.post')
    def test_successful_api_call(self, mock_post):
        """Test successful API call."""
        from strategies.llm_client import LLMClient
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"decision": "BUY", "reasoning": "Test", "confidence": 0.8}'
                }
            }]
        }
        mock_post.return_value = mock_response
        
        client = LLMClient(api_key="test_key")
        market_context = {"symbol": "EURUSD"}
        
        result = client.get_trading_decision(market_context)
        
        assert result is not None
        assert result["decision"] == "BUY"
        assert result["confidence"] == 0.8
        assert client.successful_requests == 1
    
    @patch('strategies.llm_client.requests.post')
    def test_api_retry_on_failure(self, mock_post):
        """Test API retry logic on failure."""
        from strategies.llm_client import LLMClient
        
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        client = LLMClient(api_key="test_key", max_retries=2)
        market_context = {"symbol": "EURUSD"}
        
        result = client.get_trading_decision(market_context)
        
        assert result is None
        assert mock_post.call_count == 2  # Should retry
        assert client.failed_requests == 1
    
    def test_parse_valid_json_response(self):
        """Test parsing valid JSON response."""
        from strategies.llm_client import LLMClient
        
        client = LLMClient(api_key="test_key")
        
        response_data = {
            "choices": [{
                "message": {
                    "content": '{"decision": "SELL", "reasoning": "Bearish trend", "confidence": 0.75, "key_factors": ["RSI overbought"]}'
                }
            }]
        }
        
        result = client._parse_trading_response(response_data)
        
        assert result is not None
        assert result["decision"] == "SELL"
        assert result["reasoning"] == "Bearish trend"
        assert result["confidence"] == 0.75
        assert "RSI overbought" in result["key_factors"]
    
    def test_parse_json_with_markdown(self):
        """Test parsing JSON wrapped in markdown code blocks."""
        from strategies.llm_client import LLMClient
        
        client = LLMClient(api_key="test_key")
        
        response_data = {
            "choices": [{
                "message": {
                    "content": '```json\n{"decision": "NONE", "reasoning": "Wait", "confidence": 0.5}\n```'
                }
            }]
        }
        
        result = client._parse_trading_response(response_data)
        
        assert result is not None
        assert result["decision"] == "NONE"


class TestMarketAnalyzer:
    """Tests for Market Analyzer."""
    
    @patch('strategies.market_analyzer.mt5')
    def test_get_current_price(self, mock_mt5):
        """Test getting current price."""
        from strategies.market_analyzer import MarketAnalyzer
        
        # Mock tick data
        mock_tick = Mock()
        mock_tick.bid = 1.16000
        mock_tick.ask = 1.16005
        mock_tick.time = 1234567890
        mock_mt5.symbol_info_tick.return_value = mock_tick
        
        # Mock symbol info
        mock_symbol_info = Mock()
        mock_symbol_info.point = 0.00001
        mock_mt5.symbol_info.return_value = mock_symbol_info
        
        analyzer = MarketAnalyzer()
        price_data = analyzer._get_current_price("EURUSD")
        
        assert price_data["bid"] == 1.16000
        assert price_data["ask"] == 1.16005
        assert "spread" in price_data
    
    def test_calculate_rsi(self):
        """Test RSI calculation."""
        from strategies.market_analyzer import MarketAnalyzer
        
        analyzer = MarketAnalyzer()
        
        # Create sample price data
        prices = np.array([100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 
                          111, 110, 112, 114, 113, 115, 117, 116, 118, 120])
        
        rsi = analyzer._calculate_rsi(prices, period=14)
        
        assert len(rsi) > 0
        assert all(0 <= val <= 100 for val in rsi if val > 0)
    
    def test_calculate_macd(self):
        """Test MACD calculation."""
        from strategies.market_analyzer import MarketAnalyzer
        
        analyzer = MarketAnalyzer()
        
        # Create sample price data
        prices = np.linspace(100, 120, 50)
        
        macd_line, signal_line, histogram = analyzer._calculate_macd(prices, 12, 26, 9)
        
        assert len(macd_line) == len(prices)
        assert len(signal_line) == len(prices)
        assert len(histogram) == len(prices)
    
    def test_calculate_bollinger_bands(self):
        """Test Bollinger Bands calculation."""
        from strategies.market_analyzer import MarketAnalyzer
        
        analyzer = MarketAnalyzer()
        
        # Create sample price data
        prices = np.array([100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
                          111, 110, 112, 114, 113, 115, 117, 116, 118, 120])
        
        upper, middle, lower = analyzer._calculate_bollinger_bands(prices, period=20, std_dev=2.0)
        
        assert upper is not None
        assert middle is not None
        assert lower is not None
        assert upper > middle > lower
    
    @patch('strategies.market_analyzer.mt5')
    def test_get_market_context(self, mock_mt5):
        """Test getting complete market context."""
        from strategies.market_analyzer import MarketAnalyzer
        
        # Mock MT5 functions
        mock_tick = Mock()
        mock_tick.bid = 1.16000
        mock_tick.ask = 1.16005
        mock_tick.time = 1234567890
        mock_mt5.symbol_info_tick.return_value = mock_tick
        
        mock_symbol_info = Mock()
        mock_symbol_info.point = 0.00001
        mock_mt5.symbol_info.return_value = mock_symbol_info
        
        # Mock rates data
        mock_rates = np.array([(1.16000, 1.16010, 1.15990, 1.16005)] * 100,
                             dtype=[('open', 'f8'), ('high', 'f8'), ('low', 'f8'), ('close', 'f8')])
        mock_mt5.copy_rates_from_pos.return_value = mock_rates
        
        mock_mt5.positions_get.return_value = []
        
        mock_account = Mock()
        mock_account.balance = 10000.0
        mock_account.equity = 10000.0
        mock_account.margin = 0.0
        mock_account.margin_free = 10000.0
        mock_account.margin_level = 0.0
        mock_mt5.account_info.return_value = mock_account
        
        analyzer = MarketAnalyzer()
        config = {"risk_management": {"risk_percentage": 1.0}, "max_concurrent_trades": 3}
        
        context = analyzer.get_market_context("EURUSD", config)
        
        assert context["symbol"] == "EURUSD"
        assert "current_price" in context
        assert "indicators" in context
        assert "account" in context
        assert "risk_constraints" in context


class TestAIStrategy:
    """Tests for AI Strategy."""
    
    def test_ai_strategy_initialization(self):
        """Test AI strategy initialization."""
        from strategies.ai_strategy import AIStrategy
        
        params = {
            "api_key": "test_key",
            "model": "test_model",
            "confidence_threshold": 0.7
        }
        
        strategy = AIStrategy(params)
        
        assert strategy.name == "AIStrategy"
        assert strategy.params["confidence_threshold"] == 0.7
        assert strategy.llm_client is not None
        assert strategy.market_analyzer is not None
    
    def test_ai_strategy_requires_api_key(self):
        """Test that AI strategy requires API key."""
        from strategies.ai_strategy import AIStrategy
        
        with pytest.raises(ValueError, match="API key is required"):
            AIStrategy({"api_key": None})
    
    @patch('strategies.ai_strategy.MarketAnalyzer')
    @patch('strategies.ai_strategy.LLMClient')
    def test_generate_signal_with_high_confidence(self, mock_llm_class, mock_analyzer_class):
        """Test signal generation with high confidence."""
        from strategies.ai_strategy import AIStrategy
        
        # Mock LLM client
        mock_llm = Mock()
        mock_llm.get_trading_decision.return_value = {
            "decision": "BUY",
            "reasoning": "Strong bullish signals",
            "confidence": 0.85,
            "key_factors": ["RSI oversold", "MACD bullish crossover"]
        }
        mock_llm_class.return_value = mock_llm
        
        # Mock market analyzer
        mock_analyzer = Mock()
        mock_analyzer.get_market_context.return_value = {"symbol": "EURUSD"}
        mock_analyzer_class.return_value = mock_analyzer
        
        strategy = AIStrategy({"api_key": "test_key", "confidence_threshold": 0.7})
        signal = strategy.generate_signal("EURUSD")
        
        assert signal == "BUY"
    
    @patch('strategies.ai_strategy.MarketAnalyzer')
    @patch('strategies.ai_strategy.LLMClient')
    def test_generate_signal_with_low_confidence(self, mock_llm_class, mock_analyzer_class):
        """Test signal generation with low confidence (should return NONE)."""
        from strategies.ai_strategy import AIStrategy
        
        # Mock LLM client with low confidence
        mock_llm = Mock()
        mock_llm.get_trading_decision.return_value = {
            "decision": "BUY",
            "reasoning": "Weak signals",
            "confidence": 0.5,
            "key_factors": []
        }
        mock_llm_class.return_value = mock_llm
        
        # Mock market analyzer
        mock_analyzer = Mock()
        mock_analyzer.get_market_context.return_value = {"symbol": "EURUSD"}
        mock_analyzer_class.return_value = mock_analyzer
        
        strategy = AIStrategy({"api_key": "test_key", "confidence_threshold": 0.7})
        signal = strategy.generate_signal("EURUSD")
        
        assert signal == "NONE"  # Should filter out due to low confidence
    
    def test_get_statistics(self):
        """Test getting strategy statistics."""
        from strategies.ai_strategy import AIStrategy
        
        strategy = AIStrategy({"api_key": "test_key"})
        
        # Add some mock decisions
        strategy.decision_history = [
            {"decision": "BUY", "confidence": 0.8},
            {"decision": "SELL", "confidence": 0.75},
            {"decision": "NONE", "confidence": 0.5}
        ]
        
        stats = strategy.get_statistics()
        
        assert stats["total_decisions"] == 3
        assert stats["buy_signals"] == 1
        assert stats["sell_signals"] == 1
        assert stats["hold_signals"] == 1

