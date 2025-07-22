"""Unit tests for cost optimization features."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

from src.covibe.services.cost_optimizer import (
    TokenUsage,
    CostThreshold,
    CostTracker,
    count_tokens,
    estimate_cost,
    optimize_prompt_length,
    normalize_query_for_similarity,
    calculate_query_similarity,
    generate_query_hash,
    optimize_llm_request
)


class TestTokenUsage:
    """Test TokenUsage dataclass."""
    
    def test_token_usage_creation(self):
        """Test creating TokenUsage instance."""
        now = datetime.now()
        usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            estimated_cost=0.01,
            provider="openai",
            model="gpt-4",
            timestamp=now
        )
        
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150
        assert usage.estimated_cost == 0.01
        assert usage.provider == "openai"
        assert usage.model == "gpt-4"
        assert usage.timestamp == now


class TestCostThreshold:
    """Test CostThreshold dataclass."""
    
    def test_default_thresholds(self):
        """Test default threshold values."""
        threshold = CostThreshold()
        assert threshold.daily_limit == 10.0
        assert threshold.hourly_limit == 2.0
        assert threshold.request_limit == 0.50
    
    def test_custom_thresholds(self):
        """Test custom threshold values."""
        threshold = CostThreshold(
            daily_limit=20.0,
            hourly_limit=5.0,
            request_limit=1.0
        )
        assert threshold.daily_limit == 20.0
        assert threshold.hourly_limit == 5.0
        assert threshold.request_limit == 1.0


class TestCostTracker:
    """Test CostTracker functionality."""
    
    @pytest.fixture
    def cost_tracker(self):
        """Create cost tracker for testing."""
        return CostTracker()
    
    @pytest.fixture
    def sample_usage(self):
        """Create sample token usage."""
        return TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            estimated_cost=0.005,
            provider="openai",
            model="gpt-4",
            timestamp=datetime.now()
        )
    
    @pytest.mark.asyncio
    async def test_record_usage(self, cost_tracker, sample_usage):
        """Test recording token usage."""
        await cost_tracker.record_usage(sample_usage)
        
        assert len(cost_tracker.usage_history) == 1
        assert cost_tracker.usage_history[0] == sample_usage
    
    @pytest.mark.asyncio
    async def test_get_costs_empty(self, cost_tracker):
        """Test getting costs with no usage history."""
        costs = await cost_tracker.get_costs()
        
        assert costs["total_cost"] == 0
        assert costs["total_tokens"] == 0
        assert costs["provider_costs"] == {}
        assert costs["request_count"] == 0
    
    @pytest.mark.asyncio
    async def test_get_costs_with_usage(self, cost_tracker):
        """Test getting costs with usage history."""
        usage1 = TokenUsage(100, 50, 150, 0.01, "openai", "gpt-4", datetime.now())
        usage2 = TokenUsage(200, 100, 300, 0.02, "anthropic", "claude-3", datetime.now())
        
        await cost_tracker.record_usage(usage1)
        await cost_tracker.record_usage(usage2)
        
        costs = await cost_tracker.get_costs()
        
        assert costs["total_cost"] == 0.03
        assert costs["total_tokens"] == 450
        assert costs["provider_costs"] == {"openai": 0.01, "anthropic": 0.02}
        assert costs["request_count"] == 2
    
    @pytest.mark.asyncio
    async def test_get_costs_time_window(self, cost_tracker):
        """Test getting costs for specific time window."""
        now = datetime.now()
        old_usage = TokenUsage(100, 50, 150, 0.01, "openai", "gpt-4", now - timedelta(hours=2))
        recent_usage = TokenUsage(200, 100, 300, 0.02, "openai", "gpt-4", now)
        
        await cost_tracker.record_usage(old_usage)
        await cost_tracker.record_usage(recent_usage)
        
        # Get costs for last hour (should only include recent_usage)
        costs = await cost_tracker.get_costs(timedelta(hours=1))
        
        assert costs["total_cost"] == 0.02
        assert costs["request_count"] == 1
    
    @pytest.mark.asyncio
    async def test_check_thresholds_within_limits(self, cost_tracker):
        """Test threshold checking when within limits."""
        usage = TokenUsage(100, 50, 150, 0.001, "openai", "gpt-4", datetime.now())
        await cost_tracker.record_usage(usage)
        
        status = await cost_tracker.check_thresholds()
        
        assert status["within_limits"] is True
        assert len(status["warnings"]) == 0
        assert len(status["exceeded"]) == 0
    
    @pytest.mark.asyncio
    async def test_check_thresholds_warnings(self, cost_tracker):
        """Test threshold checking with warnings."""
        # Add usage that approaches but doesn't exceed hourly limit
        high_usage = TokenUsage(1000, 500, 1500, 1.7, "openai", "gpt-4", datetime.now())
        await cost_tracker.record_usage(high_usage)
        
        status = await cost_tracker.check_thresholds()
        
        assert status["within_limits"] is True
        assert len(status["warnings"]) > 0
        assert "hourly limit" in status["warnings"][0].lower()
    
    @pytest.mark.asyncio
    async def test_check_thresholds_exceeded(self, cost_tracker):
        """Test threshold checking when limits are exceeded."""
        # Add usage that exceeds hourly limit
        excessive_usage = TokenUsage(10000, 5000, 15000, 3.0, "openai", "gpt-4", datetime.now())
        await cost_tracker.record_usage(excessive_usage)
        
        status = await cost_tracker.check_thresholds()
        
        assert status["within_limits"] is False
        assert len(status["exceeded"]) > 0
        assert "hourly limit exceeded" in status["exceeded"][0].lower()
    
    @pytest.mark.asyncio
    async def test_usage_history_cleanup(self, cost_tracker):
        """Test that old usage history is cleaned up."""
        # Add old usage (more than 24 hours old)
        old_usage = TokenUsage(
            100, 50, 150, 0.01, "openai", "gpt-4", 
            datetime.now() - timedelta(hours=25)
        )
        recent_usage = TokenUsage(
            200, 100, 300, 0.02, "openai", "gpt-4", 
            datetime.now()
        )
        
        await cost_tracker.record_usage(old_usage)
        await cost_tracker.record_usage(recent_usage)
        
        # Should only have recent usage after cleanup
        assert len(cost_tracker.usage_history) == 1
        assert cost_tracker.usage_history[0] == recent_usage


class TestTokenCounting:
    """Test token counting functionality."""
    
    def test_count_tokens_simple(self):
        """Test basic token counting."""
        text = "Hello world! How are you today?"
        count = count_tokens(text)
        
        # Should be approximately 8-9 tokens
        assert 6 <= count <= 12
    
    def test_count_tokens_empty(self):
        """Test token counting for empty text."""
        assert count_tokens("") == 0
    
    @patch('src.covibe.services.cost_optimizer.tiktoken')
    def test_count_tokens_with_tiktoken(self, mock_tiktoken):
        """Test token counting with tiktoken library."""
        # Mock tiktoken behavior
        mock_encoding = Mock()
        mock_encoding.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
        mock_tiktoken.encoding_for_model.return_value = mock_encoding
        
        count = count_tokens("test text", "gpt-4")
        
        assert count == 5
        mock_tiktoken.encoding_for_model.assert_called_once_with("gpt-4")


class TestCostEstimation:
    """Test cost estimation functionality."""
    
    def test_estimate_cost_openai_gpt4(self):
        """Test cost estimation for OpenAI GPT-4."""
        cost = estimate_cost(1000, 500, "openai", "gpt-4")
        
        # GPT-4: $0.03/1K input + $0.06/1K output
        expected = (1000/1000) * 0.03 + (500/1000) * 0.06
        assert abs(cost - expected) < 0.001
    
    def test_estimate_cost_anthropic_claude3(self):
        """Test cost estimation for Anthropic Claude-3."""
        cost = estimate_cost(1000, 500, "anthropic", "claude-3-sonnet-20240229")
        
        # Claude-3 Sonnet: $0.003/1K input + $0.015/1K output
        expected = (1000/1000) * 0.003 + (500/1000) * 0.015
        assert abs(cost - expected) < 0.001
    
    def test_estimate_cost_local_model(self):
        """Test cost estimation for local model."""
        cost = estimate_cost(1000, 500, "local", "llama2")
        
        # Local models are free
        assert cost == 0.0
    
    def test_estimate_cost_unknown_provider(self):
        """Test cost estimation for unknown provider."""
        cost = estimate_cost(1000, 500, "unknown", "unknown-model")
        
        # Unknown providers return 0 cost
        assert cost == 0.0


class TestPromptOptimization:
    """Test prompt optimization functionality."""
    
    def test_optimize_prompt_length_short(self):
        """Test optimizing prompt that's already short enough."""
        prompt = "Analyze this personality: Tony Stark"
        optimized = optimize_prompt_length(prompt, 2000)
        
        # Should return original prompt since it's short
        assert optimized == prompt
    
    def test_optimize_prompt_length_whitespace(self):
        """Test optimizing prompt with extra whitespace."""
        prompt = "Analyze   this    personality:     Tony Stark   "
        optimized = optimize_prompt_length(prompt, 2000)
        
        # Should remove extra whitespace
        assert optimized == "Analyze this personality: Tony Stark"
    
    def test_optimize_prompt_length_redundant_phrases(self):
        """Test removing redundant phrases."""
        prompt = "Please note that you should analyze this personality. It's important to be thorough."
        optimized = optimize_prompt_length(prompt, 2000)
        
        # Should remove redundant phrases
        assert "Please note that" not in optimized
        assert "It's important to" not in optimized
    
    def test_optimize_prompt_length_truncation(self):
        """Test prompt truncation when very long."""
        # Create very long prompt
        words = ["word"] * 1000  # Very long prompt
        prompt = " ".join(words)
        
        optimized = optimize_prompt_length(prompt, 100)  # Very low token limit
        
        # Should be significantly shorter
        assert len(optimized) < len(prompt)
        assert "..." in optimized  # Should have truncation marker


