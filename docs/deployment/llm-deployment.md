# LLM Integration Deployment Guide

This guide covers deploying the Covibe Agent Personality System with LLM integration in production environments.

## Environment Variables

### Required Environment Variables

```bash
# Core LLM Provider API Keys
OPENAI_API_KEY="sk-your-openai-api-key-here"
ANTHROPIC_API_KEY="sk-ant-your-anthropic-api-key-here"

# Optional: Custom Base URLs
OPENAI_BASE_URL="https://api.openai.com/v1"
ANTHROPIC_BASE_URL="https://api.anthropic.com"

# Local LLM Configuration (if using)
LOCAL_LLM_BASE_URL="http://localhost:11434"
LOCAL_LLM_API_KEY="your-local-api-key"  # If required

# Configuration Paths
LLM_CONFIG_PATH="/app/config/llm"
PROMPT_CONFIG_PATH="/app/config/prompts"

# Redis Configuration (for caching)
REDIS_URL="redis://redis:6379"
REDIS_PASSWORD="your-redis-password"
REDIS_DB="0"

# Application Settings
LLM_RESEARCH_ENABLED="true"
DEFAULT_LLM_PROVIDER="openai"
ENABLE_LLM_CACHING="true"
CACHE_TTL_HOURS="24"

# Cost and Rate Limiting
DAILY_BUDGET_USD="100.0"
MONTHLY_BUDGET_USD="2000.0"
MAX_CONCURRENT_LLM_REQUESTS="10"

# Security Settings
ENABLE_INPUT_SANITIZATION="true"
ENABLE_OUTPUT_VALIDATION="true"
MAX_DESCRIPTION_LENGTH="2000"

# Monitoring and Logging
LOG_LEVEL="INFO"
LOG_LLM_REQUESTS="true"
LOG_LLM_RESPONSES="false"  # Security: Don't log responses
ENABLE_METRICS="true"
METRICS_PORT="9090"
```

### Environment-Specific Configurations

#### Development Environment
```bash
# .env.development
NODE_ENV="development"
LOG_LEVEL="DEBUG"
LLM_RESEARCH_ENABLED="true"
DEFAULT_LLM_PROVIDER="openai"
ENABLE_LLM_CACHING="true"
LOG_LLM_REQUESTS="true"
LOG_LLM_RESPONSES="true"  # OK for development
DAILY_BUDGET_USD="10.0"  # Lower budget for dev
```

#### Staging Environment
```bash
# .env.staging
NODE_ENV="staging"
LOG_LEVEL="INFO"
LLM_RESEARCH_ENABLED="true"
DEFAULT_LLM_PROVIDER="openai"
ENABLE_LLM_CACHING="true"
LOG_LLM_REQUESTS="true"
LOG_LLM_RESPONSES="false"
DAILY_BUDGET_USD="50.0"

# Use staging-specific API keys
OPENAI_API_KEY="sk-staging-key-here"
ANTHROPIC_API_KEY="sk-ant-staging-key-here"
```

#### Production Environment
```bash
# .env.production
NODE_ENV="production"
LOG_LEVEL="INFO"
LLM_RESEARCH_ENABLED="true"
DEFAULT_LLM_PROVIDER="openai"
ENABLE_LLM_CACHING="true"
LOG_LLM_REQUESTS="false"  # Minimal logging in prod
LOG_LLM_RESPONSES="false"
DAILY_BUDGET_USD="500.0"
MONTHLY_BUDGET_USD="10000.0"

# Production Redis cluster
REDIS_URL="redis://redis-cluster:6379"
REDIS_SENTINEL_URLS="redis-sentinel-1:26379,redis-sentinel-2:26379,redis-sentinel-3:26379"
```

## Configuration Files

### LLM Provider Configuration

Create production-ready provider configuration:

