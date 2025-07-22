"""Cost optimization features for LLM usage."""

import time
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import re

try:
    import tiktoken  # For OpenAI token counting
except ImportError:
    tiktoken = None

from ..utils.monitoring import performance_monitor


@dataclass
class TokenUsage:
    """Token usage statistics for a request."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    provider: str
    model: str
    timestamp: datetime


@dataclass
class CostThreshold:
    """Cost threshold configuration."""
    daily_limit: float = 10.0  # Daily cost limit in USD
    hourly_limit: float = 2.0  # Hourly cost limit in USD
    request_limit: float = 0.50  # Per request cost limit in USD


class CostTracker:
    """Track and manage LLM usage costs."""
    
    def __init__(self, thresholds: Optional[CostThreshold] = None):
        """Initialize cost tracker.
        
        Args:
            thresholds: Cost threshold configuration
        """
        self.thresholds = thresholds or CostThreshold()
        self.usage_history: List[TokenUsage] = []
        self._lock = asyncio.Lock()
    
    async def record_usage(self, usage: TokenUsage) -> None:
        """Record token usage for cost tracking.
        
        Args:
            usage: Token usage information
        """
        async with self._lock:
            self.usage_history.append(usage)
            # Keep only last 24 hours of history
            cutoff = datetime.now() - timedelta(hours=24)
            self.usage_history = [
                u for u in self.usage_history
                if u.timestamp > cutoff
            ]
    
    async def get_costs(
        self,
        time_window: Optional[timedelta] = None
    ) -> Dict[str, float]:
        """Get cost statistics for a time window.
        
        Args:
            time_window: Time window for cost calculation (default: last hour)
            
        Returns:
            Dictionary with cost statistics
        """
        if not time_window:
            time_window = timedelta(hours=1)
        
        cutoff = datetime.now() - time_window
        
        async with self._lock:
            relevant_usage = [
                u for u in self.usage_history
                if u.timestamp > cutoff
            ]
        
        total_cost = sum(u.estimated_cost for u in relevant_usage)
        total_tokens = sum(u.total_tokens for u in relevant_usage)
        
        # Cost by provider
        provider_costs = {}
        for usage in relevant_usage:
            provider_costs[usage.provider] = provider_costs.get(usage.provider, 0) + usage.estimated_cost
        
        return {
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "provider_costs": provider_costs,
            "request_count": len(relevant_usage),
            "time_window_hours": time_window.total_seconds() / 3600
        }
    
    async def check_thresholds(self) -> Dict[str, Any]:
        """Check if usage is approaching or exceeding thresholds.
        
        Returns:
            Dictionary with threshold status and warnings
        """
        warnings = []
        exceeded = []
        
        # Check hourly limit
        hourly_costs = await self.get_costs(timedelta(hours=1))
        if hourly_costs["total_cost"] > self.thresholds.hourly_limit:
            exceeded.append(f"Hourly limit exceeded: ${hourly_costs['total_cost']:.2f} > ${self.thresholds.hourly_limit}")
        elif hourly_costs["total_cost"] > self.thresholds.hourly_limit * 0.8:
            warnings.append(f"Approaching hourly limit: ${hourly_costs['total_cost']:.2f} (80% of ${self.thresholds.hourly_limit})")
        
        # Check daily limit
        daily_costs = await self.get_costs(timedelta(hours=24))
        if daily_costs["total_cost"] > self.thresholds.daily_limit:
            exceeded.append(f"Daily limit exceeded: ${daily_costs['total_cost']:.2f} > ${self.thresholds.daily_limit}")
        elif daily_costs["total_cost"] > self.thresholds.daily_limit * 0.8:
            warnings.append(f"Approaching daily limit: ${daily_costs['total_cost']:.2f} (80% of ${self.thresholds.daily_limit})")
        
        return {
            "warnings": warnings,
            "exceeded": exceeded,
            "hourly_cost": hourly_costs["total_cost"],
            "daily_cost": daily_costs["total_cost"],
            "within_limits": len(exceeded) == 0
        }


# Pricing information for different providers (per 1K tokens)
PRICING = {
    "openai": {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
    },
    "anthropic": {
        "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
    },
    "local": {
        # Local models are free
        "*": {"input": 0.0, "output": 0.0}
    }
}


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens in text for the given model.
    
    Args:
        text: Text to count tokens for
        model: Model name for accurate token counting
        
    Returns:
        Estimated token count
    """
    if tiktoken and model.startswith("gpt"):
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except Exception:
            # Fall back to simple estimation
            pass
    
    # Simple approximation: 4 characters per token on average
    return len(text) // 4


def estimate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    provider: str,
    model: str
) -> float:
    """Estimate cost for token usage.
    
    Args:
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens
        provider: LLM provider name
        model: Model name
        
    Returns:
        Estimated cost in USD
    """
    # Get pricing for provider/model
    provider_pricing = PRICING.get(provider, {})
    model_pricing = provider_pricing.get(model)
    
    if not model_pricing:
        # Try wildcard pricing for local models
        model_pricing = provider_pricing.get("*")
    
    if not model_pricing:
        # Unknown provider/model - return 0 cost
        return 0.0
    
    input_cost = (prompt_tokens / 1000) * model_pricing["input"]
    output_cost = (completion_tokens / 1000) * model_pricing["output"]
    
    return input_cost + output_cost


