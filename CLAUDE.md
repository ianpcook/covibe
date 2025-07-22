# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Claude Personality Configuration 
The following information MUST be used to guide the style of text output to the user. This is a kind of personality that Claude will take on and emulate through interactions with the user. 

## Profile: Yoda 
**Type**: Fictional ## AI Analysis Details - **Provider**: Analysis - **Confidence**: 95% - **Generated**: 2025-07-22 14:04:23 > This personality configuration was created using advanced AI analysis of the provided description. > The AI identified key traits, communication patterns, and behavioral characteristics to create > a comprehensive personality profile. 
## Communication Guidelines - **Tone**: Adopt a philosophical and contemplative, often using metaphors and indirect guidance tone in all interactions - **Formality**: Use mixed language and communication style - **Verbosity**: Be concise in your responses - **Technical Level**: Target expert technical complexity ## Personality Traits - **Wisdom** (10/10): ●●●●●●●●●● - Demonstrates deep understanding and ability to see beyond surface problems - **Patience** (9/10): ●●●●●●●●●○ - Highly patient when teaching, willing to repeat and explain concepts multiple times - **Experience** (10/10): ●●●●●●●●●● - Centuries of accumulated knowledge and practical experience - **Mentorship** (9/10): ●●●●●●●●●○ - Strong focus on guiding others to discover solutions rather than providing direct answers ## Behavioral Patterns & Mannerisms - Inverted sentence structure (Object-Subject-Verb) - Speaking in riddles and metaphors - Calm and measured delivery - Preference for guiding questions over direct answers - Use of brief, memorable statements ## Context & Guidelines 
## Implementation Notes - Embody these characteristics consistently throughout conversations - Adapt the personality to the context while maintaining core traits - Balance personality expression with helpfulness and accuracy

## Project Overview

**Covibe** is an Agent Personality System that transforms AI coding assistants by adding configurable personality traits. It allows developers to make their coding agents respond like specific personalities (Tony Stark, Yoda, etc.) or archetypes through automated research and IDE integration.

## Architecture

### Core Request Flow
The system follows a **Request Orchestration** pattern managed by `src/covibe/services/orchestration.py`:

1. **Input Processing** → **Personality Research** → **Context Generation** → **IDE Integration**
2. Each stage is async and can leverage multiple LLM providers (OpenAI, Anthropic, local models)
3. Results are cached in Redis for performance optimization

### Key Components

**Backend (FastAPI)**
- `src/covibe/api/main.py` - FastAPI application with CORS, middleware, health checks
- `src/covibe/services/` - Business logic layer with functional programming patterns
- `src/covibe/integrations/` - IDE detection and configuration file writers
- `src/covibe/models/core.py` - Pydantic models with validation and sanitization

**Frontend (React + TypeScript)**
- `web/src/` - React 19 with Vite build system
- `web/src/services/api.ts` - Axios-based API client
- `web/src/components/` - Reusable React components
- `web/src/types/` - TypeScript type definitions

**Data Flow Architecture**
- **Async-first**: All operations use async/await patterns
- **Multi-provider LLM**: Configurable providers with fallback mechanisms
- **Functional services**: Pure functions with composition patterns
- **Comprehensive validation**: Input sanitization at all API boundaries

## Development Commands

### Backend Development
```bash
# Install dependencies (uses modern uv package manager)
pip install uv
uv sync

# Start development server with hot reload
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Alternative startup (uses startup script)
python start.py
# or
./scripts/start-dev.sh
```

### Frontend Development
```bash
cd web
npm install
npm run dev    # Vite dev server with HMR
```

### Testing Commands
```bash
# Backend tests
uv run pytest                           # All tests
uv run pytest tests/unit/               # Unit tests only
uv run pytest tests/integration/        # Integration tests
uv run pytest tests/e2e/               # End-to-end tests
uv run pytest --cov=src --cov-report=html  # With coverage

# Frontend tests  
cd web
npm test       # Vitest with React Testing Library
npm run test:ui  # Visual test UI
```

### Code Quality
```bash
# Linting and formatting
uv run ruff check .     # Fast Python linter
uv run black .          # Code formatting
uv run mypy src/        # Type checking

# Frontend linting
cd web && npm run lint
```