```yaml
# config/llm/providers.yaml
providers:
  openai:
    api_key_env: "OPENAI_API_KEY"
    base_url: "${OPENAI_BASE_URL:-https://api.openai.com/v1}"
    models:
      - "gpt-4-1106-preview"
      - "gpt-4"
      - "gpt-3.5-turbo-1106"
    default_model: "gpt-4"
    timeout_seconds: 30
    max_retries: 3
    rate_limiting:
      requests_per_minute: 50
      tokens_per_minute: 90000
    retry_settings:
      initial_delay: 1.0
      exponential_base: 2.0
      max_delay: 60.0
    
  anthropic:
    api_key_env: "ANTHROPIC_API_KEY"
    base_url: "${ANTHROPIC_BASE_URL:-https://api.anthropic.com}"
    models:
      - "claude-3-opus-20240229"
      - "claude-3-sonnet-20240229"
      - "claude-3-haiku-20240307"
    default_model: "claude-3-sonnet-20240229"
    timeout_seconds: 45
    max_retries: 3
    rate_limiting:
      requests_per_minute: 60
      tokens_per_minute: 100000
    
  local:
    base_url: "${LOCAL_LLM_BASE_URL:-http://localhost:11434}"
    models:
      - "llama2:13b"
      - "mistral:7b"
    default_model: "llama2:13b"
    timeout_seconds: 120
    max_retries: 2

# Global settings
default_provider: "${DEFAULT_LLM_PROVIDER:-openai}"
fallback_providers: ["anthropic", "local"]
enable_response_caching: ${ENABLE_LLM_CACHING:-true}
cache_ttl_hours: ${CACHE_TTL_HOURS:-24}
max_concurrent_requests: ${MAX_CONCURRENT_LLM_REQUESTS:-10}

# Cost management
cost_optimization:
  enabled: true
  daily_budget_usd: ${DAILY_BUDGET_USD:-100.0}
  monthly_budget_usd: ${MONTHLY_BUDGET_USD:-2000.0}
  warn_threshold: 0.8
  fallback_on_budget_exceeded: true

# Security
security:
  input_sanitization:
    enabled: ${ENABLE_INPUT_SANITIZATION:-true}
    max_description_length: ${MAX_DESCRIPTION_LENGTH:-2000}
  output_validation:
    enabled: ${ENABLE_OUTPUT_VALIDATION:-true}
    max_response_length: 10000
```

### Caching Configuration

```yaml
# config/llm/cache.yaml
cache:
  backend: "redis"
  redis:
    url: "${REDIS_URL}"
    password: "${REDIS_PASSWORD}"
    db: ${REDIS_DB:-0}
    key_prefix: "covibe:llm:"
    connection_pool:
      max_connections: 50
      retry_on_timeout: true
  
  # Cache policies
  ttl_hours: ${CACHE_TTL_HOURS:-24}
  key_strategy: "semantic"
  similarity_threshold: 0.85
  compress_responses: true
  
  # Health monitoring
  health_check_interval: 30
  max_failure_count: 5
```

### Monitoring Configuration

```yaml
# config/monitoring/llm_metrics.yaml
metrics:
  enabled: ${ENABLE_METRICS:-true}
  port: ${METRICS_PORT:-9090}
  
  # Prometheus metrics
  prometheus:
    enabled: true
    metrics:
      - name: "llm_requests_total"
        type: "counter"
        labels: ["provider", "model", "status"]
      - name: "llm_response_time_seconds"
        type: "histogram"
        labels: ["provider", "model"]
      - name: "llm_cost_usd_total"
        type: "counter"
        labels: ["provider", "model"]
      - name: "llm_cache_hits_total"
        type: "counter"
        labels: ["cache_type"]
      - name: "llm_errors_total"
        type: "counter"
        labels: ["provider", "error_type"]
  
  # Alerting
  alerts:
    - name: "high_error_rate"
      condition: "rate(llm_errors_total[5m]) / rate(llm_requests_total[5m]) > 0.1"
      action: "webhook"
      webhook_url: "${ALERT_WEBHOOK_URL}"
    - name: "budget_exceeded"
      condition: "llm_cost_usd_total > ${DAILY_BUDGET_USD} * 0.9"
      action: "disable_llm"
```

## Container Deployment

### Docker Configuration

Update the main Dockerfile to include LLM dependencies:

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN pip install uv && \
    uv sync --frozen

# Copy application code
COPY . .

# Create configuration directories
RUN mkdir -p /app/config/llm /app/config/prompts /app/cache

# Copy default configurations
COPY config/llm/ /app/config/llm/
COPY config/prompts/ /app/config/prompts/