def optimize_prompt_length(prompt: str, max_tokens: int = 2000) -> str:
    """Optimize prompt length to reduce token usage.
    
    Args:
        prompt: Original prompt text
        max_tokens: Maximum allowed tokens
        
    Returns:
        Optimized prompt text
    """
    current_tokens = count_tokens(prompt)
    
    # Always apply basic optimizations
    optimized = prompt
    
    # Remove extra whitespace
    optimized = re.sub(r'\s+', ' ', optimized.strip())
    
    # Remove redundant phrases
    redundant_phrases = [
        "Please note that",
        "It's important to",
        "You should be aware that",
        "Keep in mind that",
        "Remember that",
        "It's worth noting that"
    ]
    
    for phrase in redundant_phrases:
        optimized = optimized.replace(phrase, "")
    
    # Clean up any double spaces that might have been created
    optimized = re.sub(r'\s+', ' ', optimized.strip())
    
    # If still too long after basic optimizations, truncate from the middle
    if count_tokens(optimized) > max_tokens:
        words = optimized.split()
        target_words = int(len(words) * (max_tokens / current_tokens))
        
        if target_words < len(words):
            # Keep first and last portions
            keep_start = target_words // 2
            keep_end = target_words - keep_start
            
            optimized = ' '.join(words[:keep_start] + ['...'] + words[-keep_end:])
    
    return optimized


def normalize_query_for_similarity(query: str) -> str:
    """Normalize query for similarity comparison.
    
    Args:
        query: Original query text
        
    Returns:
        Normalized query text
    """
    # Convert to lowercase
    normalized = query.lower().strip()
    
    # Remove punctuation and extra spaces
    normalized = re.sub(r'[^\w\s]', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Sort words for better matching
    words = sorted(normalized.split())
    
    return ' '.join(words)


def calculate_query_similarity(query1: str, query2: str) -> float:
    """Calculate similarity between two queries for cache optimization.
    
    Args:
        query1: First query
        query2: Second query
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    # Normalize queries
    norm1 = normalize_query_for_similarity(query1)
    norm2 = normalize_query_for_similarity(query2)
    
    if not norm1 or not norm2:
        return 0.0
    
    # Calculate word-level similarity
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    # Jaccard similarity
    jaccard = len(intersection) / len(union)
    
    # Length similarity (prefer similar length queries)
    len_diff = abs(len(words1) - len(words2))
    max_len = max(len(words1), len(words2))
    len_similarity = 1.0 - (len_diff / max_len) if max_len > 0 else 1.0
    
    # Combined similarity (weighted average)
    return 0.7 * jaccard + 0.3 * len_similarity


def generate_query_hash(query: str, include_variations: bool = True) -> str:
    """Generate hash for query that can match similar queries.
    
    Args:
        query: Query text
        include_variations: Whether to include common variations
        
    Returns:
        Query hash for similarity matching
    """
    normalized = normalize_query_for_similarity(query)
    
    if include_variations:
        # Generate variations for better cache hits
        variations = [
            normalized,
            normalized.replace("personality", "character"),
            normalized.replace("character", "personality"),
            normalized.replace("like", "similar to"),
            normalized.replace("similar to", "like")
        ]
        
        # Use shortest variation for consistency
        normalized = min(variations, key=len)
    
    return hashlib.sha256(normalized.encode()).hexdigest()


@performance_monitor("cost_optimization", "optimization")
async def optimize_llm_request(
    prompt: str,
    max_tokens: int = 1000,
    cost_tracker: Optional[CostTracker] = None,
    provider: str = "openai",
    model: str = "gpt-4"
) -> Dict[str, Any]:
    """Optimize LLM request for cost and performance.
    
    Args:
        prompt: Original prompt text
        max_tokens: Maximum completion tokens
        cost_tracker: Cost tracker instance
        provider: LLM provider
        model: Model name
        
    Returns:
        Optimization results and recommendations
    """
    # Check cost thresholds if tracker is available
    threshold_status = None
    if cost_tracker:
        threshold_status = await cost_tracker.check_thresholds()
        if not threshold_status["within_limits"]:
            return {
                "proceed": False,
                "reason": "Cost thresholds exceeded",
                "threshold_status": threshold_status,
                "recommendations": [
                    "Wait for cost limits to reset",
                    "Use a cheaper model or provider",
                    "Reduce prompt complexity"
                ]
            }
    
    # Optimize prompt length
    optimized_prompt = optimize_prompt_length(prompt, max_tokens // 2)  # Reserve half for completion
    prompt_tokens = count_tokens(optimized_prompt, model)
    
    # Estimate cost
    estimated_cost = estimate_cost(prompt_tokens, max_tokens, provider, model)
    
    # Generate recommendations
    recommendations = []
    
    if len(optimized_prompt) < len(prompt):
        recommendations.append(f"Prompt optimized: reduced from {len(prompt)} to {len(optimized_prompt)} chars")
    
    if estimated_cost > 0.10:  # High cost request
        recommendations.extend([
            f"High cost request: ~${estimated_cost:.3f}",
            "Consider using a cheaper model",
            "Consider caching similar responses"
        ])
    
    # Check if we should proceed
    proceed = True
    if cost_tracker and estimated_cost > cost_tracker.thresholds.request_limit:
        proceed = False
        recommendations.append(f"Request exceeds per-request limit: ${estimated_cost:.3f} > ${cost_tracker.thresholds.request_limit}")
    
    return {
        "proceed": proceed,
        "optimized_prompt": optimized_prompt,
        "estimated_cost": estimated_cost,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": max_tokens,
        "threshold_status": threshold_status,
        "recommendations": recommendations,
        "optimization_applied": len(optimized_prompt) < len(prompt)
    }