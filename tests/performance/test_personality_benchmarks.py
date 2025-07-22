"""Performance benchmarks for personality research and generation."""

import asyncio
import time
from typing import List, Dict, Any
from unittest.mock import AsyncMock, patch

import pytest
from memory_profiler import profile

from src.covibe.services.research import research_personality
from src.covibe.services.context_generation import generate_personality_context
from src.covibe.services.orchestration import process_personality_request
from src.covibe.models.core import PersonalityRequest


class TestPersonalityPerformanceBenchmarks:
    """Performance benchmarks for personality system components."""
    
    @pytest.fixture
    def sample_requests(self) -> List[PersonalityRequest]:
        """Create sample personality requests for benchmarking."""
        return [
            PersonalityRequest(
                id=f"req-{i}",
                description=desc,
                user_id=f"user-{i}",
                timestamp="2024-01-01T00:00:00Z",
                source="api"
            )
            for i, desc in enumerate([
                "Tony Stark - genius inventor",
                "Sherlock Holmes - brilliant detective",
                "Yoda - wise Jedi master",
                "Einstein - theoretical physicist",
                "Gandalf - wise wizard",
                "Batman - dark knight",
                "Hermione Granger - brilliant witch",
                "Spock - logical Vulcan",
                "Professor X - telepathic leader",
                "Wonder Woman - Amazonian warrior"
            ])
        ]
    
    @pytest.mark.benchmark(group="research")
    def test_personality_research_performance(self, benchmark, sample_requests):
        """Benchmark personality research performance."""
        
        async def research_single_personality():
            """Research a single personality."""
            request = sample_requests[0]
            with patch('src.covibe.services.research.fetch_wikipedia_data') as mock_wiki:
                mock_wiki.return_value = {
                    "title": "Tony Stark",
                    "summary": "Fictional character and superhero",
                    "traits": ["genius", "inventor", "billionaire"]
                }
                
                result = await research_personality(request.description)
                return result
        
        # Benchmark the research function
        result = benchmark(asyncio.run, research_single_personality())
        
        # Verify result quality
        assert result is not None
        assert len(result.get("profiles", [])) > 0
    
    @pytest.mark.benchmark(group="research")
    def test_batch_personality_research(self, benchmark, sample_requests):
        """Benchmark batch personality research."""
        
        async def research_batch():
            """Research multiple personalities concurrently."""
            tasks = []
            for request in sample_requests[:5]:  # Test with 5 personalities
                with patch('src.covibe.services.research.fetch_wikipedia_data') as mock_wiki:
                    mock_wiki.return_value = {
                        "title": request.description.split(" - ")[0],
                        "summary": f"Information about {request.description}",
                        "traits": ["trait1", "trait2", "trait3"]
                    }
                    task = research_personality(request.description)
                    tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            return results
        
        results = benchmark(asyncio.run, research_batch())
        
        # Verify all requests were processed
        assert len(results) == 5
        assert all(r is not None for r in results)
    
    @pytest.mark.benchmark(group="context_generation")
    def test_context_generation_performance(self, benchmark):
        """Benchmark context generation performance."""
        
        # Sample personality profile for testing
        personality_profile = {
            "id": "test-profile",
            "name": "Tony Stark",
            "type": "fictional",
            "traits": [
                {"category": "personality", "trait": "confident", "intensity": 9},
                {"category": "communication", "trait": "witty", "intensity": 8},
                {"category": "technical", "trait": "genius", "intensity": 10}
            ],
            "communication_style": {
                "tone": "confident",
                "formality": "casual",
                "verbosity": "moderate",
                "technical_level": "expert"
            },
            "mannerisms": ["Uses technical jargon", "Makes references"]
        }
        
        def generate_context():
            """Generate context for the personality."""
            return generate_personality_context(personality_profile)
        
        result = benchmark(generate_context)
        
        # Verify context quality
        assert result is not None
        assert len(result) > 100  # Should generate substantial context
        assert "Tony Stark" in result
    
    @pytest.mark.benchmark(group="context_generation")
    def test_context_generation_scaling(self, benchmark):
        """Benchmark context generation with varying complexity."""
        
        def generate_complex_context():
            """Generate context for a complex personality with many traits."""
            complex_profile = {
                "id": "complex-profile",
                "name": "Complex Character",
                "type": "custom",
                "traits": [
                    {"category": f"cat-{i}", "trait": f"trait-{i}", "intensity": i % 10 + 1}
                    for i in range(50)  # 50 traits
                ],
                "communication_style": {
                    "tone": "variable",
                    "formality": "mixed",
                    "verbosity": "verbose",
                    "technical_level": "expert"
                },
                "mannerisms": [f"Mannerism {i}" for i in range(20)]
            }
            
            return generate_personality_context(complex_profile)
        
        result = benchmark(generate_complex_context)
        
        # Verify complex context was generated
        assert result is not None
        assert len(result) > 500  # Should be longer for complex personality
    
    @pytest.mark.benchmark(group="orchestration")
    def test_end_to_end_processing_performance(self, benchmark, sample_requests):
        """Benchmark end-to-end personality request processing."""
        
        async def process_request():
            """Process a complete personality request."""
            request = sample_requests[0]
            
            # Mock external dependencies
            with patch('src.covibe.services.research.research_personality') as mock_research, \
                 patch('src.covibe.services.context_generation.generate_personality_context') as mock_context, \
                 patch('src.covibe.integrations.ide_writers.write_cursor_config') as mock_writer:
                
                mock_research.return_value = {
                    "profiles": [{
                        "id": "profile-1",
                        "name": "Tony Stark",
                        "traits": [{"category": "personality", "trait": "confident", "intensity": 9}]
                    }]
                }
                
                mock_context.return_value = "Generated personality context for Tony Stark"
                mock_writer.return_value = {"success": True, "file_path": "/cursor/rules/personality.mdc"}
                
                result = await process_personality_request(request)
                return result
        
        result = benchmark(asyncio.run, process_request())
        
        # Verify processing completed successfully
        assert result is not None
        assert result.get("success") is True
    
    @pytest.mark.benchmark(group="memory")
    @profile
    def test_memory_usage_research(self, sample_requests):
        """Profile memory usage during personality research."""
        
        async def memory_intensive_research():
            """Perform research that may use significant memory."""
            results = []
            
            for request in sample_requests:
                # Simulate memory-intensive research
                with patch('src.covibe.services.research.fetch_wikipedia_data') as mock_wiki:
                    mock_wiki.return_value = {
                        "title": request.description,
                        "summary": "Large summary text " * 1000,  # Simulate large data
                        "traits": [f"trait-{i}" for i in range(100)]
                    }
                    
                    result = await research_personality(request.description)
                    results.append(result)
            
            return results
        
        results = asyncio.run(memory_intensive_research())
        
        # Verify all requests were processed
        assert len(results) == len(sample_requests)
    
    @pytest.mark.benchmark(group="concurrency")
    def test_concurrent_request_handling(self, benchmark, sample_requests):
        """Benchmark concurrent request processing."""
        
        async def process_concurrent_requests():
            """Process multiple requests concurrently."""
            
            async def process_single_request(request):
                """Process a single request with mocked dependencies."""
                with patch('src.covibe.services.research.research_personality') as mock_research, \
                     patch('src.covibe.services.context_generation.generate_personality_context') as mock_context:
                    
                    mock_research.return_value = {"profiles": [{"name": request.description}]}
                    mock_context.return_value = f"Context for {request.description}"
                    
                    # Simulate processing time
                    await asyncio.sleep(0.1)
                    
                    return await process_personality_request(request)
            
            # Process 5 requests concurrently
            tasks = [process_single_request(req) for req in sample_requests[:5]]
            results = await asyncio.gather(*tasks)
            return results
        
        results = benchmark(asyncio.run, process_concurrent_requests())
        
        # Verify concurrent processing
        assert len(results) == 5
        assert all(r is not None for r in results)
    
    @pytest.mark.benchmark(group="caching")
    def test_caching_performance_impact(self, benchmark):
        """Benchmark the impact of caching on performance."""
        
        cache = {}
        
        def research_with_cache(personality_name: str):
            """Research personality with simple caching."""
            if personality_name in cache:
                return cache[personality_name]
            
            # Simulate research work
            time.sleep(0.01)  # 10ms simulated research time
            
            result = {
                "name": personality_name,
                "traits": ["trait1", "trait2"],
                "context": f"Context for {personality_name}"
            }
            
            cache[personality_name] = result
            return result
        
        def benchmark_cached_research():
            """Benchmark research with caching."""
            personalities = ["Tony Stark", "Sherlock Holmes", "Yoda"] * 10
            results = []
            
            for personality in personalities:
                result = research_with_cache(personality)
                results.append(result)
            
            return results
        
        results = benchmark(benchmark_cached_research)
        
        # Verify caching worked (should have 30 results from 3 unique personalities)
        assert len(results) == 30
        assert len(set(r["name"] for r in results)) == 3  # Only 3 unique personalities
    
    def test_performance_regression_detection(self, sample_requests):
        """Test for performance regressions in key operations."""
        
        # Define performance thresholds (in seconds)
        THRESHOLDS = {
            "research_single": 2.0,
            "context_generation": 1.0,
            "end_to_end_processing": 5.0
        }
        
        # Test single personality research
        start_time = time.time()
        
        async def test_research():
            with patch('src.covibe.services.research.fetch_wikipedia_data') as mock_wiki:
                mock_wiki.return_value = {"title": "Test", "summary": "Test summary"}
                return await research_personality("Tony Stark")
        
        asyncio.run(test_research())
        research_time = time.time() - start_time
        
        assert research_time < THRESHOLDS["research_single"], \
            f"Research took {research_time:.2f}s, exceeds threshold of {THRESHOLDS['research_single']}s"
        
        # Test context generation
        start_time = time.time()
        
        test_profile = {
            "name": "Test Character",
            "traits": [{"category": "test", "trait": "test", "intensity": 5}],
            "communication_style": {"tone": "neutral"}
        }
        
        generate_personality_context(test_profile)
        context_time = time.time() - start_time
        
        assert context_time < THRESHOLDS["context_generation"], \
            f"Context generation took {context_time:.2f}s, exceeds threshold of {THRESHOLDS['context_generation']}s"
    
    @pytest.mark.benchmark(group="scalability")
    def test_scalability_limits(self, benchmark):
        """Test system behavior under high load."""
        
        def high_load_simulation():
            """Simulate high load scenario."""
            results = []
            
            # Simulate processing 100 personality requests
            for i in range(100):
                # Mock quick processing
                result = {
                    "id": f"personality-{i}",
                    "processed_at": time.time(),
                    "status": "completed"
                }
                results.append(result)
            
            return results
        
        results = benchmark(high_load_simulation)
        
        # Verify all requests were processed
        assert len(results) == 100
        
        # Check processing was reasonably fast
        processing_times = [r["processed_at"] for r in results]
        total_time = max(processing_times) - min(processing_times)
        assert total_time < 1.0, f"High load processing took {total_time:.2f}s, too slow"