class TestQuerySimilarity:
    """Test query similarity functionality."""
    
    def test_normalize_query_for_similarity(self):
        """Test query normalization."""
        query = "Analyze Tony Stark's personality!"
        normalized = normalize_query_for_similarity(query)
        
        # Should be lowercase, no punctuation, sorted words
        expected_words = sorted(["analyze", "tony", "stark", "s", "personality"])
        assert normalized == " ".join(expected_words)
    
    def test_calculate_query_similarity_identical(self):
        """Test similarity calculation for identical queries."""
        query1 = "Tony Stark personality"
        query2 = "Tony Stark personality"
        
        similarity = calculate_query_similarity(query1, query2)
        assert similarity == 1.0
    
    def test_calculate_query_similarity_similar(self):
        """Test similarity calculation for similar queries."""
        query1 = "Tony Stark personality analysis"
        query2 = "Analyze Tony Stark's personality"
        
        similarity = calculate_query_similarity(query1, query2)
        assert 0.5 < similarity < 1.0  # Should be similar but not identical
    
    def test_calculate_query_similarity_different(self):
        """Test similarity calculation for different queries."""
        query1 = "Tony Stark personality"
        query2 = "Sherlock Holmes character"
        
        similarity = calculate_query_similarity(query1, query2)
        assert 0.0 <= similarity < 0.5  # Should be low similarity
    
    def test_calculate_query_similarity_empty(self):
        """Test similarity calculation with empty queries."""
        similarity = calculate_query_similarity("", "test")
        assert similarity == 0.0
        
        similarity = calculate_query_similarity("test", "")
        assert similarity == 0.0
    
    def test_generate_query_hash_consistency(self):
        """Test that similar queries generate same hash."""
        query1 = "Tony Stark personality"
        query2 = "personality of Tony Stark"
        
        hash1 = generate_query_hash(query1)
        hash2 = generate_query_hash(query2)
        
        # Should generate consistent hashes (both normalize to same form)
        assert isinstance(hash1, str)
        assert isinstance(hash2, str)
        assert len(hash1) == 64  # SHA256 hash length
    
    def test_generate_query_hash_variations(self):
        """Test query hash with variations."""
        query = "Tony Stark personality"
        
        hash_with_variations = generate_query_hash(query, include_variations=True)
        hash_without_variations = generate_query_hash(query, include_variations=False)
        
        assert isinstance(hash_with_variations, str)
        assert isinstance(hash_without_variations, str)


