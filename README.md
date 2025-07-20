# 🎭 Agent Personality System

Enhance your coding agents with configurable personality traits. Create custom personalities that influence how your AI assistants respond and interact.

## ✨ Features

- **Personality Research**: Automatically research celebrities, fictional characters, and archetypes
- **Context Generation**: Generate LLM-ready personality contexts for coding agents
- **IDE Integration**: Automatically integrate with Cursor, Claude, Windsurf, and other IDEs
- **Web Interface**: User-friendly web interface for creating and managing personalities
- **REST API**: Complete API for programmatic access
- **Caching**: Intelligent caching for improved performance

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ with pip
- Node.js 18+ with npm
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd agent-personality-system
   ```

2. **Set up Python environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e .
   ```

3. **Install frontend dependencies**
   ```bash
   cd web
   npm install
   cd ..
   ```

### 🎯 One-Command Startup

**Option 1: Python Script (Recommended)**
```bash
python start.py
```

**Option 2: Bash Script**
```bash
./start.sh
```

This will start both:
- 🔧 **Backend API** at http://localhost:8000
- 🌐 **Web Interface** at http://localhost:5173

Press `Ctrl+C` to stop all services.

## 🌐 Usage

### Web Interface

1. Open http://localhost:5173 in your browser
2. Enter a personality description (e.g., "Tony Stark", "friendly mentor", "sarcastic genius")
3. Optionally specify your project path for IDE integration
4. Click "Create Personality" to generate the configuration

### API Documentation

Visit http://localhost:8000/docs for interactive API documentation with:
- All available endpoints
- Request/response schemas
- Try-it-out functionality

### Manual Startup (Development)

If you prefer to start services separately:

**Backend API:**
```bash
source .venv/bin/activate
python -c "
import uvicorn
from src.covibe.api.main import app
uvicorn.run(app, host='127.0.0.1', port=8000)
"
```

**Frontend:**
```bash
cd web
npm run dev
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │    │   REST API      │    │  Orchestration  │
│   (React/TS)    │◄──►│   (FastAPI)     │◄──►│   System        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Context Gen    │◄──►│   Research      │
                       │  System         │    │   System        │
                       └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │  IDE Detection  │◄──►│  IDE Writers    │
                       │  System         │    │  System         │
                       └─────────────────┘    └─────────────────┘
```

## 🔧 API Endpoints

### Personality Management
- `POST /api/personality/` - Create personality configuration
- `GET /api/personality/{id}` - Get personality configuration
- `PUT /api/personality/{id}` - Update personality configuration
- `DELETE /api/personality/{id}` - Delete personality configuration

### Research & Utilities
- `POST /api/personality/research` - Research personality only
- `GET /api/personality/ide/detect` - Detect IDE environment
- `GET /api/personality/configs` - List configurations
- `GET /api/personality/cache/stats` - Cache statistics

## 🧪 Testing

**Run all tests:**
```bash
source .venv/bin/activate
python -m pytest
```

**Run specific test suites:**
```bash
# Backend tests
python -m pytest tests/unit/ tests/integration/

# Frontend tests
cd web
npm test
```

## 🛠️ Development

### Project Structure
```
├── src/covibe/           # Backend Python code
│   ├── api/             # FastAPI routes and handlers
│   ├── services/        # Core business logic
│   ├── models/          # Data models and validation
│   └── integrations/    # IDE detection and writers
├── web/                 # Frontend React application
│   ├── src/components/  # React components
│   ├── src/pages/       # Page components
│   ├── src/services/    # API client
│   └── src/types/       # TypeScript types
├── tests/               # Test suites
└── docs/                # Documentation
```

### Adding New IDE Support

1. Add detection logic in `src/covibe/integrations/ide_detection.py`
2. Add writer logic in `src/covibe/integrations/ide_writers.py`
3. Update context generation for IDE-specific formatting
4. Add tests for the new IDE support

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the test suite
5. Submit a pull request

## 📝 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# API Configuration
API_BASE_URL=http://localhost:8000
VITE_API_BASE_URL=http://localhost:8000

# Research Configuration
RESEARCH_CACHE_TTL=24  # hours
MAX_CONCURRENT_REQUESTS=3

# IDE Integration
DEFAULT_IDE_TYPE=cursor
```

### Frontend Configuration

The web interface can be configured via `web/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=Agent Personality System
```

## 🐛 Troubleshooting

### Common Issues

**Port already in use:**
- The startup script will automatically find available ports
- Backend tries port 8000, frontend tries 5173 then finds next available

**Virtual environment issues:**
```bash
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

**Frontend dependency issues:**
```bash
cd web
rm -rf node_modules package-lock.json
npm install
```

**API connection errors:**
- Ensure both frontend and backend are running
- Check that backend is accessible at http://localhost:8000/health
- Verify CORS settings in the API configuration

## 📄 License

[Add your license information here]

## 🤝 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the API documentation at http://localhost:8000/docs
3. Open an issue on the repository

---

**Happy coding with personality! 🎭✨**