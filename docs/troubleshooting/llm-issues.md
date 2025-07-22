# LLM Integration Troubleshooting Guide

This guide helps diagnose and resolve common issues with LLM integration in the Covibe Agent Personality System.

## Quick Diagnostics

### Health Check Commands

```bash
# Check overall system health
curl -X GET "http://localhost:8000/health"

# Check LLM provider status
curl -X GET "http://localhost:8000/api/personality/llm/status" \
  -H "X-API-Key: your-api-key"

# Test basic LLM research
curl -X POST "http://localhost:8000/api/personality/research" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "description": "test personality",
    "use_llm": true,
    "llm_provider": "openai"
  }'
```

### Log Analysis

```bash
# Check recent logs for LLM-related errors
tail -f /app/logs/app.log | grep -i "llm\|openai\|anthropic"

# Check error patterns
grep -E "(ERROR|CRITICAL)" /app/logs/app.log | grep -i llm | tail -20

# Monitor real-time LLM requests
tail -f /app/logs/app.log | grep "llm_request"
```

## Common Issues and Solutions

### 1. API Key Problems

#### Issue: "Invalid API Key" or "Unauthorized" Errors

**Symptoms:**
```
ERROR: OpenAI API request failed: 401 Unauthorized
ERROR: Invalid API key provided
```

**Diagnosis:**
```bash
# Check if API key is set
echo $OPENAI_API_KEY | head -c 10

# Verify API key format
if [[ $OPENAI_API_KEY =~ ^sk-[a-zA-Z0-9]{48}$ ]]; then
  echo "OpenAI API key format is correct"
else
  echo "OpenAI API key format is incorrect"
fi

# Test API key directly
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     "https://api.openai.com/v1/models" \
     | jq '.data[0].id' 2>/dev/null || echo "API key test failed"
```

**Solutions:**

1. **Verify API Key Format:**
   ```bash
   # OpenAI keys start with "sk-"
   export OPENAI_API_KEY="sk-your-actual-key-here"
   
   # Anthropic keys start with "sk-ant-"
   export ANTHROPIC_API_KEY="sk-ant-your-actual-key-here"
   ```

2. **Check Environment Loading:**
   ```bash
   # Ensure environment file is loaded
   source .env
   
   # Or check if running in container
   docker exec container_name env | grep API_KEY
   ```

3. **Verify Key Permissions:**
   - Check if key has required scopes
   - Ensure key is not rate-limited or suspended
   - Verify billing account is active

4. **Secret Management Issues:**
   ```bash
   # Kubernetes secret debugging
   kubectl get secrets llm-secrets -o yaml
   kubectl describe secret llm-secrets
   
   # Docker secret debugging
   docker secret ls
   docker secret inspect openai_api_key
   ```

#### Issue: "API Key Rotation" Problems

**Solution:**
```bash
# Update API keys without downtime
kubectl patch secret llm-secrets -p='{"data":{"OPENAI_API_KEY":"'$(echo -n "new-key" | base64)'"}}'

# Trigger pod restart to pick up new secrets
kubectl rollout restart deployment/covibe-api
```

### 2. Network and Connectivity Issues

#### Issue: "Connection Timeout" or "DNS Resolution Failed"

**Symptoms:**
```
ERROR: Connection timeout when calling OpenAI API
ERROR: DNS resolution failed for api.openai.com
ERROR: SSL certificate verification failed
```

**Diagnosis:**
```bash
# Test basic connectivity
curl -I https://api.openai.com/v1/models
curl -I https://api.anthropic.com/v1/messages

# Check DNS resolution
nslookup api.openai.com
dig api.openai.com

# Test from container
docker exec container_name curl -I https://api.openai.com/v1/models

# Check SSL certificate
openssl s_client -connect api.openai.com:443 -servername api.openai.com
```

**Solutions:**

1. **Network Policy Issues (Kubernetes):**
   ```yaml
   # Allow egress to LLM providers
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: allow-llm-egress
   spec:
     podSelector:
       matchLabels:
         app: covibe-api
     policyTypes:
     - Egress
     egress:
     - to: []
       ports:
       - protocol: TCP
         port: 443
   ```

2. **Proxy Configuration:**
   ```bash
   # Set proxy environment variables
   export HTTP_PROXY="http://proxy.company.com:8080"
   export HTTPS_PROXY="http://proxy.company.com:8080"
   export NO_PROXY="localhost,127.0.0.1,.local"
   ```

3. **Firewall Rules:**
   ```bash
   # Allow outbound HTTPS traffic
   sudo ufw allow out 443/tcp
   
   # Check iptables rules
   sudo iptables -L OUTPUT -v -n | grep 443
   ```