# Set permissions
RUN chown -R app:app /app && \
    chmod -R 755 /app/config

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
USER app
EXPOSE 8000
CMD ["uvicorn", "src.covibe.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  covibe-api:
    build: .
    ports:
      - "8000:8000"
      - "9090:9090"  # Metrics port
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - REDIS_URL=redis://redis:6379
      - LLM_CONFIG_PATH=/app/config/llm
      - PROMPT_CONFIG_PATH=/app/config/prompts
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - ENABLE_METRICS=true
    volumes:
      - ./config/llm:/app/config/llm:ro
      - ./config/prompts:/app/config/prompts:ro
      - ./logs:/app/logs
      - ./cache:/app/cache
    depends_on:
      - redis
      - prometheus
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    environment:
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9091:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./config/grafana:/etc/grafana/provisioning:ro
    restart: unless-stopped

volumes:
  redis_data:
  prometheus_data:
  grafana_data:
```

### Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  covibe-api:
    image: covibe/personality-system:latest
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    ports:
      - "8000:8000"
    environment:
      - NODE_ENV=production
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - REDIS_URL=redis://redis-cluster:6379
      - LOG_LEVEL=INFO
      - DAILY_BUDGET_USD=500.0
    volumes:
      - /opt/covibe/config/llm:/app/config/llm:ro
      - /opt/covibe/config/prompts:/app/config/prompts:ro
      - /var/log/covibe:/app/logs
    networks:
      - covibe-network
    secrets:
      - openai_api_key
      - anthropic_api_key

  redis-cluster:
    image: redis:7-alpine
    deploy:
      replicas: 3
    volumes:
      - redis_cluster_data:/data
    networks:
      - covibe-network
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - covibe-api
    networks:
      - covibe-network

networks:
  covibe-network:
    driver: overlay

volumes:
  redis_cluster_data:

secrets:
  openai_api_key:
    external: true
  anthropic_api_key:
    external: true
```

## Kubernetes Deployment

### Namespace and ConfigMaps

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
  name: llm-config
  namespace: covibe
data:
  providers.yaml: |
    providers:
      openai:
        api_key_env: "OPENAI_API_KEY"
        base_url: "https://api.openai.com/v1"
        models: ["gpt-4", "gpt-3.5-turbo"]
        default_model: "gpt-4"
      anthropic:
        api_key_env: "ANTHROPIC_API_KEY"
        base_url: "https://api.anthropic.com"
        models: ["claude-3-sonnet-20240229"]
        default_model: "claude-3-sonnet-20240229"
    default_provider: "openai"
    fallback_providers: ["anthropic"]
```

### Secrets Management

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: llm-secrets
  namespace: covibe
type: Opaque
data:
  OPENAI_API_KEY: c2stWW91ck9wZW5BSUFQSUtleUhlcmU=  # base64 encoded
  ANTHROPIC_API_KEY: c2stYW50LVlvdXJBbnRocm9waWNBUElLZXlIZXJl  # base64 encoded
  REDIS_PASSWORD: WW91clJlZGlzUGFzc3dvcmQ=  # base64 encoded
```

### Deployment Configuration

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: covibe-api
  namespace: covibe
spec:
  replicas: 3
  selector:
    matchLabels:
      app: covibe-api
  template:
    metadata:
      labels:
        app: covibe-api
    spec:
      containers:
      - name: covibe-api
        image: covibe/personality-system:latest
        ports:
        - containerPort: 8000
        - containerPort: 9090  # Metrics
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-secrets
              key: OPENAI_API_KEY
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-secrets
              key: ANTHROPIC_API_KEY
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        - name: LLM_CONFIG_PATH
          value: "/app/config/llm"
        - name: LOG_LEVEL
          value: "INFO"
        volumeMounts:
        - name: llm-config
          mountPath: /app/config/llm
          readOnly: true
        - name: prompt-config
          mountPath: /app/config/prompts
          readOnly: true
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
      volumes:
      - name: llm-config
        configMap:
          name: llm-config
      - name: prompt-config
        configMap:
          name: prompt-config
```

### Service and Ingress

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: covibe-api-service
  namespace: covibe
spec:
  selector:
    app: covibe-api
  ports:
  - name: http
    port: 80
    targetPort: 8000
  - name: metrics
    port: 9090
    targetPort: 9090
---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: covibe-ingress
  namespace: covibe
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.covibe.dev
    secretName: covibe-tls
  rules:
  - host: api.covibe.dev
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: covibe-api-service
            port:
              number: 80
```

## Monitoring and Alerting

### Prometheus Configuration

```yaml
# config/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'covibe-api'
    static_configs:
      - targets: ['covibe-api:9090']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Alert Rules

```yaml
# config/alert_rules.yml
groups:
- name: llm_alerts
  rules:
  - alert: HighLLMErrorRate
    expr: rate(llm_errors_total[5m]) / rate(llm_requests_total[5m]) > 0.1
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High LLM error rate detected"
      description: "LLM error rate is {{ $value | humanizePercentage }} for the last 5 minutes"

  - alert: LLMBudgetExceeded
    expr: llm_cost_usd_total > 500
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Daily LLM budget exceeded"
      description: "Daily LLM costs have reached ${{ $value }}"

  - alert: LLMHighLatency
    expr: histogram_quantile(0.95, rate(llm_response_time_seconds_bucket[5m])) > 10
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High LLM response latency"
      description: "95th percentile latency is {{ $value }}s"
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Covibe LLM Metrics",
    "panels": [
      {
        "title": "LLM Requests per Second",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(llm_requests_total[1m])",
            "legendFormat": "{{provider}} - {{model}}"
          }
        ]
      },
      {
        "title": "LLM Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(llm_errors_total[1m]) / rate(llm_requests_total[1m])",
            "legendFormat": "{{provider}} error rate"
          }
        ]
      },
      {
        "title": "Daily LLM Costs",
        "type": "singlestat",
        "targets": [
          {
            "expr": "sum(llm_cost_usd_total)",
            "legendFormat": "Total Cost USD"
          }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(llm_cache_hits_total[1m]) / (rate(llm_cache_hits_total[1m]) + rate(llm_requests_total[1m]))",
            "legendFormat": "Cache Hit Rate"
          }
        ]
      }
    ]
  }
}
```

## Security Considerations

### API Key Management

1. **Environment Variables**: Store in secure secret management
2. **Rotation**: Regularly rotate API keys
3. **Monitoring**: Monitor for unusual usage patterns
4. **Scoping**: Use least privilege API keys when possible

### Network Security

```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: covibe-network-policy
  namespace: covibe
