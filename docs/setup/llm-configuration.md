# LLM Configuration Guide

This guide covers setting up and configuring LLM providers for enhanced personality research in the Covibe Agent Personality System.

## Overview

The LLM integration provides enhanced personality analysis capabilities by leveraging large language models to understand free-form personality descriptions and generate detailed personality profiles. The system supports multiple providers with automatic fallback mechanisms.

## Supported LLM Providers

### OpenAI
- **Models**: GPT-4, GPT-3.5-turbo
- **Best for**: High-quality personality analysis, creative descriptions
- **Rate limits**: Varies by plan
- **Cost**: Pay-per-token

### Anthropic (Claude)
- **Models**: Claude-3-opus, Claude-3-sonnet, Claude-3-haiku
- **Best for**: Detailed analysis, safety-conscious responses
- **Rate limits**: Varies by plan
- **Cost**: Pay-per-token

### Local Models
- **Models**: Ollama, LocalAI, or custom endpoints
- **Best for**: Privacy, cost control, customization
- **Rate limits**: Hardware dependent
- **Cost**: Infrastructure only

## Quick Start

### 1. Environment Variables

Set your API keys as environment variables:

```bash
# OpenAI Configuration
export OPENAI_API_KEY="sk-your-openai-api-key-here"

# Anthropic Configuration  
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-api-key-here"

# Optional: Custom base URLs
export OPENAI_BASE_URL="https://api.openai.com/v1"  # Default
export ANTHROPIC_BASE_URL="https://api.anthropic.com"  # Default

# Local model configuration
export LOCAL_LLM_BASE_URL="http://localhost:11434"  # Ollama default
```

### 2. Provider Configuration

Create or update `config/llm/providers.yaml`:

```yaml
providers:
  openai:
    api_key_env: "OPENAI_API_KEY"
    base_url: "https://api.openai.com/v1"
    models:
      - "gpt-4"
      - "gpt-3.5-turbo"
    default_model: "gpt-4"
    timeout_seconds: 30
    max_retries: 3
    
  anthropic:
    api_key_env: "ANTHROPIC_API_KEY"
    base_url: "https://api.anthropic.com"
    models:
      - "claude-3-opus-20240229"
      - "claude-3-sonnet-20240229"
      - "claude-3-haiku-20240307"
    default_model: "claude-3-sonnet-20240229"
    timeout_seconds: 45
    max_retries: 3
    
  local:
    base_url: "http://localhost:11434"
    models:
      - "llama2"
      - "mistral"
      - "codellama"
    default_model: "llama2"
    timeout_seconds: 60
    max_retries: 2
    headers:
      # Optional custom headers for local models
      Authorization: "Bearer your-local-token"

# Global settings
default_provider: "openai"
fallback_providers: ["anthropic", "local"]
enable_response_caching: true
cache_ttl_hours: 24
max_concurrent_requests: 5
```

### 3. Test Configuration

Verify your setup:

```bash
# Check LLM provider status
curl -X GET "http://localhost:8000/api/personality/llm/status" \
  -H "X-API-Key: your-api-key"

# Test LLM-enhanced research
curl -X POST "http://localhost:8000/api/personality/research" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "description": "A brilliant detective with exceptional deductive reasoning",
    "use_llm": true,
    "llm_provider": "openai"
  }'
```

## Advanced Configuration

### Provider-Specific Settings

#### OpenAI Configuration

```yaml
openai:
  api_key_env: "OPENAI_API_KEY"
  organization: "org-your-organization-id"  # Optional
  base_url: "https://api.openai.com/v1"
  models:
    - "gpt-4-1106-preview"  # Latest GPT-4
    - "gpt-4"
    - "gpt-3.5-turbo-1106"
  default_model: "gpt-4"
  request_settings:
    temperature: 0.7
    max_tokens: 1500
    top_p: 0.9
    frequency_penalty: 0.0
    presence_penalty: 0.0
  rate_limiting:
    requests_per_minute: 50
    tokens_per_minute: 90000
  retry_settings:
    max_retries: 3
    initial_delay: 1.0
    exponential_base: 2.0
    max_delay: 60.0
```

#### Anthropic Configuration

```yaml
anthropic:
  api_key_env: "ANTHROPIC_API_KEY"
  base_url: "https://api.anthropic.com"
  models:
    - "claude-3-opus-20240229"
    - "claude-3-sonnet-20240229"
    - "claude-3-haiku-20240307"
  default_model: "claude-3-sonnet-20240229"
  request_settings:
    max_tokens: 1500
    temperature: 0.7
  rate_limiting:
    requests_per_minute: 60
    tokens_per_minute: 100000
  retry_settings:
    max_retries: 3
    initial_delay: 1.0
    exponential_base: 2.0
```