4. **DNS Issues:**
   ```bash
   # Use public DNS servers
   echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
   echo "nameserver 1.1.1.1" | sudo tee -a /etc/resolv.conf
   ```

### 3. Rate Limiting and Quota Issues

#### Issue: "Rate Limit Exceeded" Errors

**Symptoms:**
```
ERROR: Rate limit exceeded for OpenAI API: 429 Too Many Requests
WARNING: Switching to fallback provider due to rate limits
```

**Diagnosis:**
```bash
# Check current rate limit status
curl -X GET "http://localhost:8000/api/personality/llm/status" | jq '.providers.openai.rate_limit_status'

# Monitor rate limit headers in logs
grep -i "rate.limit" /app/logs/app.log | tail -10

# Check request frequency
grep "llm_request" /app/logs/app.log | tail -20 | awk '{print $1, $2}'
```

**Solutions:**

1. **Configure Rate Limiting:**
   ```yaml
   # config/llm/providers.yaml
   providers:
     openai:
       rate_limiting:
         requests_per_minute: 50
         tokens_per_minute: 90000
         burst_allowance: 10
       retry_settings:
         max_retries: 3
         exponential_backoff: true
         initial_delay: 1.0
         max_delay: 60.0
   ```

2. **Implement Request Queuing:**
   ```python
   # Request queue configuration
   REQUEST_QUEUE_CONFIG = {
       "max_queue_size": 100,
       "queue_timeout": 300,
       "priority_levels": 3
   }
   ```

3. **Provider Switching:**
   ```yaml
   # Automatic fallback configuration
   fallback_providers: ["anthropic", "local"]
   fallback_on_rate_limit: true
   rate_limit_threshold: 0.8
   ```

#### Issue: "Quota Exceeded" or "Billing Issues"

**Solutions:**

1. **Check Account Status:**
   ```bash
   # OpenAI API usage check
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
        "https://api.openai.com/v1/usage"
   ```

2. **Implement Cost Controls:**
   ```yaml
   cost_optimization:
     daily_budget_usd: 100.0
     warn_threshold: 0.8
     stop_threshold: 0.95
     budget_reset_hour: 0  # Midnight UTC
   ```

### 4. Response Validation Issues

#### Issue: "Invalid JSON Response" or "Validation Failed"

**Symptoms:**
```
ERROR: Failed to parse LLM response as JSON
ERROR: Response validation failed: missing required field 'name'
WARNING: Retrying request due to malformed response
```

**Diagnosis:**
```bash
# Check recent response validation errors
grep "validation.*failed\|invalid.*json" /app/logs/app.log | tail -10

# Look for malformed responses
grep -A 5 -B 5 "malformed\|invalid.*response" /app/logs/app.log
```

**Solutions:**

1. **Improve Prompt Templates:**
   ```yaml
   # More explicit JSON formatting instructions
   template: |
     Respond ONLY with valid JSON in this exact format:
     {
       "name": "string",
       "type": "celebrity|fictional|archetype|custom",
       "traits": [{"trait": "string", "intensity": number}],
       "confidence": number
     }
     
     Do not include any text before or after the JSON.
   ```

2. **Add Response Cleaning:**
   ```python
   def clean_llm_response(response: str) -> str:
       """Clean and normalize LLM response."""
       # Remove common prefixes/suffixes
       response = re.sub(r'^.*?({.*}|\\[.*\\]).*?$', r'\\1', response, flags=re.DOTALL)
       
       # Fix common JSON issues
       response = response.replace("'", '"')  # Single to double quotes
       response = re.sub(r',\\s*}', '}', response)  # Remove trailing commas
       
       return response.strip()
   ```

3. **Implement Retry Logic:**
   ```yaml
   validation:
     max_retries: 3
     retry_on_validation_failure: true
     retry_with_simpler_prompt: true
     fallback_to_traditional: true
   ```

### 5. Performance Issues

#### Issue: "Slow Response Times" or "Timeouts"

**Symptoms:**
```
WARNING: LLM request took 45 seconds, exceeding timeout
ERROR: Request timeout after 60 seconds
```

**Diagnosis:**
```bash
# Check response time metrics
curl -X GET "http://localhost:9090/metrics" | grep llm_response_time

# Monitor slow requests
grep -E "took [0-9]{2,}" /app/logs/app.log | tail -10

# Check concurrent request load
ps aux | grep python | wc -l
```

**Solutions:**

1. **Optimize Timeouts:**
   ```yaml
   providers:
     openai:
       timeout_seconds: 30
       request_timeout: 25
       connection_timeout: 10
   ```

2. **Implement Caching:**
   ```yaml
   cache:
     enabled: true
     backend: "redis"
     ttl_hours: 24
     similarity_threshold: 0.85
   ```