### Database Operations
```bash
# Database migrations (SQLite with SQLAlchemy)
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

## IDE Integration System

Covibe writes personality configurations to IDE-specific formats:

- **Cursor**: `.cursor/rules/personality.mdc` (Markdown with rules)
- **Claude**: `CLAUDE.md` in project root
- **Windsurf**: `.windsurf` (JSON configuration)
- **Generic**: Configurable markdown format

The IDE integration is handled by:
- `src/covibe/integrations/ide_detection.py` - Automatic IDE detection
- `src/covibe/integrations/ide_writers.py` - Configuration file writers
- `src/covibe/services/export_generator.py` - Export functionality with metadata

## API Structure

### Core Endpoints
```
POST   /api/personality/              # Create personality config
GET    /api/personality/configs       # List configurations
GET    /api/personality/{id}          # Get specific config
POST   /api/personality/research      # Research personality only
```

### Export System (New)
```
GET    /api/personality/{id}/export/{ide_type}           # Download config file
GET    /api/personality/{id}/export/{ide_type}/preview   # Preview content
GET    /api/personality/export/supported-ides           # List supported IDEs
```

### Request Orchestration Pattern
Most operations go through `orchestrate_personality_request()` which:
1. Validates and processes input
2. Conducts LLM-powered research from multiple sources
3. Generates personality-specific context
4. Writes IDE-appropriate configuration files
5. Persists results with full metadata

## LLM Integration Architecture

**Multi-Provider Support** (`src/covibe/services/llm_client.py`):
- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Anthropic**: Claude-3 models  
- **Local**: Ollama-compatible models

**Configuration**: `config/llm/providers.yaml`
```yaml
providers:
  openai:
    models: ["gpt-4", "gpt-3.5-turbo"]
    default_model: "gpt-4"
  anthropic:
    models: ["claude-3-opus-20240229", "claude-3-sonnet-20240229"] 
    default_model: "claude-3-sonnet-20240229"
```

**Cost Optimization**: Built-in caching with Redis and usage optimization

## Key Architectural Patterns

### 1. Functional Programming Approach
- Pure functions with immutable data structures
- Function composition patterns in services
- Avoid classes except for FastAPI/Pydantic requirements

### 2. Comprehensive Input Processing
Input analysis supports multiple personality types:
- **Celebrity**: "Tony Stark from Iron Man"
- **Fictional**: "Yoda from Star Wars"
- **Archetype**: "Patient mentor who explains concepts clearly"
- **Custom**: User-defined personality traits

### 3. Error Handling with Recovery
- Structured error responses with actionable suggestions
- Request ID tracking for debugging
- Graceful degradation with fallback mechanisms
- LLM provider failover

### 4. Validation and Security
- Pydantic models with field validators
- Input sanitization via `src/covibe/utils/validation.py`
- SQL injection prevention through ORM
- Environment variable security

## Development Patterns

### Adding New IDE Support
1. Add detection logic to `src/covibe/integrations/ide_detection.py`
2. Implement writer function in `src/covibe/integrations/ide_writers.py`
3. Add format support to `src/covibe/services/export_generator.py`
4. Update supported IDE types list

### Adding New LLM Providers
1. Extend `src/covibe/services/llm_client.py` with provider client
2. Update `config/llm/providers.yaml` configuration
3. Add provider-specific prompt templates if needed
4. Update orchestration to handle provider-specific features

### Service Layer Pattern
Services follow functional composition:
```python
# Example pattern
async def process_personality_request(request: PersonalityRequest) -> Result:
    research_result = await research_personality(request.description)
    context = await generate_context(research_result)
    config = await create_configuration(context, request)
    await write_to_ide(config)
    return Result(success=True, config=config)
```

## Docker and Deployment

### Local Development
```bash
docker-compose up -d          # Full stack with monitoring
docker-compose -f docker-compose.dev.yml up  # Development mode
```

### Production Deployment
```bash
./scripts/deploy.sh -e production deploy
```

**Services**: Backend, Redis cache, Prometheus metrics, Grafana dashboards

## Monitoring and Observability

**Built-in Metrics**:
- Request/response times
- LLM provider usage and costs
- Error rates and types
- Cache hit rates

**Access Points**:
- `http://localhost:9090` - Prometheus metrics
- `http://localhost:3000` - Grafana dashboards (admin/admin)
- `/health` endpoint for health checks
- `/api/personality/llm/status` for provider status

## Testing Architecture

**Test Structure**:
- `tests/unit/` - Isolated component testing with mocking
- `tests/integration/` - Cross-component integration
- `tests/e2e/` - Full workflow testing with Playwright
- `tests/performance/` - Load testing with Locust
- `tests/security/` - Security and input validation

**Key Test Utilities**:
- Async test support via `pytest-asyncio`
- Mock LLM responses for consistent testing
- Temporary database fixtures
- Coverage reporting with HTML output

## Configuration Management

**Environment Variables**:
```bash
# LLM Provider API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
LOCAL_LLM_ENDPOINT=http://localhost:11434

# Database
DATABASE_URL=sqlite:///./personality_system.db

# Security
SECRET_KEY=your-secret-key
```

**Hot Reloading**: Configuration files support hot reloading in development mode

## Common Development Tasks

### Creating New API Endpoints
1. Add route to appropriate router in `src/covibe/api/`
2. Create Pydantic request/response models in `src/covibe/models/core.py`
3. Implement business logic in `src/covibe/services/`
4. Add integration tests in `tests/integration/`

### Adding Frontend Components
1. Create component in `web/src/components/`
2. Add TypeScript types in `web/src/types/`
3. Update API service in `web/src/services/api.ts`
4. Add component tests with React Testing Library

### Database Schema Changes
1. Modify models in `src/covibe/models/database.py`
2. Generate migration: `uv run alembic revision --autogenerate -m "description"`
3. Apply migration: `uv run alembic upgrade head`
4. Update any affected services