spec:
  podSelector:
    matchLabels:
      app: covibe-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to: []  # Allow all outbound for LLM API calls
    ports:
    - protocol: TCP
      port: 443  # HTTPS
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
```

### Input Validation

Ensure all LLM inputs are validated and sanitized:

```python
# Security configuration
SECURITY_CONFIG = {
    "input_sanitization": {
        "max_length": 2000,
        "forbidden_patterns": [
            r"ignore\s+previous\s+instructions",
            r"system\s*:",
            r"api\s*key",
            r"password"
        ]
    },
    "output_validation": {
        "max_length": 10000,
        "content_filters": [
            "personal_information",
            "harmful_content"
        ]
    }
}
```

## Backup and Recovery

### Configuration Backup

```bash
#!/bin/bash
# backup-config.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/covibe/$DATE"

mkdir -p $BACKUP_DIR

# Backup configurations
cp -r /app/config/llm $BACKUP_DIR/
cp -r /app/config/prompts $BACKUP_DIR/

# Backup Redis data
redis-cli --rdb $BACKUP_DIR/redis_dump.rdb

# Upload to S3
aws s3 sync $BACKUP_DIR s3://covibe-backups/$DATE/
```

### Disaster Recovery

```yaml
# k8s/backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: config-backup
  namespace: covibe
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: alpine:latest
            command:
            - /bin/sh
            - -c
            - |
              apk add --no-cache aws-cli
              aws s3 sync /config s3://covibe-backups/$(date +%Y%m%d)/
            volumeMounts:
            - name: llm-config
              mountPath: /config/llm
            - name: prompt-config
              mountPath: /config/prompts
          volumes:
          - name: llm-config
            configMap:
              name: llm-config
          - name: prompt-config
            configMap:
              name: prompt-config
          restartPolicy: OnFailure
```

## Performance Optimization

### Resource Allocation

```yaml
# Resource requests and limits
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"

# Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: covibe-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: covibe-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Caching Strategy

```yaml
# Redis cluster for high availability
redis:
  cluster:
    enabled: true
    nodes: 6
    replicas: 2
  persistence:
    enabled: true
    size: 10Gi
  monitoring:
    enabled: true
```

This deployment guide provides comprehensive coverage of deploying the LLM-enhanced Covibe system in production environments with proper security, monitoring, and scalability considerations.