3. **Request Optimization:**
   ```yaml
   request_optimization:
     batch_similar_requests: true
     compress_prompts: true
     use_streaming: false  # For faster simple responses
   ```

#### Issue: "Memory Usage Too High"

**Diagnosis:**
```bash
# Check memory usage
docker stats container_name
kubectl top pods

# Monitor memory leaks
ps -o pid,ppid,cmd,%mem,%cpu --sort=-%mem | head -10
```

**Solutions:**

1. **Limit Response Sizes:**
   ```yaml
   validation:
     max_response_length: 5000
     truncate_long_responses: true
   ```

2. **Optimize Caching:**
   ```yaml
   cache:
     max_entries: 1000
     cleanup_interval: 3600
     compress_responses: true
   ```

### 6. Configuration Issues

#### Issue: "Configuration File Not Found" or "Invalid YAML"

**Symptoms:**
```
ERROR: Failed to load LLM configuration from /app/config/llm/providers.yaml
ERROR: YAML parsing error in prompt template
```

**Diagnosis:**
```bash
# Check file existence and permissions
ls -la /app/config/llm/
ls -la /app/config/prompts/

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('/app/config/llm/providers.yaml'))"

# Check file encoding
file /app/config/llm/providers.yaml
```

**Solutions:**

1. **Fix File Permissions:**
   ```bash
   # Set correct permissions
   chmod 644 /app/config/llm/*.yaml
   chmod 644 /app/config/prompts/*.yaml
   chown app:app /app/config/llm/*.yaml
   ```

2. **Validate Configuration:**
   ```bash
   # Use configuration validator
   python scripts/validate_config.py --config /app/config/llm/providers.yaml
   
   # Test YAML parsing
   python -c "
   import yaml
   with open('/app/config/llm/providers.yaml') as f:
       config = yaml.safe_load(f)
       print('Configuration loaded successfully')
       print(f'Providers: {list(config.get(\"providers\", {}).keys())}')
   "
   ```

3. **Container Mount Issues:**
   ```bash
   # Check Docker volume mounts
   docker inspect container_name | jq '.[0].Mounts'
   
   # Kubernetes volume mounts
   kubectl describe pod pod_name | grep -A 10 Mounts
   ```

### 7. Authentication and Authorization

#### Issue: "Permission Denied" or "Insufficient Privileges"

**Solutions:**

1. **Check API Key Scopes:**
   ```bash
   # Verify OpenAI API key permissions
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
        "https://api.openai.com/v1/models" | jq '.data[].id'
   ```

2. **Service Account Issues (Kubernetes):**
   ```yaml
   apiVersion: v1
   kind: ServiceAccount
   metadata:
     name: covibe-service-account
   ---
   apiVersion: rbac.authorization.k8s.io/v1
   kind: ClusterRole
   metadata:
     name: covibe-role
   rules:
   - apiGroups: [""]
     resources: ["secrets", "configmaps"]
     verbs: ["get", "list"]
   ```

## Debugging Tools and Scripts

### LLM Status Checker

```python
#!/usr/bin/env python3
# scripts/check_llm_status.py
import asyncio
import os
import httpx
from typing import Dict, Any

async def check_provider_status(provider: str, api_key: str, base_url: str) -> Dict[str, Any]:
    """Check individual provider status."""
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if provider == "openai":
                response = await client.get(f"{base_url}/models", headers=headers)
            elif provider == "anthropic":
                response = await client.get(f"{base_url}/v1/models", headers=headers)
            else:
                response = await client.get(base_url, headers=headers)
            
            return {
                "status": "healthy" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "error": None
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "response_time_ms": None
        }

async def main():
    providers = {
        "openai": {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "base_url": "https://api.openai.com/v1"
        },
        "anthropic": {
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
            "base_url": "https://api.anthropic.com"
        }
    }
    
    for name, config in providers.items():
        if config["api_key"]:
            status = await check_provider_status(name, config["api_key"], config["base_url"])
            print(f"{name}: {status}")
        else:
            print(f"{name}: API key not configured")

if __name__ == "__main__":
    asyncio.run(main())
```

### Configuration Validator

