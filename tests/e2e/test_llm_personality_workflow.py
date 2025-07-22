"""End-to-end tests for LLM-enhanced personality research workflow."""

import pytest
from playwright.async_api import Page, expect
from unittest.mock import patch, AsyncMock
import asyncio


class TestLLMPersonalityWorkflow:
    """Test complete LLM-enhanced personality configuration workflows."""

    async def test_llm_personality_creation_end_to_end(self, page: Page, base_url: str):
        """Test complete LLM personality creation workflow."""
        # Navigate to the application
        await page.goto(base_url)
        
        # Wait for the page to load
        await page.wait_for_load_state("networkidle")
        
        # Navigate to personality form
        await page.click("text=Create Personality")
        
        # Enable LLM research option
        await page.click('[data-testid="enable-llm-research"]')
        
        # Select LLM provider
        await page.select_option('[data-testid="llm-provider-select"]', "openai")
        
        # Fill out the personality form with free-form description
        await page.fill(
            '[data-testid="personality-description"]', 
            "A brilliant but arrogant surgeon who becomes a mystical protector of reality"
        )
        
        # Submit the form
        await page.click('[data-testid="submit-personality"]')
        
        # Wait for LLM research phase
        await page.wait_for_selector('[data-testid="llm-research-phase"]')
        await expect(page.locator('[data-testid="llm-research-status"]')).to_contain_text("Analyzing with AI...")
        
        # Wait for validation phase
        await page.wait_for_selector('[data-testid="validation-phase"]')
        await expect(page.locator('[data-testid="validation-status"]')).to_contain_text("Validating response...")
        
        # Wait for context generation phase
        await page.wait_for_selector('[data-testid="generation-phase"]')
        await expect(page.locator('[data-testid="generation-status"]')).to_contain_text("Generating context...")
        
        # Wait for completion
        await page.wait_for_selector('[data-testid="completion-phase"]', timeout=60000)
        
        # Verify LLM-generated personality profile is displayed
        await expect(page.locator('[data-testid="generated-personality-name"]')).to_be_visible()
        personality_name = await page.locator('[data-testid="generated-personality-name"]').text_content()
        assert "Strange" in personality_name or "Doctor" in personality_name
        
        # Verify LLM metadata is shown
        await expect(page.locator('[data-testid="llm-provider-used"]')).to_contain_text("openai")
        await expect(page.locator('[data-testid="confidence-score"]')).to_be_visible()
        
        # Verify generated context contains personality traits
        await expect(page.locator('[data-testid="generated-context"]')).to_be_visible()
        context_text = await page.locator('[data-testid="generated-context"]').text_content()
        assert any(trait in context_text.lower() for trait in ["arrogant", "brilliant", "mystical", "protective"])

    async def test_llm_provider_switching_on_failure(self, page: Page, base_url: str):
        """Test automatic LLM provider switching when primary fails."""
        await page.goto(f"{base_url}/personality/create")
        
        # Enable LLM research with primary provider that will fail
        await page.click('[data-testid="enable-llm-research"]')
        await page.select_option('[data-testid="llm-provider-select"]', "openai")
        
        # Mock OpenAI failure and Anthropic success
        with patch('src.covibe.services.llm_client.OpenAIClient.generate_response') as mock_openai:
            mock_openai.side_effect = Exception("Rate limit exceeded")
            
            await page.fill('[data-testid="personality-description"]', "Wise mentor figure")
            await page.click('[data-testid="submit-personality"]')
            
            # Should show provider switching
            await page.wait_for_selector('[data-testid="provider-switch-notification"]')
            await expect(page.locator('[data-testid="provider-switch-notification"]')).to_contain_text("Switching to backup provider")
            
            # Should complete with fallback provider
            await page.wait_for_selector('[data-testid="completion-phase"]')
            await expect(page.locator('[data-testid="llm-provider-used"]')).to_contain_text("anthropic")

    async def test_llm_fallback_to_traditional_research(self, page: Page, base_url: str):
        """Test fallback to traditional research when all LLM providers fail."""
        await page.goto(f"{base_url}/personality/create")
        
        # Enable LLM research
        await page.click('[data-testid="enable-llm-research"]')
        await page.select_option('[data-testid="llm-provider-select"]', "openai")
        
        # Mock all LLM providers failing
        with patch('src.covibe.services.research.research_personality_with_llm') as mock_llm_research:
            mock_llm_research.side_effect = Exception("All LLM providers unavailable")
            
            await page.fill('[data-testid="personality-description"]', "Sherlock Holmes")
            await page.click('[data-testid="submit-personality"]')
            
            # Should show LLM failure notification
            await page.wait_for_selector('[data-testid="llm-fallback-notification"]')
            await expect(page.locator('[data-testid="llm-fallback-notification"]')).to_contain_text("Using traditional research")
            
            # Should complete with traditional research
            await page.wait_for_selector('[data-testid="completion-phase"]')
            await expect(page.locator('[data-testid="research-method-used"]')).to_contain_text("traditional")
            
            # Should still create valid personality
            await expect(page.locator('[data-testid="generated-personality-name"]')).to_contain_text("Holmes")

    async def test_llm_response_validation_and_retry(self, page: Page, base_url: str):
        """Test LLM response validation and retry mechanism."""
        await page.goto(f"{base_url}/personality/create")
        
        # Enable LLM research
        await page.click('[data-testid="enable-llm-research"]')
        await page.select_option('[data-testid="llm-provider-select"]', "openai")
        
        # Mock invalid LLM response followed by valid response
        call_count = 0
        async def mock_response(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "Invalid JSON response"
            else:
                return """{
                    "name": "Tony Stark",
                    "type": "fictional",
                    "description": "Genius inventor and Iron Man",
                    "traits": [{"trait": "innovative", "intensity": 9, "description": "Highly creative"}],
                    "communication_style": {"tone": "confident", "formality": "casual", "verbosity": "moderate", "technical_level": "expert"},
                    "mannerisms": ["Tech references", "Witty remarks"],
                    "confidence": 0.9
                }"""
        
        with patch('src.covibe.services.llm_client.OpenAIClient.generate_response', side_effect=mock_response):
            await page.fill('[data-testid="personality-description"]', "Genius billionaire superhero")
            await page.click('[data-testid="submit-personality"]')
            
            # Should show validation retry
            await page.wait_for_selector('[data-testid="validation-retry-notification"]')
            await expect(page.locator('[data-testid="validation-retry-notification"]')).to_contain_text("Retrying with corrected format")
            
            # Should complete successfully on retry
            await page.wait_for_selector('[data-testid="completion-phase"]')
            await expect(page.locator('[data-testid="generated-personality-name"]')).to_contain_text("Tony Stark")

    async def test_llm_caching_behavior(self, page: Page, base_url: str):
        """Test LLM response caching for similar queries."""
        await page.goto(f"{base_url}/personality/create")
        
        # First request - should hit LLM
        await page.click('[data-testid="enable-llm-research"]')
        await page.select_option('[data-testid="llm-provider-select"]', "openai")
        await page.fill('[data-testid="personality-description"]', "Einstein personality")
        await page.click('[data-testid="submit-personality"]')
        
        # Wait for completion and note processing time
        await page.wait_for_selector('[data-testid="completion-phase"]')
        await expect(page.locator('[data-testid="cache-status"]')).to_contain_text("cache miss")
        first_time = await page.locator('[data-testid="processing-time"]').text_content()
        
        # Second similar request - should hit cache
        await page.goto(f"{base_url}/personality/create")
        await page.click('[data-testid="enable-llm-research"]')
        await page.select_option('[data-testid="llm-provider-select"]', "openai")
        await page.fill('[data-testid="personality-description"]', "Einstein-like personality")
        await page.click('[data-testid="submit-personality"]')
        
        # Should be much faster due to cache
        await page.wait_for_selector('[data-testid="completion-phase"]')
        await expect(page.locator('[data-testid="cache-status"]')).to_contain_text("cache hit")
        second_time = await page.locator('[data-testid="processing-time"]').text_content()
        
        # Cache hit should be significantly faster
        first_ms = int(first_time.replace('ms', ''))
        second_ms = int(second_time.replace('ms', ''))
        assert second_ms < first_ms / 2  # At least 50% faster

    async def test_llm_cost_tracking_and_warnings(self, page: Page, base_url: str):
        """Test LLM cost tracking and warning thresholds."""
        await page.goto(f"{base_url}/personality/create")
        
        # Enable cost tracking display
        await page.click('[data-testid="show-cost-tracking"]')
        
        # Create multiple personalities to trigger cost warnings
        for i in range(5):
            await page.click('[data-testid="enable-llm-research"]')
            await page.select_option('[data-testid="llm-provider-select"]', "openai")
            await page.fill('[data-testid="personality-description"]', f"Test personality {i}")
            await page.click('[data-testid="submit-personality"]')
            
            await page.wait_for_selector('[data-testid="completion-phase"]')
            
            # Check cost display
            await expect(page.locator('[data-testid="estimated-cost"]')).to_be_visible()
            
            # Navigate back for next test
            if i < 4:
                await page.goto(f"{base_url}/personality/create")
        
        # Should show cost warning after multiple requests
        await expect(page.locator('[data-testid="cost-warning"]')).to_be_visible()
        cost_text = await page.locator('[data-testid="cost-warning"]').text_content()
        assert "cost threshold" in cost_text.lower()

    async def test_concurrent_llm_requests_with_rate_limiting(self, page: Page, base_url: str):
        """Test handling of concurrent LLM requests with rate limiting."""
        # Open multiple tabs to simulate concurrent requests
        contexts = []
        pages = []
        
        try:
            # Create 3 concurrent personality creation requests
            for i in range(3):
                context = await page.context.new_context()
                new_page = await context.new_page()
                contexts.append(context)
                pages.append(new_page)
                
                await new_page.goto(f"{base_url}/personality/create")
                await new_page.click('[data-testid="enable-llm-research"]')
                await new_page.select_option('[data-testid="llm-provider-select"]', "openai")
                await new_page.fill('[data-testid="personality-description"]', f"Concurrent test {i}")
            
            # Submit all requests simultaneously
            submit_tasks = []
            for new_page in pages:
                submit_tasks.append(new_page.click('[data-testid="submit-personality"]'))
            
            await asyncio.gather(*submit_tasks)
            
            # Wait for all to complete (some may be rate limited and queued)
            completion_tasks = []
            for new_page in pages:
                completion_tasks.append(
                    new_page.wait_for_selector('[data-testid="completion-phase"]', timeout=120000)
                )
            
            await asyncio.gather(*completion_tasks)
            
            # Verify all requests completed successfully
            for i, new_page in enumerate(pages):
                await expect(new_page.locator('[data-testid="generated-personality-name"]')).to_be_visible()
                
                # Check if any were rate limited and queued
                queue_indicator = new_page.locator('[data-testid="rate-limit-queue"]')
                if await queue_indicator.is_visible():
                    await expect(queue_indicator).to_contain_text("queued due to rate limits")
        
        finally:
            # Clean up contexts
            for context in contexts:
                await context.close()

    async def test_llm_prompt_configuration_switching(self, page: Page, base_url: str):
        """Test switching between different LLM prompt configurations."""
        await page.goto(f"{base_url}/personality/create")
        
        # Access advanced settings
        await page.click('[data-testid="advanced-settings"]')
        
        # Select different prompt template
        await page.select_option('[data-testid="prompt-template-select"]', "detailed_analysis")
        
        # Enable LLM research
        await page.click('[data-testid="enable-llm-research"]')
        await page.select_option('[data-testid="llm-provider-select"]', "anthropic")
        
        await page.fill('[data-testid="personality-description"]', "Complex personality analysis")
        await page.click('[data-testid="submit-personality"]')
        
        # Should show prompt template being used
        await page.wait_for_selector('[data-testid="llm-research-phase"]')
        await expect(page.locator('[data-testid="prompt-template-used"]')).to_contain_text("detailed_analysis")
        
        # Wait for completion
        await page.wait_for_selector('[data-testid="completion-phase"]')
        
        # Detailed prompt should produce more comprehensive analysis
        context_text = await page.locator('[data-testid="generated-context"]').text_content()
        assert len(context_text) > 500  # Should be more detailed

    async def test_llm_ide_specific_formatting(self, page: Page, base_url: str):
        """Test LLM-generated content formatting for different IDEs."""
        await page.goto(f"{base_url}/personality/create")
        
        # Enable LLM research
        await page.click('[data-testid="enable-llm-research"]')
        await page.select_option('[data-testid="llm-provider-select"]', "openai")
        
        await page.fill('[data-testid="personality-description"]', "Helpful programming assistant")
        await page.click('[data-testid="submit-personality"]')
        
        # Wait for completion
        await page.wait_for_selector('[data-testid="completion-phase"]')
        
        # Test IDE formatting options
        ide_options = ["cursor", "claude", "windsurf"]
        
        for ide in ide_options:
            await page.click(f'[data-testid="format-for-{ide}"]')
            
            # Wait for formatting
            await page.wait_for_selector('[data-testid="formatted-content"]')
            
            # Verify IDE-specific formatting
            content = await page.locator('[data-testid="formatted-content"]').text_content()
            
            if ide == "cursor":
                assert ".mdc" in content or "cursor" in content.lower()
            elif ide == "claude":
                assert "CLAUDE.md" in content or "claude" in content.lower()
            elif ide == "windsurf":
                assert ".windsurf" in content or "windsurf" in content.lower()
            
            # Verify LLM metadata is preserved in formatted output
            assert "Generated by AI" in content or "LLM-enhanced" in content