# Deployment Guide

This guide covers deploying Covibe in various environments, from local development to production.

## Table of Contents

1. [Quick Deployment](#quick-deployment)
2. [Environment Configuration](#environment-configuration)
3. [Docker Deployment](#docker-deployment)
4. [Production Deployment](#production-deployment)
5. [Monitoring Setup](#monitoring-setup)
6. [Security Considerations](#security-considerations)
7. [Backup and Recovery](#backup-and-recovery)
8. [Troubleshooting](#troubleshooting)

## Quick Deployment

### Using the Deployment Script

The easiest way to deploy Covibe is using the provided deployment script:

```bash
# Development deployment
./scripts/deploy.sh start

# Production deployment
./scripts/deploy.sh -e production deploy

# With monitoring
./scripts/deploy.sh -m start
```

### Manual Docker Deployment

```bash
# Clone repository
git clone https://github.com/covibe/covibe.git
cd covibe

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

## Environment Configuration

### Development Environment

```bash
# .env.development
ENVIRONMENT=development
LOG_LEVEL=debug
DATABASE_URL=sqlite:///./data/covibe.db
API_KEY_REQUIRED=false
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

### Staging Environment

```bash
# .env.staging
ENVIRONMENT=staging
LOG_LEVEL=info
DATABASE_URL=postgresql://covibe:password@db:5432/covibe_staging
API_KEY_REQUIRED=true
SECRET_KEY=staging-secret-key
CORS_ORIGINS=["https://staging.covibe.dev"]
```

### Production Environment

```bash
# .env.production
ENVIRONMENT=production
LOG_LEVEL=warning
DATABASE_URL=postgresql://covibe:${DB_PASSWORD}@db:5432/covibe
API_KEY_REQUIRED=true
SECRET_KEY=${SECRET_KEY}
CORS_ORIGINS=["https://covibe.dev"]

# Security
HTTPS_ONLY=true
SECURE_COOKIES=true
CSRF_PROTECTION=true

# Performance
REDIS_URL=redis://redis:6379
CACHE_TTL=3600
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

## Docker Deployment

### Basic Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///app/data/covibe.db
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs

  frontend:
    build:
      context: ./web
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
```

### Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    image: covibe/backend:latest
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://covibe:${DB_PASSWORD}@db:5432/covibe
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped

  frontend:
    image: covibe/frontend:latest
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=covibe
      - POSTGRES_USER=covibe
      - POSTGRES_PASSWORD=${DB_PASSWORD}
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
    restart: unless-stopped

volumes:
  postgres_data:
```

### Building Images

```bash
# Build backend image
docker build -t covibe/backend:latest -f Dockerfile.backend .

# Build frontend image
docker build -t covibe/frontend:latest ./web

# Push to registry
docker push covibe/backend:latest
docker push covibe/frontend:latest
```

## Production Deployment

### Prerequisites

1. **Server Requirements**:
   - Ubuntu 20.04+ or CentOS 8+
   - 4GB RAM minimum (8GB recommended)
   - 20GB storage minimum
   - Docker and Docker Compose installed

2. **Domain and SSL**:
   - Domain name configured
   - SSL certificate (Let's Encrypt recommended)

3. **Database**:
   - PostgreSQL 13+ (managed service recommended)
   - Redis for caching

### Step-by-Step Production Deployment

#### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install additional tools
sudo apt install -y nginx certbot python3-certbot-nginx
```

#### 2. SSL Certificate Setup

```bash
# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### 3. Database Setup

```bash
# PostgreSQL setup (if not using managed service)
sudo apt install -y postgresql postgresql-contrib
sudo -u postgres createdb covibe
sudo -u postgres createuser covibe
sudo -u postgres psql -c "ALTER USER covibe WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE covibe TO covibe;"
```

#### 4. Application Deployment

```bash
# Clone repository
git clone https://github.com/covibe/covibe.git
cd covibe

# Set up environment
cp .env.production.example .env
# Edit .env with your configuration

# Deploy
./scripts/deploy.sh -e production deploy
```

#### 5. Nginx Configuration

```nginx
# /etc/nginx/sites-available/covibe
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass http://localhost:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### Kubernetes Deployment

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: covibe

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: covibe-config
  namespace: covibe
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "info"

---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: covibe-secrets
  namespace: covibe
type: Opaque
data:
  database-url: <base64-encoded-database-url>
  secret-key: <base64-encoded-secret-key>

---
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: covibe-backend
  namespace: covibe
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
        envFrom:
        - configMapRef:
            name: covibe-config
        - secretRef:
            name: covibe-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: covibe-backend-service
  namespace: covibe
spec:
  selector:
    app: covibe-backend
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: covibe-ingress
  namespace: covibe
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - yourdomain.com
    secretName: covibe-tls
  rules:
  - host: yourdomain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: covibe-backend-service
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: covibe-frontend-service
            port:
              number: 80
```

## Monitoring Setup

### Prometheus and Grafana

```bash
# Start with monitoring
./scripts/deploy.sh -m start

# Access monitoring services
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
```

### Custom Metrics

Add to your backend application:

```python
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
personality_requests = Counter('personality_requests_total', 'Total personality requests')
request_duration = Histogram('request_duration_seconds', 'Request duration')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    request_duration.observe(time.time() - start_time)
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Alerting Rules

```yaml
# monitoring/alert_rules.yml
groups:
- name: covibe_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: High error rate detected

  - alert: DatabaseConnectionFailed
    expr: up{job="covibe-backend"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: Backend service is down
```

## Security Considerations

### Network Security

```bash
# Firewall configuration
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8000/tcp  # Block direct backend access
sudo ufw enable
```

### Application Security

1. **Environment Variables**: Never commit secrets to version control
2. **API Keys**: Use strong, randomly generated API keys
3. **Database**: Use connection pooling and prepared statements
4. **HTTPS**: Always use HTTPS in production
5. **CORS**: Configure CORS properly for your domain

### Docker Security

```dockerfile
# Use non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Read-only filesystem
docker run --read-only --tmpfs /tmp covibe/backend
```

## Backup and Recovery

### Automated Backups

```bash
# Create backup script
cat > /usr/local/bin/covibe-backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/covibe"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Database backup
pg_dump -h localhost -U covibe covibe > "$BACKUP_DIR/db_$DATE.sql"

# Configuration backup
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" /opt/covibe/data /opt/covibe/logs

# Cleanup old backups (keep 7 days)
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x /usr/local/bin/covibe-backup.sh

# Schedule backup
echo "0 2 * * * /usr/local/bin/covibe-backup.sh" | crontab -
```

### Recovery Procedures

```bash
# Database recovery
psql -h localhost -U covibe -d covibe < backup.sql

# Configuration recovery
tar -xzf config_backup.tar.gz -C /

# Restart services
./scripts/deploy.sh restart
```

## Troubleshooting

### Common Issues

#### Service Won't Start

```bash
# Check logs
docker-compose logs backend

# Check disk space
df -h

# Check memory
free -h

# Check ports
netstat -tulpn | grep :8000
```

#### Database Connection Issues

```bash
# Test database connection
docker-compose exec backend python -c "
from src.covibe.utils.database import get_database_config
import asyncio
asyncio.run(get_database_config())
"

# Check database logs
docker-compose logs db
```

#### Performance Issues

```bash
# Monitor resource usage
docker stats

# Check application metrics
curl http://localhost:8000/metrics

# Analyze logs
docker-compose logs backend | grep ERROR
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Database health
docker-compose exec db pg_isready -U covibe

# Redis health
docker-compose exec redis redis-cli ping
```

### Log Analysis

```bash
# View recent logs
docker-compose logs --tail=100 backend

# Follow logs
docker-compose logs -f backend

# Search logs
docker-compose logs backend | grep ERROR

# Export logs
docker-compose logs backend > backend.log
```

## Scaling and Performance

### Horizontal Scaling

```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  backend:
    deploy:
      replicas: 3
    
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx-lb.conf:/etc/nginx/nginx.conf
```

### Load Balancer Configuration

```nginx
upstream backend {
    server backend_1:8000;
    server backend_2:8000;
    server backend_3:8000;
}

server {
    location /api/ {
        proxy_pass http://backend;
    }
}
```

### Performance Tuning

1. **Database**: Connection pooling, indexing, query optimization
2. **Caching**: Redis for session and API response caching
3. **CDN**: Use CDN for static assets
4. **Compression**: Enable gzip compression
5. **Monitoring**: Continuous performance monitoring

## Next Steps

- [Set up monitoring dashboards](./monitoring.md)
- [Configure automated backups](./backup.md)
- [Implement CI/CD pipeline](./cicd.md)
- [Security hardening](./security.md)