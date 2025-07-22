# Quick Start - Development Setup

This guide will get you up and running with Covibe in development mode, avoiding the Docker build issues.

## Option 1: Backend Only (Recommended for Development)

This approach runs just the backend with Docker and lets you develop/test the API directly.

```bash
# 1. Start just the backend and Redis
./scripts/deploy.sh start

# 2. Test the backend API
curl http://localhost:8000/health

# 3. View API documentation
open http://localhost:8000/docs
```

## Option 2: Full Local Development

Run both backend and frontend locally without Docker.

### Backend Setup
```bash
# Install Python dependencies
pip install uv
uv sync

# Start the backend
uv run uvicorn main:app --reload --port 8000
```

### Frontend Setup (in another terminal)
```bash
# Navigate to web directory
cd web

# Install Node.js dependencies
npm install

# Start development server
npm run dev
```

## Option 3: Fix Docker Build Issues

If you want to use the full Docker setup, here's how to fix the build issues:

### Fix Frontend Build
```bash
# Navigate to web directory
cd web

# Install dependencies and test build locally first
npm install
npm run build

# If build succeeds, then try Docker
cd ..
docker-compose -f docker-compose.yml build frontend
```

### Fix Backend Build
```bash
# Build backend separately
docker-compose -f docker-compose.yml build backend
```

## Testing Your Setup

Once you have the backend running (any method above):

### Test API Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Create a personality
curl -X POST http://localhost:8000/api/personality \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Tony Stark from Iron Man",
    "project_path": "/tmp/test"
  }'

# List personalities
curl http://localhost:8000/api/personality/configs
```

### View API Documentation
Open http://localhost:8000/docs in your browser to see the interactive API documentation.

## Common Issues and Solutions

### "Docker build failed"
- Use Option 1 or 2 above to avoid Docker build issues
- The development compose file (`docker-compose.dev.yml`) only builds the backend

### "Frontend build failed"
- The frontend has TypeScript compilation issues in Docker
- Use local development (Option 2) for frontend development
- Or fix the build locally first, then try Docker

### "Backend not healthy"
- Check if port 8000 is already in use: `lsof -i :8000`
- Check backend logs: `docker-compose logs backend`
- Ensure database directory exists: `mkdir -p data`

### "Permission denied"
- Make sure the deploy script is executable: `chmod +x scripts/deploy.sh`
- Check Docker permissions: `sudo usermod -aG docker $USER` (then logout/login)

## Next Steps

Once you have the backend running:

1. **Test the API**: Use the Swagger UI at http://localhost:8000/docs
2. **Create personalities**: Try different personality descriptions
3. **Check IDE integration**: Test with your coding projects
4. **Explore the code**: Look at the source code in `src/covibe/`

## Development Workflow

For active development, I recommend:

1. **Backend**: Use `uv run uvicorn main:app --reload` for hot reloading
2. **Frontend**: Use `npm run dev` for hot reloading
3. **Database**: SQLite file in `./data/covibe.db` (created automatically)
4. **Logs**: Check `./logs/` directory for application logs

This setup gives you the fastest development experience while avoiding Docker build complexities.