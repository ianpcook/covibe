"""Playwright configuration and fixtures for E2E tests."""

import asyncio
import subprocess
import time
from typing import AsyncGenerator, Generator

import pytest
from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def playwright() -> AsyncGenerator[Playwright, None]:
    """Start Playwright."""
    async with async_playwright() as p:
        yield p


@pytest.fixture(scope="session")
async def browser(playwright: Playwright) -> AsyncGenerator[Browser, None]:
    """Launch browser for testing."""
    browser = await playwright.chromium.launch(headless=True)
    yield browser
    await browser.close()


@pytest.fixture
async def context(browser: Browser) -> AsyncGenerator[BrowserContext, None]:
    """Create a new browser context for each test."""
    context = await browser.new_context()
    yield context
    await context.close()


@pytest.fixture
async def page(context: BrowserContext) -> AsyncGenerator[Page, None]:
    """Create a new page for each test."""
    page = await context.new_page()
    yield page
    await page.close()


@pytest.fixture(scope="session")
def backend_server():
    """Start the backend server for E2E tests."""
    # Start the backend server
    process = subprocess.Popen(
        ["python", "-m", "uvicorn", "src.covibe.api.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    # Wait for server to start
    time.sleep(3)
    
    yield "http://127.0.0.1:8000"
    
    # Cleanup
    process.terminate()
    process.wait()


@pytest.fixture(scope="session")
def frontend_server():
    """Start the frontend server for E2E tests."""
    # Build frontend first
    subprocess.run(["npm", "run", "build"], cwd="web", check=True)
    
    # Start the frontend server
    process = subprocess.Popen(
        ["npm", "run", "preview", "--", "--port", "3000"],
        cwd="web",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    # Wait for server to start
    time.sleep(5)
    
    yield "http://127.0.0.1:3000"
    
    # Cleanup
    process.terminate()
    process.wait()


@pytest.fixture
def base_url(frontend_server):
    """Base URL for the application."""
    return frontend_server