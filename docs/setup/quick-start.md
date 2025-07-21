# Quick Start Guide

Get up and running with Covibe in under 5 minutes!

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher (for web interface)
- Git

## Installation Options

### Option 1: Docker (Recommended)

The fastest way to get started is with Docker:

```bash
# Clone the repository
git clone https://github.com/covibe/covibe.git
cd covibe

# Start with Docker Compose
docker-compose up -d

# Access the web interface
open http://localhost:80
```

### Option 2: Local Development

For development or customization:

```bash
# Clone the repository
git clone https://github.com/covibe/covibe.git
cd covibe

# Install backend dependencies
pip install uv
uv sync

# Install frontend dependencies
cd web
npm install
npm run build
cd ..

# Start the backend
uv run uvicorn main:app --reload

# In another terminal, start the frontend
cd web
npm run dev
```

## First Configuration

1. **Open the web interface** at `http://localhost:8000` (or `http://localhost:80` for Docker)

2. **Enter a personality description**:
   - Try: "Tony Stark from Iron Man"
   - Or: "A patient mentor who explains things clearly"
   - Or: "Yoda from Star Wars"

3. **Select your project directory**:
   - Click "Browse" and select your coding project folder
   - Covibe will automatically detect your IDE

4. **Generate the configuration**:
   - Click "Generate Configuration"
   - Wait for the personality research to complete
   - Review the generated personality profile

5. **Apply to your IDE**:
   - Covibe will automatically create the appropriate configuration files
   - For Cursor: Check `/cursor/rules/personality.mdc`
   - For Claude: Check `CLAUDE.md` in your project root
   - For Windsurf: Check `.windsurf` file

## Testing Your Configuration

1. **Open your IDE** (Cursor, Claude, or Windsurf)
2. **Start a new chat** with your coding agent
3. **Ask a coding question** and notice the personality in the response
4. **Try different questions** to see how the personality affects responses

## Example Personalities to Try

### Technical Personalities
- "Linus Torvalds" - Direct, technical, no-nonsense
- "Steve Jobs" - Perfectionist, design-focused
- "Ada Lovelace" - Analytical, pioneering

### Fictional Characters
- "Sherlock Holmes" - Logical, deductive reasoning
- "Tony Stark" - Witty, confident, tech-savvy
- "Yoda" - Wise, patient, speaks in unique patterns

### Character Archetypes
- "Friendly mentor" - Patient, encouraging, educational
- "Drill sergeant" - Direct, motivating, results-focused
- "Wise professor" - Academic, thorough, thoughtful

## API Quick Start

If you prefer to use the API directly:

```bash
# Create a personality configuration
curl -X POST http://localhost:8000/api/personality \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Tony Stark from Iron Man",
    "project_path": "/path/to/your/project"
  }'

# List your configurations
curl http://localhost:8000/api/personality/configs

# Research a personality without creating a config
curl -X POST http://localhost:8000/api/personality/research \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Sherlock Holmes",
    "use_cache": true
  }'
```

## Chat Interface

For conversational configuration:

1. **Open the chat interface** in the web UI
2. **Type natural language requests**:
   - "I want my agent to be like Tony Stark"
   - "Make it more patient and less sarcastic"
   - "Switch to Yoda personality"
3. **Refine through conversation** until you get the perfect personality

## Next Steps

- [Read the full User Guide](../user-guide/README.md)
- [Explore API documentation](../api/README.md)
- [Learn about IDE integration](../user-guide/ide-integration.md)
- [Set up multiple personalities](../user-guide/managing-personalities.md)

## Troubleshooting

### Common Issues

**"No IDE detected"**
- Ensure you're in a valid project directory
- Check that your IDE has created its configuration files
- Try manually specifying the IDE type

**"Personality research failed"**
- Check your internet connection
- Try a more specific personality description
- Use the research endpoint to test different queries

**"Configuration not applied"**
- Restart your IDE after configuration
- Check file permissions in your project directory
- Verify the configuration file was created correctly

For more help, see the [Troubleshooting Guide](../troubleshooting.md).