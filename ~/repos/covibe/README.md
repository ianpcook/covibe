# Covibe - Agent Personality System

A tool that enhances existing coding agents by adding configurable personality traits to their responses.

## Overview

Covibe accepts personality descriptions from users through multiple interfaces (web, API, chat), researches the requested personality type, and generates contextual prompts that can be integrated into various IDE environments to influence how coding agents respond to users.

## Features

- Multiple input methods (web interface, REST API, chat)
- Automatic personality research for celebrities, authors, fictional characters, and archetypes
- Context generation for LLM integration
- IDE-specific file persistence (Cursor, Claude, Windsurf, and others)
- Flexible personality input handling

## Development

This project follows functional programming principles with modern Python best practices:

- Pure functions and immutable data structures
- Full type hints with Pydantic models
- Async/await patterns throughout
- Comprehensive testing with pytest

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd covibe

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Start development server
uvicorn src.covibe.main:app --reload
```

## Project Structure

```
src/covibe/
├── models/         # Pydantic data models
├── api/           # FastAPI routes and handlers
├── services/      # Core business logic
├── integrations/  # IDE-specific writers
└── utils/         # Shared utilities
```