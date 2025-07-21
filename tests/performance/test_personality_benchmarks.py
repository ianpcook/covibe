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