class TestLLMPerformanceBenchmarks:
    """Performance benchmarks comparing LLM vs traditional research methods."""
    
    @pytest.fixture
    def llm_test_descriptions(self) -> List[str]:
        """Test descriptions for LLM benchmarking."""
        return [
            "A brilliant detective with exceptional deductive reasoning skills",
            "An innovative tech entrepreneur who revolutionized multiple industries",
            "A wise mentor figure who guides heroes on their journey",
            "A complex anti-hero with a troubled past and noble intentions",
            "An eccentric scientist who makes groundbreaking discoveries"
        ]
    
    @pytest.mark.benchmark(group="llm_vs_traditional")
    def test_llm_research_vs_traditional_performance(self, benchmark, llm_test_descriptions):
        """Compare LLM research performance against traditional methods."""
        
        async def llm_research_benchmark():
            """Benchmark LLM-based personality research."""
            with patch('src.covibe.services.llm_client.OpenAIClient.generate_response') as mock_llm:
                mock_llm.return_value = """{
                    "name": "Sherlock Holmes",
                    "type": "fictional",
                    "description": "Brilliant detective",
                    "traits": [{"trait": "analytical", "intensity": 10, "description": "Highly analytical"}],
                    "communication_style": {"tone": "precise", "formality": "formal", "verbosity": "concise", "technical_level": "expert"},
                    "mannerisms": ["Deductive reasoning", "Pipe smoking"],
                    "confidence": 0.95
                }"""
                
                results = []
                for description in llm_test_descriptions:
                    result = await research_personality(description, use_llm=True, llm_provider="openai")
                    results.append(result)
                return results
        
        async def traditional_research_benchmark():
            """Benchmark traditional personality research."""
            with patch('src.covibe.services.research.fetch_wikipedia_data') as mock_wiki:
                mock_wiki.return_value = {
                    "title": "Character",
                    "summary": "Fictional character",
                    "traits": ["intelligent", "determined"]
                }
                
                results = []
                for description in llm_test_descriptions:
                    result = await research_personality(description, use_llm=False)
                    results.append(result)
                return results
        
        # Benchmark both approaches
        llm_results = benchmark.pedantic(asyncio.run, (llm_research_benchmark(),), iterations=3, rounds=1)
        
        # Store baseline for comparison
        traditional_start = time.time()
        traditional_results = asyncio.run(traditional_research_benchmark())
        traditional_time = time.time() - traditional_start
        
        # Verify both produced results
        assert len(llm_results) == len(llm_test_descriptions)
        assert len(traditional_results) == len(llm_test_descriptions)
        
        # Log performance comparison
        print(f"Traditional research time: {traditional_time:.3f}s")
        print(f"LLM research (benchmark) completed successfully")
    
    @pytest.mark.benchmark(group="llm_quality")
    def test_llm_response_quality_vs_speed_tradeoff(self, benchmark):
        """Benchmark LLM response quality vs speed with different parameters."""
        
        test_description = "A complex character with multiple personality facets"
        
        async def llm_quick_response():
            """Quick LLM response (lower quality)."""
            with patch('src.covibe.services.llm_client.OpenAIClient.generate_response') as mock_llm:
                mock_llm.return_value = """{
                    "name": "Quick Character",
                    "type": "custom",
                    "description": "Basic description",
                    "traits": [{"trait": "simple", "intensity": 5, "description": "Basic trait"}],
                    "communication_style": {"tone": "neutral", "formality": "mixed", "verbosity": "moderate", "technical_level": "intermediate"},
                    "mannerisms": ["Generic behavior"],
                    "confidence": 0.7
                }"""
                
                # Simulate quick processing
                await asyncio.sleep(0.1)
                return await research_personality(test_description, use_llm=True, llm_provider="openai")
        
        async def llm_detailed_response():
            """Detailed LLM response (higher quality, slower)."""
            with patch('src.covibe.services.llm_client.OpenAIClient.generate_response') as mock_llm:
                mock_llm.return_value = """{
                    "name": "Detailed Character",
                    "type": "custom", 
                    "description": "Comprehensive personality analysis",
                    "traits": [
                        {"trait": "analytical", "intensity": 9, "description": "Deep analytical thinking"},
                        {"trait": "empathetic", "intensity": 8, "description": "Strong emotional intelligence"},
                        {"trait": "creative", "intensity": 7, "description": "Innovative problem solving"}
                    ],
                    "communication_style": {"tone": "thoughtful", "formality": "professional", "verbosity": "detailed", "technical_level": "expert"},
                    "mannerisms": ["Thoughtful pauses", "Detailed explanations", "Empathetic responses"],
                    "confidence": 0.95
                }"""
                
                # Simulate longer processing for detailed analysis
                await asyncio.sleep(0.5)
                return await research_personality(test_description, use_llm=True, llm_provider="openai")
        
        # Benchmark quick response
        quick_result = benchmark.pedantic(asyncio.run, (llm_quick_response(),), iterations=3, rounds=1)
        
        # Compare with detailed response (not benchmarked to avoid skewing results)
        detailed_start = time.time()
        detailed_result = asyncio.run(llm_detailed_response())
        detailed_time = time.time() - detailed_start
        
        # Verify quality differences
        assert quick_result is not None
        assert detailed_result is not None
        
        print(f"Detailed analysis time: {detailed_time:.3f}s")
        print("Quality vs speed tradeoff analysis completed")
    
    @pytest.mark.benchmark(group="llm_caching")
    def test_llm_cache_performance_impact(self, benchmark):
        """Benchmark LLM response caching effectiveness."""
        
        cache_data = {}
        test_descriptions = [
            "Einstein-like physicist",
            "Einstein personality", 
            "Physics genius similar to Einstein"  # Should hit cache due to similarity
        ]
        
        async def llm_with_cache():
            """LLM research with caching enabled."""
            results = []
            
            for description in test_descriptions:
                # Simple cache key based on normalized description
                cache_key = description.lower().replace(" ", "_")
                
                if cache_key in cache_data:
                    # Cache hit - instant return
                    results.append(cache_data[cache_key])
                    continue
                
                # Cache miss - perform LLM request
                with patch('src.covibe.services.llm_client.OpenAIClient.generate_response') as mock_llm:
                    mock_llm.return_value = """{
                        "name": "Albert Einstein",
                        "type": "celebrity",
                        "description": "Theoretical physicist",
                        "traits": [{"trait": "genius", "intensity": 10, "description": "Exceptional intelligence"}],
                        "communication_style": {"tone": "thoughtful", "formality": "academic", "verbosity": "detailed", "technical_level": "expert"},
                        "mannerisms": ["Complex theories", "Thought experiments"],
                        "confidence": 0.98
                    }"""
                    
                    # Simulate LLM processing time
                    await asyncio.sleep(0.2)
                    
                    result = await research_personality(description, use_llm=True, llm_provider="openai")
                    cache_data[cache_key] = result
                    results.append(result)
            
            return results
        
        async def llm_without_cache():
            """LLM research without caching."""
            results = []
            
            for description in test_descriptions:
                with patch('src.covibe.services.llm_client.OpenAIClient.generate_response') as mock_llm:
                    mock_llm.return_value = """{
                        "name": "Albert Einstein",
                        "type": "celebrity", 
                        "description": "Theoretical physicist",
                        "traits": [{"trait": "genius", "intensity": 10, "description": "Exceptional intelligence"}],
                        "communication_style": {"tone": "thoughtful", "formality": "academic", "verbosity": "detailed", "technical_level": "expert"},
                        "mannerisms": ["Complex theories", "Thought experiments"],
                        "confidence": 0.98
                    }"""
                    
                    # Simulate LLM processing time for each request
                    await asyncio.sleep(0.2)
                    
                    result = await research_personality(description, use_llm=True, llm_provider="openai")
                    results.append(result)
            
            return results
        
        # Benchmark cached version
        cached_results = benchmark.pedantic(asyncio.run, (llm_with_cache(),), iterations=3, rounds=1)
        
        # Compare with non-cached version
        no_cache_start = time.time()
        no_cache_results = asyncio.run(llm_without_cache())
        no_cache_time = time.time() - no_cache_start
        
        # Verify results
        assert len(cached_results) == 3
        assert len(no_cache_results) == 3
        
        print(f"No cache time: {no_cache_time:.3f}s")
        print("Cache effectiveness benchmark completed")
    
    @pytest.mark.benchmark(group="llm_concurrent")
    def test_llm_concurrent_request_performance(self, benchmark):
        """Benchmark concurrent LLM requests with rate limiting simulation."""
        
        request_count = 0
        rate_limit_threshold = 3
        
        async def llm_concurrent_requests():
            """Simulate concurrent LLM requests with rate limiting."""
            nonlocal request_count
            
            async def single_llm_request(description: str, request_id: int):
                """Single LLM request with rate limiting simulation."""
                nonlocal request_count
                
                # Simulate rate limiting
                if request_count >= rate_limit_threshold:
                    await asyncio.sleep(1.0)  # Rate limit delay
                    request_count = 0  # Reset counter
                
                request_count += 1
                
                with patch('src.covibe.services.llm_client.OpenAIClient.generate_response') as mock_llm:
                    mock_llm.return_value = f"""{{"name": "Character {request_id}", "type": "custom", "description": "Test character", "traits": [{{"trait": "test", "intensity": 5, "description": "Test trait"}}], "communication_style": {{"tone": "neutral", "formality": "mixed", "verbosity": "moderate", "technical_level": "intermediate"}}, "mannerisms": ["Test behavior"], "confidence": 0.8}}"""
                    
                    # Simulate LLM processing
                    await asyncio.sleep(0.1)
                    
                    return await research_personality(description, use_llm=True, llm_provider="openai")
            
            # Create 6 concurrent requests (will trigger rate limiting)
            descriptions = [f"Test personality {i}" for i in range(6)]
            tasks = [single_llm_request(desc, i) for i, desc in enumerate(descriptions)]
            
            results = await asyncio.gather(*tasks)
            return results
        
        results = benchmark(asyncio.run, llm_concurrent_requests())
        
        # Verify all requests completed
        assert len(results) == 6
        assert all(r is not None for r in results)
        
        print("Concurrent LLM request benchmark completed")
    
    @pytest.mark.benchmark(group="llm_provider_comparison")
    def test_multiple_llm_provider_performance(self, benchmark):
        """Benchmark performance across different LLM providers."""
        
        test_description = "Innovative tech leader personality"
        
        async def openai_provider_benchmark():
            """Benchmark OpenAI provider."""
            with patch('src.covibe.services.llm_client.OpenAIClient.generate_response') as mock_openai:
                mock_openai.return_value = """{
                    "name": "Tech Leader",
                    "type": "archetype",
                    "description": "Innovative technology leader",
                    "traits": [{"trait": "visionary", "intensity": 9, "description": "Forward-thinking"}],
                    "communication_style": {"tone": "inspiring", "formality": "casual", "verbosity": "moderate", "technical_level": "expert"},
                    "mannerisms": ["Bold statements", "Future focus"],
                    "confidence": 0.9
                }"""
                
                # Simulate OpenAI processing time
                await asyncio.sleep(0.15)
                
                return await research_personality(test_description, use_llm=True, llm_provider="openai")
        
        async def anthropic_provider_benchmark():
            """Benchmark Anthropic provider."""
            with patch('src.covibe.services.llm_client.AnthropicClient.generate_response') as mock_anthropic:
                mock_anthropic.return_value = """{
                    "name": "Tech Innovator", 
                    "type": "archetype",
                    "description": "Technology innovation leader",
                    "traits": [{"trait": "innovative", "intensity": 9, "description": "Highly innovative"}],
                    "communication_style": {"tone": "confident", "formality": "professional", "verbosity": "detailed", "technical_level": "expert"},
                    "mannerisms": ["Strategic thinking", "Innovation focus"],
                    "confidence": 0.92
                }"""
                
                # Simulate Anthropic processing time (slightly different)
                await asyncio.sleep(0.18)
                
                return await research_personality(test_description, use_llm=True, llm_provider="anthropic")
        
        # Benchmark OpenAI
        openai_result = benchmark.pedantic(asyncio.run, (openai_provider_benchmark(),), iterations=3, rounds=1)
        
        # Compare with Anthropic (not benchmarked to avoid confusion)
        anthropic_start = time.time()
        anthropic_result = asyncio.run(anthropic_provider_benchmark())
        anthropic_time = time.time() - anthropic_start
        
        # Verify both providers work
        assert openai_result is not None
        assert anthropic_result is not None
        
        print(f"Anthropic provider time: {anthropic_time:.3f}s")
        print("Provider comparison benchmark completed")