#### Local Model Configuration

```yaml
local:
  base_url: "http://localhost:11434"  # Ollama
  # Alternative: "http://localhost:8080"  # LocalAI
  models:
    - "llama2:13b"
    - "mistral:7b"
    - "codellama:13b"
  default_model: "llama2:13b"
  request_settings:
    temperature: 0.7
    max_tokens: 1500
    stream: false
  timeout_seconds: 120  # Local models may be slower
  headers:
    User-Agent: "covibe-personality-system"
  # Custom model mappings
  model_aliases:
    "llama2": "llama2:13b"
    "mistral": "mistral:7b"
```

### Response Caching Configuration

Configure caching for improved performance and cost savings:

```yaml
caching:
  enabled: true
  backend: "redis"  # Options: memory, redis, file
  redis:
    url: "redis://localhost:6379"
    db: 0
    key_prefix: "covibe:llm:"
  memory:
    max_entries: 1000
    ttl_hours: 24
  file:
    cache_dir: "./cache/llm"
    max_files: 5000
  
  # Cache key configuration
  key_strategy: "semantic"  # Options: exact, semantic, fuzzy
  similarity_threshold: 0.85  # For semantic matching
  
  # Cache policies
  ttl_hours: 24
  invalidate_on_error: true
  compress_responses: true
```

### Cost Optimization

```yaml
cost_optimization:
  enabled: true
  daily_budget_usd: 50.0
  monthly_budget_usd: 1000.0
  
  # Token counting
  track_usage: true
  warn_threshold: 0.8  # Warn at 80% of budget
  
  # Model selection based on cost
  prefer_cheaper_models: true
  model_cost_tiers:
    tier1: ["gpt-3.5-turbo", "claude-3-haiku"]
    tier2: ["gpt-4", "claude-3-sonnet"] 
    tier3: ["gpt-4-1106-preview", "claude-3-opus"]
  
  # Automatic fallbacks
  fallback_on_budget_exceeded: true
  fallback_to_traditional_research: true
```

## Prompt Template Configuration

### Creating Custom Prompts

Create prompt templates in `config/prompts/`:

```yaml
# config/prompts/detailed_personality_analysis.yaml
name: "detailed_personality_analysis"
version: "1.2"
description: "Comprehensive personality analysis with detailed traits"
model_requirements:
  min_context_length: 4000
  preferred_models: ["gpt-4", "claude-3-opus"]

template: |
  You are an expert personality analyst. Analyze the following personality description and provide detailed, structured information.

  Personality Description: "{description}"

  Please provide your analysis in the following JSON format:
  {{
    "name": "Character or personality name",
    "type": "celebrity|fictional|archetype|custom",
    "description": "2-3 sentence personality summary",
    "traits": [
      {{
        "trait": "trait name",
        "intensity": 1-10,
        "description": "detailed explanation of this trait"
      }}
    ],
    "communication_style": {{
      "tone": "overall communication tone",
      "formality": "casual|formal|mixed",
      "verbosity": "concise|moderate|verbose",
      "technical_level": "beginner|intermediate|expert"
    }},
    "mannerisms": ["specific behavioral pattern 1", "specific behavioral pattern 2"],
    "confidence": 0.0-1.0
  }}

  Focus on traits relevant to coding assistance and technical communication.
  Ensure the personality is helpful, ethical, and professional.

variables:
  description: "User-provided personality description"

validation:
  required_fields: ["name", "type", "description", "traits", "communication_style", "mannerisms", "confidence"]
  min_traits: 3
  max_traits: 8
  min_mannerisms: 2
  max_mannerisms: 5
```

### Prompt Selection Strategy

```yaml
# config/prompts/selection_strategy.yaml
selection_strategy:
  default_prompt: "personality_analysis"
  
  # Model-specific prompts
  model_overrides:
    "gpt-4": "detailed_personality_analysis"
    "claude-3-opus": "detailed_personality_analysis"
    "gpt-3.5-turbo": "simple_personality_analysis"
    "claude-3-haiku": "simple_personality_analysis"
  
  # Description-based selection
  description_patterns:
    - pattern: "complex|detailed|nuanced"
      prompt: "detailed_personality_analysis"
    - pattern: "simple|basic|quick"
      prompt: "simple_personality_analysis"
    - pattern: "technical|programming|coding"
      prompt: "technical_personality_analysis"
```

