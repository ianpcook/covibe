"""End-to-end tests for personality configuration workflow."""

import pytest
from playwright.async_api import Page, expect


class TestPersonalityWorkflow:
    """Test complete personality configuration workflows."""

    async def test_create_personality_via_web_form(self, page: Page, base_url: str):
        """Test creating a personality configuration through the web form."""
        # Navigate to the application
        await page.goto(base_url)
        
        # Wait for the page to load
        await page.wait_for_load_state("networkidle")
        
        # Check if we're on the home page
        await expect(page.locator("h1")).to_contain_text("Agent Personality System")
        
        # Navigate to personality form
        await page.click("text=Create Personality")
        
        # Fill out the personality form
        await page.fill('[data-testid="personality-description"]', "Tony Stark - genius, billionaire, playboy, philanthropist")
        
        # Submit the form
        await page.click('[data-testid="submit-personality"]')
        
        # Wait for processing
        await page.wait_for_selector('[data-testid="processing-indicator"]')
        await page.wait_for_selector('[data-testid="success-message"]', timeout=30000)
        
        # Verify success message
        await expect(page.locator('[data-testid="success-message"]')).to_be_visible()
        
        # Verify personality was created
        await expect(page.locator('[data-testid="personality-name"]')).to_contain_text("Tony Stark")

    async def test_personality_research_and_generation(self, page: Page, base_url: str):
        """Test the personality research and context generation process."""
        await page.goto(f"{base_url}/personality/create")
        
        # Test with a well-known fictional character
        await page.fill('[data-testid="personality-description"]', "Sherlock Holmes")
        await page.click('[data-testid="submit-personality"]')
        
        # Wait for research phase
        await page.wait_for_selector('[data-testid="research-phase"]')
        await expect(page.locator('[data-testid="research-status"]')).to_contain_text("Researching personality...")
        
        # Wait for context generation phase
        await page.wait_for_selector('[data-testid="generation-phase"]')
        await expect(page.locator('[data-testid="generation-status"]')).to_contain_text("Generating context...")
        
        # Wait for completion
        await page.wait_for_selector('[data-testid="completion-phase"]')
        
        # Verify generated context is displayed
        await expect(page.locator('[data-testid="generated-context"]')).to_be_visible()
        context_text = await page.locator('[data-testid="generated-context"]').text_content()
        assert "deductive" in context_text.lower() or "analytical" in context_text.lower()

    async def test_ide_integration_selection(self, page: Page, base_url: str):
        """Test IDE integration options and file generation."""
        await page.goto(f"{base_url}/personality/create")
        
        # Create a personality
        await page.fill('[data-testid="personality-description"]', "Yoda - wise Jedi master")
        await page.click('[data-testid="submit-personality"]')
        
        # Wait for completion
        await page.wait_for_selector('[data-testid="completion-phase"]')
        
        # Test IDE selection
        await page.click('[data-testid="ide-selection"]')
        
        # Verify IDE options are available
        await expect(page.locator('[data-testid="cursor-option"]')).to_be_visible()
        await expect(page.locator('[data-testid="claude-option"]')).to_be_visible()
        await expect(page.locator('[data-testid="windsurf-option"]')).to_be_visible()
        
        # Select Cursor IDE
        await page.click('[data-testid="cursor-option"]')
        
        # Verify file content is generated
        await expect(page.locator('[data-testid="file-content"]')).to_be_visible()
        file_content = await page.locator('[data-testid="file-content"]').text_content()
        assert "Yoda" in file_content

    async def test_personality_management_dashboard(self, page: Page, base_url: str):
        """Test the personality management dashboard functionality."""
        await page.goto(f"{base_url}/dashboard")
        
        # Create a test personality first
        await page.click('[data-testid="create-new-personality"]')
        await page.fill('[data-testid="personality-description"]', "Einstein - brilliant physicist")
        await page.click('[data-testid="submit-personality"]')
        await page.wait_for_selector('[data-testid="success-message"]')
        
        # Navigate back to dashboard
        await page.goto(f"{base_url}/dashboard")
        
        # Verify personality appears in dashboard
        await expect(page.locator('[data-testid="personality-card"]')).to_be_visible()
        await expect(page.locator('[data-testid="personality-name"]')).to_contain_text("Einstein")
        
        # Test edit functionality
        await page.click('[data-testid="edit-personality"]')
        await page.fill('[data-testid="personality-description"]', "Einstein - theoretical physicist and philosopher")
        await page.click('[data-testid="save-changes"]')
        
        # Verify changes were saved
        await expect(page.locator('[data-testid="personality-description"]')).to_contain_text("philosopher")
        
        # Test delete functionality
        await page.click('[data-testid="delete-personality"]')
        await page.click('[data-testid="confirm-delete"]')
        
        # Verify personality was deleted
        await expect(page.locator('[data-testid="personality-card"]')).not_to_be_visible()

    async def test_chat_interface_workflow(self, page: Page, base_url: str):
        """Test the chat interface for personality configuration."""
        await page.goto(f"{base_url}/chat")
        
        # Wait for chat interface to load
        await page.wait_for_selector('[data-testid="chat-input"]')
        
        # Send a personality request via chat
        await page.fill('[data-testid="chat-input"]', "I want my agent to be like Gandalf the Grey")
        await page.click('[data-testid="send-message"]')
        
        # Wait for response
        await page.wait_for_selector('[data-testid="chat-response"]')
        
        # Verify bot understood the request
        response_text = await page.locator('[data-testid="chat-response"]').last.text_content()
        assert "Gandalf" in response_text
        
        # Continue conversation to refine personality
        await page.fill('[data-testid="chat-input"]', "Make him more patient and less cryptic")
        await page.click('[data-testid="send-message"]')
        
        # Wait for refined response
        await page.wait_for_selector('[data-testid="chat-response"]')
        
        # Confirm personality configuration
        await page.fill('[data-testid="chat-input"]', "Yes, that looks good")
        await page.click('[data-testid="send-message"]')
        
        # Wait for configuration completion
        await page.wait_for_selector('[data-testid="configuration-complete"]')
        
        # Verify personality was configured
        await expect(page.locator('[data-testid="configuration-complete"]')).to_contain_text("configured successfully")

    async def test_error_handling_and_recovery(self, page: Page, base_url: str):
        """Test error handling and recovery mechanisms."""
        await page.goto(f"{base_url}/personality/create")
        
        # Test with invalid input
        await page.fill('[data-testid="personality-description"]', "")
        await page.click('[data-testid="submit-personality"]')
        
        # Verify validation error
        await expect(page.locator('[data-testid="validation-error"]')).to_be_visible()
        await expect(page.locator('[data-testid="validation-error"]')).to_contain_text("required")
        
        # Test with ambiguous personality
        await page.fill('[data-testid="personality-description"]', "xyz123nonexistent")
        await page.click('[data-testid="submit-personality"]')
        
        # Wait for research to complete
        await page.wait_for_selector('[data-testid="research-error"]', timeout=15000)
        
        # Verify error message and suggestions
        await expect(page.locator('[data-testid="research-error"]')).to_be_visible()
        await expect(page.locator('[data-testid="suggestions"]')).to_be_visible()
        
        # Test recovery by selecting a suggestion
        await page.click('[data-testid="suggestion-item"]')
        
        # Verify recovery worked
        await page.wait_for_selector('[data-testid="success-message"]')

    async def test_cross_browser_compatibility(self, page: Page, base_url: str):
        """Test basic functionality across different browsers."""
        # This test runs with the configured browser in conftest.py
        # Additional browsers can be tested by parameterizing the browser fixture
        
        await page.goto(base_url)
        
        # Test basic navigation
        await expect(page.locator("h1")).to_be_visible()
        
        # Test form interaction
        await page.click("text=Create Personality")
        await expect(page.locator('[data-testid="personality-description"]')).to_be_visible()
        
        # Test responsive design (mobile viewport)
        await page.set_viewport_size({"width": 375, "height": 667})
        await expect(page.locator('[data-testid="mobile-menu"]')).to_be_visible()
        
        # Test desktop viewport
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await expect(page.locator('[data-testid="desktop-nav"]')).to_be_visible()

    async def test_accessibility_compliance(self, page: Page, base_url: str):
        """Test accessibility compliance of the web interface."""
        await page.goto(base_url)
        
        # Test keyboard navigation
        await page.keyboard.press("Tab")
        focused_element = await page.evaluate("document.activeElement.tagName")
        assert focused_element in ["A", "BUTTON", "INPUT"]
        
        # Test ARIA labels
        create_button = page.locator('[data-testid="create-personality"]')
        aria_label = await create_button.get_attribute("aria-label")
        assert aria_label is not None
        
        # Test color contrast (basic check)
        background_color = await page.evaluate(
            "getComputedStyle(document.body).backgroundColor"
        )
        assert background_color is not None
        
        # Test alt text for images
        images = page.locator("img")
        count = await images.count()
        for i in range(count):
            alt_text = await images.nth(i).get_attribute("alt")
            assert alt_text is not None and alt_text.strip() != ""