```python
#!/usr/bin/env python3
# scripts/validate_llm_config.py
import yaml
import sys
from pathlib import Path

def validate_provider_config(config: dict) -> list:
    """Validate provider configuration."""
    errors = []
    
    required_fields = ["api_key_env", "base_url", "models", "default_model"]
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    if "models" in config and "default_model" in config:
        if config["default_model"] not in config["models"]:
            errors.append("default_model not in models list")
    
    return errors

def validate_config_file(config_path: Path) -> bool:
    """Validate entire configuration file."""
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"ERROR: Failed to parse YAML: {e}")
        return False
    
    errors = []
    
    # Check top-level structure
    if "providers" not in config:
        errors.append("Missing 'providers' section")
        return False
    
    # Validate each provider
    for name, provider_config in config["providers"].items():
        provider_errors = validate_provider_config(provider_config)
        for error in provider_errors:
            errors.append(f"Provider '{name}': {error}")
    
    if errors:
        print("Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("Configuration validation passed")
        return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate_llm_config.py <config_file>")
        sys.exit(1)
    
    config_file = Path(sys.argv[1])
    if not config_file.exists():
        print(f"ERROR: Configuration file not found: {config_file}")
        sys.exit(1)
    
    success = validate_config_file(config_file)
    sys.exit(0 if success else 1)
```

### Performance Monitor

```bash
#!/bin/bash
# scripts/monitor_llm_performance.sh

echo "Monitoring LLM performance..."
echo "================================"

# Check response times
echo "Average response times (last 100 requests):"
grep "llm_response_time" /app/logs/app.log | tail -100 | \
  awk '{sum+=$NF; count++} END {if(count>0) print "Average:", sum/count "ms"}'

# Check error rates
echo -e "\nError rates:"
total_requests=$(grep "llm_request" /app/logs/app.log | wc -l)
error_requests=$(grep "llm_error" /app/logs/app.log | wc -l)
if [ $total_requests -gt 0 ]; then
  error_rate=$(echo "scale=2; $error_requests * 100 / $total_requests" | bc)
  echo "Error rate: $error_rate%"
fi

# Check cache hit rate
echo -e "\nCache performance:"
cache_hits=$(grep "cache_hit" /app/logs/app.log | wc -l)
cache_misses=$(grep "cache_miss" /app/logs/app.log | wc -l)
total_cache_requests=$((cache_hits + cache_misses))
if [ $total_cache_requests -gt 0 ]; then
  hit_rate=$(echo "scale=2; $cache_hits * 100 / $total_cache_requests" | bc)
  echo "Cache hit rate: $hit_rate%"
fi

# Check provider usage
echo -e "\nProvider usage:"
grep "llm_request" /app/logs/app.log | grep -o "provider=[a-z]*" | sort | uniq -c
```

## Emergency Procedures

### Disable LLM Integration

```bash
# Quick disable via environment variable
export LLM_RESEARCH_ENABLED="false"

# Or via configuration
curl -X POST "http://localhost:8000/admin/config" \
  -H "Content-Type: application/json" \
  -d '{"llm_research_enabled": false}'

# Kubernetes emergency disable
kubectl patch configmap llm-config -p='{"data":{"enable_llm":"false"}}'
kubectl rollout restart deployment/covibe-api
```

### Force Fallback Mode

```bash
# Force traditional research only
export FORCE_TRADITIONAL_RESEARCH="true"

# Or disable specific providers
export OPENAI_DISABLED="true"
export ANTHROPIC_DISABLED="true"
```

### Scale Down for Maintenance

```bash
# Kubernetes scaling
kubectl scale deployment covibe-api --replicas=0
kubectl scale deployment covibe-api --replicas=3

# Docker Compose
docker-compose down
docker-compose up -d --scale covibe-api=0
docker-compose up -d --scale covibe-api=3
```

## Getting Help

### Support Resources

1. **Check Documentation:**
   - [LLM Configuration Guide](../setup/llm-configuration.md)
   - [Prompt Templates Guide](../setup/prompt-templates.md)
   - [Deployment Guide](../deployment/llm-deployment.md)

2. **Community Support:**
   - GitHub Issues: Report bugs and feature requests
   - Discord: Real-time community support
   - Documentation: Comprehensive guides and examples

3. **Professional Support:**
   - Enterprise support available
   - Custom integration assistance
   - Performance optimization consulting

### Creating Support Tickets

When creating support tickets, include:

1. **System Information:**
   ```bash
   # Collect system info
   python scripts/collect_debug_info.py > debug_info.txt
   ```

2. **Log Files:**
   ```bash
   # Collect relevant logs
   tail -1000 /app/logs/app.log | grep -E "(ERROR|WARNING|llm)" > llm_logs.txt
   ```

3. **Configuration:**
   ```bash
   # Sanitized configuration (remove API keys)
   python scripts/sanitize_config.py config/llm/providers.yaml > sanitized_config.yaml
   ```

4. **Reproduction Steps:**
   - Exact steps to reproduce the issue
   - Expected vs actual behavior
   - Frequency of occurrence

This troubleshooting guide covers the most common issues encountered with LLM integration and provides practical solutions for resolving them quickly.