## Security Configuration

### API Key Management

```bash
# Use a secure secrets management system
export OPENAI_API_KEY="$(vault kv get -field=api_key secret/llm/openai)"
export ANTHROPIC_API_KEY="$(vault kv get -field=api_key secret/llm/anthropic)"

# Or use environment-specific files
source /etc/covibe/llm-secrets.env
```

### Input Sanitization

```yaml
security:
  input_sanitization:
    enabled: true
    max_description_length: 2000
    forbidden_patterns:
      - "ignore\\s+previous\\s+instructions"
      - "system\\s*:"
      - "api\\s*key"
      - "password"
    replacement_text: "[FILTERED]"
  
  output_validation:
    enabled: true
    max_response_length: 10000
    content_filters:
      - "personal_information"
      - "harmful_content"
      - "code_injection"
  
  rate_limiting:
    per_user_per_minute: 10
    per_ip_per_minute: 20
    global_per_minute: 1000
```

## Monitoring and Logging

### Metrics Configuration

```yaml
monitoring:
  enabled: true
  metrics:
    - "llm_requests_total"
    - "llm_response_time_seconds"
    - "llm_errors_total"
    - "llm_cost_usd_total"
    - "cache_hit_rate"
  
  alerts:
    - name: "high_error_rate"
      condition: "llm_errors_total / llm_requests_total > 0.1"
      action: "fallback_to_traditional"
    - name: "budget_exceeded"
      condition: "llm_cost_usd_total > daily_budget * 0.9"
      action: "disable_llm_temporarily"
```

### Logging Configuration

```yaml
logging:
  level: "INFO"
  format: "json"
  
  log_requests: true
  log_responses: false  # May contain sensitive data
  log_errors: true
  
  # Sensitive data masking
  mask_api_keys: true
  mask_personal_info: true
  
  # Log rotation
  max_file_size: "100MB"
  max_files: 10
```

## Troubleshooting

### Common Issues

1. **API Key Issues**
   ```bash
   # Verify API key format
   echo $OPENAI_API_KEY | head -c 10  # Should start with "sk-"
   
   # Test API key
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
        "https://api.openai.com/v1/models"
   ```

2. **Network Issues**
   ```bash
   # Test connectivity
   curl -I "https://api.openai.com/v1/models"
   curl -I "https://api.anthropic.com/v1/messages"
   ```

3. **Configuration Issues**
   ```bash
   # Validate YAML syntax
   python -c "import yaml; yaml.safe_load(open('config/llm/providers.yaml'))"
   
   # Check provider status
   curl "http://localhost:8000/api/personality/llm/status"
   ```

### Debug Mode

Enable debug logging for troubleshooting:

```yaml
debug:
  enabled: true
  log_prompts: true
  log_responses: true
  log_timing: true
  save_debug_files: true
  debug_dir: "./debug/llm"
```

## Performance Tuning

### Request Optimization

```yaml
performance:
  # Connection pooling
  connection_pool:
    max_connections: 100
    max_keepalive_connections: 20
    keepalive_expiry: 30
  
  # Request batching
  batching:
    enabled: false  # Not supported by most LLM APIs
    max_batch_size: 1
  
  # Concurrent requests
  concurrency:
    max_concurrent: 10
    per_provider_limit: 5
  
  # Timeouts
  timeouts:
    connect: 10
    read: 60
    total: 90
```

### Model Selection

```yaml
model_selection:
  # Automatic model selection based on description complexity
  auto_select: true
  
  complexity_thresholds:
    simple: 50    # Character count
    medium: 200
    complex: 500
  
  model_mapping:
    simple: ["gpt-3.5-turbo", "claude-3-haiku"]
    medium: ["gpt-4", "claude-3-sonnet"]
    complex: ["gpt-4-1106-preview", "claude-3-opus"]
```

## Best Practices

1. **Cost Management**
   - Set daily/monthly budgets
   - Use cheaper models for simple requests
   - Enable response caching
   - Monitor usage regularly

2. **Performance**
   - Configure appropriate timeouts
   - Use connection pooling
   - Implement proper retry logic
   - Cache responses aggressively

3. **Security**
   - Store API keys securely
   - Sanitize all inputs
   - Validate all outputs
   - Log security events

4. **Reliability**
   - Configure multiple providers
   - Implement fallback mechanisms
   - Monitor provider health
   - Have traditional research as ultimate fallback

5. **Quality**
   - Use appropriate prompts for each use case
   - Validate response structure
   - Monitor confidence scores
   - Review generated personalities regularly