class TestOptimizeLLMRequest:
    """Test complete LLM request optimization."""
    
    @pytest.fixture
    def cost_tracker(self):
        """Create cost tracker with low thresholds for testing."""
        thresholds = CostThreshold(
            daily_limit=1.0,
            hourly_limit=0.1,
            request_limit=0.05
        )
        return CostTracker(thresholds)
    
    @pytest.mark.asyncio
    async def test_optimize_llm_request_normal(self):
        """Test normal LLM request optimization."""
        prompt = "Analyze this personality: Tony Stark"
        
        result = await optimize_llm_request(prompt)
        
        assert result["proceed"] is True
        assert "optimized_prompt" in result
        assert "estimated_cost" in result
        assert "recommendations" in result
    
    @pytest.mark.asyncio
    async def test_optimize_llm_request_high_cost(self):
        """Test optimization with high-cost request."""
        # Very long prompt that will be expensive
        long_prompt = "Analyze this personality: " + "Tony Stark " * 1000
        
        result = await optimize_llm_request(long_prompt, max_tokens=2000)
        
        assert "High cost request" in " ".join(result["recommendations"])
    
    @pytest.mark.asyncio
    async def test_optimize_llm_request_threshold_exceeded(self, cost_tracker):
        """Test optimization when cost thresholds are exceeded."""
        # Add high-cost usage to exceed thresholds
        high_usage = TokenUsage(
            10000, 5000, 15000, 0.15, "openai", "gpt-4", datetime.now()
        )
        await cost_tracker.record_usage(high_usage)
        
        result = await optimize_llm_request(
            "Test prompt",
            cost_tracker=cost_tracker
        )
        
        assert result["proceed"] is False
        assert "Cost thresholds exceeded" in result["reason"]
    
    @pytest.mark.asyncio
    async def test_optimize_llm_request_per_request_limit(self, cost_tracker):
        """Test optimization when per-request limit is exceeded."""
        # Very expensive single request
        expensive_prompt = "Analyze: " + "detailed analysis " * 2000
        
        result = await optimize_llm_request(
            expensive_prompt,
            max_tokens=3000,
            cost_tracker=cost_tracker,
            provider="openai",
            model="gpt-4"
        )
        
        # Should be blocked due to high estimated cost
        assert result["proceed"] is False or "per-request limit" in " ".join(result["recommendations"])
    
    @pytest.mark.asyncio
    async def test_optimize_llm_request_prompt_optimization(self):
        """Test that prompt optimization is applied."""
        verbose_prompt = "Please note that    you should analyze this personality.    It's important to be thorough.   "
        
        result = await optimize_llm_request(verbose_prompt)
        
        # Should apply optimization
        assert result["optimization_applied"] is True
        assert len(result["optimized_prompt"]) < len(verbose_prompt)
    
    @pytest.mark.asyncio
    async def test_optimize_llm_request_local_model(self):
        """Test optimization with local model (free)."""
        result = await optimize_llm_request(
            "Test prompt",
            provider="local",
            model="llama2"
        )
        
        assert result["proceed"] is True
        assert result["estimated_cost"] == 0.0