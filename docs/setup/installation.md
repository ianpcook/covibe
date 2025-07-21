# Installation Guide

This guide covers different installation methods for Covibe, from simple Docker deployment to development setup.

## System Requirements

### Minimum Requirements
- **OS**: Linux, macOS, or Windows
- **Python**: 3.11 or higher
- **Memory**: 2GB RAM
- **Storage**: 1GB free space
- **Network**: Internet connection for personality research

### Recommended Requirements
- **OS**: Linux or macOS
- **Python**: 3.11+
- **Node.js**: 18+ (for web interface development)
- **Memory**: 4GB RAM
- **Storage**: 5GB free space
- **Network**: Stable internet connection

## Installation Methods

### 1. Docker Installation (Recommended)

Docker provides the easiest and most reliable installation method.

#### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

#### Quick Setup
```bash
# Clone the repository
git clone https://github.com/covibe/covibe.git
cd covibe

# Start all services
docker-compose up -d

# Verify installation
curl http://localhost:80/health
```

#### Custom Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env

# Start with custom config
docker-compose --env-file .env up -d
```

#### Docker Environment Variables
```bash
# Backend Configuration
ENVIRONMENT=production
LOG_LEVEL=info
DATABASE_URL=sqlite:///app/data/covibe.db
API_KEY_REQUIRED=false

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

### 2. Python Package Installation

Install Covibe as a Python package for integration into existing projects.

```bash
# Install from PyPI (when available)
pip install covibe

# Or install from source
git clone https://github.com/covibe/covibe.git
cd covibe
pip install -e .

# Start the service
covibe start --port 8000
```

### 3. Development Installation

For contributors and advanced users who want to modify Covibe.

#### Backend Setup
```bash
# Clone repository
git clone https://github.com/covibe/covibe.git
cd covibe

# Install uv (modern Python package manager)
pip install uv

# Create virtual environment and install dependencies
uv sync

# Install development dependencies
uv sync --group dev

# Run tests to verify installation
uv run pytest

# Start development server
uv run uvicorn main:app --reload --port 8000
```

#### Frontend Setup
```bash
# Navigate to web directory
cd web

# Install Node.js dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

#### Full Development Environment
```bash
# Terminal 1: Backend
uv run uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd web && npm run dev

# Terminal 3: Tests (optional)
uv run pytest --watch
```

### 4. Production Installation

For production deployments with proper security and monitoring.

#### Using Docker Compose (Production)
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=warning
      - DATABASE_URL=postgresql://user:pass@db:5432/covibe
      - API_KEY_REQUIRED=true
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped

  frontend:
    build:
      context: ./web
      dockerfile: Dockerfile
    environment:
      - REACT_APP_API_URL=https://api.yourdomain.com
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=covibe
      - POSTGRES_USER=covibe
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
```

#### Kubernetes Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: covibe-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: covibe-backend
  template:
    metadata:
      labels:
        app: covibe-backend
    spec:
      containers:
      - name: backend
        image: covibe/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: covibe-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

## Configuration

### Environment Variables

#### Backend Configuration
```bash
# Server Configuration
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development  # development, staging, production
LOG_LEVEL=info          # debug, info, warning, error

# Database Configuration
DATABASE_URL=sqlite:///./data/covibe.db
# Or for PostgreSQL: postgresql://user:pass@localhost:5432/covibe

# Security Configuration
API_KEY_REQUIRED=false
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# External Services
WIKIPEDIA_API_URL=https://en.wikipedia.org/api/rest_v1
MARVEL_API_KEY=your-marvel-api-key
DC_API_KEY=your-dc-api-key

# Caching
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600  # seconds

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60  # seconds
```

#### Frontend Configuration
```bash
# API Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000

# Feature Flags
REACT_APP_ENABLE_CHAT=true
REACT_APP_ENABLE_ANALYTICS=false

# UI Configuration
REACT_APP_THEME=light  # light, dark, auto
REACT_APP_LANGUAGE=en
```

### Database Setup

#### SQLite (Default)
No additional setup required. Database file will be created automatically.

#### PostgreSQL
```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE covibe;
CREATE USER covibe WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE covibe TO covibe;
\q

# Update DATABASE_URL
export DATABASE_URL="postgresql://covibe:your_password@localhost:5432/covibe"
```

#### MySQL
```bash
# Install MySQL
sudo apt-get install mysql-server

# Create database and user
mysql -u root -p
CREATE DATABASE covibe;
CREATE USER 'covibe'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON covibe.* TO 'covibe'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# Update DATABASE_URL
export DATABASE_URL="mysql://covibe:your_password@localhost:3306/covibe"
```

## Verification

### Health Checks
```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend (if running separately)
curl http://localhost:3000

# Check database connection
curl http://localhost:8000/api/personality/configs
```

### Test Configuration
```bash
# Create a test personality
curl -X POST http://localhost:8000/api/personality \
  -H "Content-Type: application/json" \
  -d '{
    "description": "test personality",
    "project_path": "/tmp/test"
  }'

# Verify it was created
curl http://localhost:8000/api/personality/configs
```

## Troubleshooting Installation

### Common Issues

#### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn main:app --port 8001
```

#### Permission Errors
```bash
# Fix file permissions
chmod -R 755 /path/to/covibe
chown -R $USER:$USER /path/to/covibe

# For Docker
sudo chown -R $USER:$USER ./data ./logs
```

#### Database Connection Issues
```bash
# Check database service
systemctl status postgresql  # or mysql

# Test connection
psql -h localhost -U covibe -d covibe  # PostgreSQL
mysql -h localhost -u covibe -p covibe  # MySQL

# Reset database
rm -f ./data/covibe.db  # SQLite only
```

#### Python Dependencies
```bash
# Clear pip cache
pip cache purge

# Reinstall dependencies
uv sync --reinstall

# Check Python version
python --version  # Should be 3.11+
```

#### Node.js Issues
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version  # Should be 18+
```

## Next Steps

After successful installation:

1. [Complete the Quick Start Guide](./quick-start.md)
2. [Configure your first personality](../user-guide/creating-personalities.md)
3. [Set up IDE integration](../user-guide/ide-integration.md)
4. [Explore the API](../api/README.md)

## Getting Help

If you encounter issues during installation:

- Check the [Troubleshooting Guide](../troubleshooting.md)
- Search [GitHub Issues](https://github.com/covibe/covibe/issues)
- Join our [Discord community](https://discord.gg/covibe)
- Email support@covibe.dev