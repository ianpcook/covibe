# Prompt Template Configuration Guide

This guide covers creating, customizing, and managing prompt templates for LLM-enhanced personality research in the Covibe system.

## Overview

Prompt templates define how personality descriptions are processed by LLMs to generate structured personality profiles. The template system supports:

- Variable substitution
- Model-specific optimization
- Response validation
- Automatic prompt selection
- Fallback mechanisms

## Template Structure

### Basic Template Format

```yaml
# config/prompts/example_template.yaml
name: "example_template"
version: "1.0"
description: "Example personality analysis template"

# Model compatibility
model_requirements:
  min_context_length: 2000
  max_context_length: 8000
  preferred_models: ["gpt-4", "claude-3-sonnet"]
  fallback_models: ["gpt-3.5-turbo", "claude-3-haiku"]

# The main prompt template
template: |
  You are a personality analysis expert. Analyze the following description.
  
  Description: "{description}"
  
  Provide structured analysis in JSON format.

# Variables used in the template
variables:
  description: "User-provided personality description"
  
# Response validation rules
validation:
  required_fields: ["name", "type", "traits"]
  response_format: "json"
  max_response_length: 5000

# Template metadata
metadata:
  author: "Covibe Team"
  created: "2024-01-15"
  tags: ["personality", "analysis", "structured"]
```

### Advanced Template Features

```yaml
# config/prompts/advanced_template.yaml
name: "advanced_personality_analysis"
version: "2.1"
description: "Advanced template with conditional logic and validation"

# Model-specific variations
model_variations:
  gpt-4:
    template: |
      You are an advanced AI personality analyst with deep understanding of human psychology.
      
      Personality Description: "{description}"
      Context: {context}
      
      Provide comprehensive analysis with the following JSON structure:
      {{detailed_json_schema}}
      
  claude-3-sonnet:
    template: |
      As a thoughtful personality analyst, please examine this description carefully.
      
      Description to analyze: "{description}"
      Additional context: {context}
      
      Please respond with structured JSON following this format:
      {{detailed_json_schema}}
      
  default:
    template: |
      Analyze this personality description: "{description}"
      
      Respond with JSON containing: name, type, traits, communication_style, confidence.

# Dynamic variables
variables:
  description: 
    type: "string"
    required: true
    description: "Main personality description from user"
  context:
    type: "string" 
    required: false
    default: "General coding assistant context"
    description: "Additional context for analysis"
  detailed_json_schema:
    type: "template"
    value: |
      {
        "name": "Personality name or title",
        "type": "celebrity|fictional|archetype|custom",
        "description": "Brief 2-3 sentence summary",
        "traits": [
          {
            "trait": "trait name", 
            "intensity": 1-10,
            "description": "detailed explanation",
            "examples": ["example 1", "example 2"]
          }
        ],
        "communication_style": {
          "tone": "primary communication tone",
          "formality": "casual|formal|mixed",
          "verbosity": "concise|moderate|verbose",
          "technical_level": "beginner|intermediate|expert"
        },
        "mannerisms": ["behavior 1", "behavior 2"],
        "confidence": 0.0-1.0
      }

# Conditional logic
conditions:
  - if: "len(description) > 200"
    then:
      add_to_prompt: "Provide detailed analysis given the comprehensive description."
  - if: "any(word in description.lower() for word in ['technical', 'programming', 'coding'])"
    then:
      add_to_prompt: "Focus on technical communication aspects and coding-related traits."

# Advanced validation
validation:
  required_fields: ["name", "type", "description", "traits", "communication_style", "confidence"]
  field_constraints:
    name:
      min_length: 2
      max_length: 100
    traits:
      min_items: 3
      max_items: 8
    confidence:
      min_value: 0.0
      max_value: 1.0
  response_format: "json"
  max_response_length: 8000
  
# Error handling
error_handling:
  max_retries: 3
  retry_on_validation_failure: true
  fallback_to_simpler_template: true
  fallback_template: "simple_personality_analysis"
```

## Built-in Templates

### 1. Simple Personality Analysis

```yaml
# config/prompts/simple_personality_analysis.yaml
name: "simple_personality_analysis"
version: "1.0"
description: "Fast, basic personality analysis for simple descriptions"

model_requirements:
  min_context_length: 1000
  preferred_models: ["gpt-3.5-turbo", "claude-3-haiku"]

template: |
  Analyze this personality: "{description}"
  
  Respond with JSON:
  {{
    "name": "personality name",
    "type": "celebrity|fictional|archetype|custom", 
    "description": "brief description",
    "traits": [
      {{"trait": "trait name", "intensity": 1-10, "description": "explanation"}}
    ],
    "communication_style": {{
      "tone": "communication tone",
      "formality": "casual|formal|mixed",
      "verbosity": "concise|moderate|verbose",
      "technical_level": "beginner|intermediate|expert"
    }},
    "mannerisms": ["behavior 1", "behavior 2"],
    "confidence": 0.0-1.0
  }}

variables:
  description: "User personality description"

validation:
  required_fields: ["name", "type", "traits", "communication_style", "confidence"]
  min_traits: 2
  max_traits: 5
```

### 2. Detailed Character Analysis

```yaml
# config/prompts/detailed_character_analysis.yaml
name: "detailed_character_analysis"
version: "1.3"
description: "Comprehensive analysis for complex personality descriptions"

model_requirements:
  min_context_length: 4000
  preferred_models: ["gpt-4", "claude-3-opus"]

template: |
  You are a professional character analyst with expertise in psychology and personality assessment.
  
  Please analyze the following personality description in detail:
  
  "{description}"
  
  Consider the following aspects:
  1. Core personality traits and their manifestations
  2. Communication patterns and preferences
  3. Behavioral mannerisms and habits
  4. Technical competence and learning style
  5. Interpersonal dynamics and collaboration style
  
  Provide your analysis in the following structured JSON format:
  
  {{
    "name": "Character name or title",
    "type": "celebrity|fictional|archetype|custom",
    "description": "Comprehensive 3-4 sentence personality summary",
    "traits": [
      {{
        "trait": "specific trait name",
        "intensity": 1-10,
        "description": "detailed explanation of how this trait manifests",
        "examples": ["specific example 1", "specific example 2"],
        "impact_on_coding": "how this affects coding assistance"
      }}
    ],
    "communication_style": {{
      "tone": "primary communication tone with nuances",
      "formality": "casual|formal|mixed",
      "verbosity": "concise|moderate|verbose", 
      "technical_level": "beginner|intermediate|expert",
      "explanation_style": "how they explain complex concepts",
      "feedback_approach": "how they provide feedback and corrections"
    }},
    "mannerisms": [
      "specific behavioral pattern 1",
      "specific behavioral pattern 2", 
      "specific behavioral pattern 3"
    ],
    "collaboration_style": {{
      "teamwork_approach": "how they work with others",
      "leadership_style": "natural|supportive|directive|collaborative",
      "conflict_resolution": "approach to handling disagreements"
    }},
    "learning_preferences": {{
      "explanation_depth": "surface|moderate|deep",
      "example_preference": "abstract|concrete|mixed",
      "pace": "quick|moderate|thorough"
    }},
    "confidence": 0.0-1.0,
    "analysis_notes": "Additional insights or considerations"
  }}

variables:
  description: "Detailed personality description"

validation:
  required_fields: ["name", "type", "description", "traits", "communication_style", "mannerisms", "confidence"]
  min_traits: 4
  max_traits: 8
  min_mannerisms: 3
  max_mannerisms: 6
```

### 3. Technical Personality Focus

```yaml
# config/prompts/technical_personality_analysis.yaml
name: "technical_personality_analysis"
version: "1.1"
description: "Specialized template for technical/programming personalities"

model_requirements:
  min_context_length: 3000
  preferred_models: ["gpt-4", "claude-3-sonnet"]

template: |
  You are analyzing a personality for technical coding assistance. Focus on traits relevant to programming, problem-solving, and technical communication.
  
  Personality Description: "{description}"
  
  Analyze with emphasis on:
  - Technical communication style
  - Problem-solving approach
  - Code review and feedback style
  - Learning and teaching preferences
  - Debugging and troubleshooting approach
  
  Provide structured JSON analysis:
  
  {{
    "name": "Technical personality name",
    "type": "celebrity|fictional|archetype|custom",
    "description": "Technical personality summary focusing on coding traits",
    "traits": [
      {{
        "trait": "technical trait name",
        "intensity": 1-10,
        "description": "how this applies to coding assistance",
        "coding_impact": "specific impact on code quality/style"
      }}
    ],
    "communication_style": {{
      "tone": "technical communication tone",
      "formality": "casual|formal|mixed",
      "verbosity": "concise|moderate|verbose",
      "technical_level": "beginner|intermediate|expert",
      "code_explanation_style": "step-by-step|overview|deep-dive",
      "error_explanation_approach": "direct|gentle|educational"
    }},
    "technical_mannerisms": [
      "specific coding-related behavior 1",
      "specific technical communication pattern 2",
      "specific problem-solving approach 3"
    ],
    "code_style_preferences": {{
      "clarity_vs_brevity": "clarity|brevity|balanced",
      "comment_style": "minimal|moderate|extensive",
      "naming_approach": "descriptive|concise|conventional"
    }},
    "teaching_style": {{
      "explanation_depth": "high-level|detailed|comprehensive",
      "example_preference": "simple|realistic|complex",
      "encouragement_level": "supportive|neutral|challenging"
    }},
    "confidence": 0.0-1.0
  }}

variables:
  description: "Technical personality description"

validation:
  required_fields: ["name", "type", "traits", "communication_style", "technical_mannerisms", "confidence"]
  min_traits: 3
  max_traits: 6
```

## Template Selection Strategies

### Automatic Selection Configuration

```yaml
# config/prompts/selection_strategy.yaml
selection_strategy:
  # Default template for unknown cases
  default_template: "simple_personality_analysis"
  
  # Selection based on description characteristics
  description_analysis:
    enabled: true
    rules:
      - condition: "len(description) < 50"
        template: "simple_personality_analysis"
        reason: "Short description - use simple template"
        
      - condition: "len(description) > 300"
        template: "detailed_character_analysis" 
        reason: "Long description - use detailed template"
        
      - condition: "any(word in description.lower() for word in ['programming', 'coding', 'developer', 'technical', 'engineer'])"
        template: "technical_personality_analysis"
        reason: "Technical keywords detected"
        
      - condition: "any(word in description.lower() for word in ['character', 'fictional', 'movie', 'book', 'story'])"
        template: "detailed_character_analysis"
        reason: "Fictional character detected"
  
  # Model-based selection
  model_preferences:
    "gpt-4": 
      preferred_templates: ["detailed_character_analysis", "technical_personality_analysis"]
      fallback_template: "simple_personality_analysis"
    "gpt-3.5-turbo":
      preferred_templates: ["simple_personality_analysis"]
      fallback_template: "simple_personality_analysis"
    "claude-3-opus":
      preferred_templates: ["detailed_character_analysis"]
      fallback_template: "simple_personality_analysis"
  
  # Performance-based selection
  performance_optimization:
    enabled: true
    fast_mode_templates: ["simple_personality_analysis"]
    quality_mode_templates: ["detailed_character_analysis", "technical_personality_analysis"]
    
  # Cost-based selection
  cost_optimization:
    enabled: true
    budget_conscious_templates: ["simple_personality_analysis"]
    premium_templates: ["detailed_character_analysis"]
```

## Custom Template Development

### Template Creation Process

1. **Define Requirements**
   ```yaml
   # Start with basic metadata
   name: "my_custom_template"
   version: "1.0"
   description: "Custom template for specific use case"
   ```

2. **Design the Prompt**
   ```yaml
   template: |
     Your carefully crafted prompt here.
     
     Use {variables} for dynamic content.
     
     Structure your response requirements clearly.
   ```

3. **Add Validation Rules**
   ```yaml
   validation:
     required_fields: ["field1", "field2"]
     response_format: "json"
     custom_validators:
       - "validate_personality_name"
       - "validate_trait_intensity"
   ```

4. **Test and Iterate**
   ```bash
   # Test template with various inputs
   python scripts/test_template.py my_custom_template
   ```

### Template Variables

#### Built-in Variables
- `{description}` - User-provided personality description
- `{context}` - Additional context information
- `{timestamp}` - Current timestamp
- `{user_id}` - User identifier (if available)

#### Custom Variables
```yaml
variables:
  custom_var:
    type: "string|number|boolean|list"
    required: true|false
    default: "default_value"
    description: "Variable description"
    validation:
      min_length: 1
      max_length: 100
```

### Response Validation

#### Field Validation
```yaml
validation:
  required_fields: ["name", "type", "confidence"]
  
  field_constraints:
    name:
      type: "string"
      min_length: 1
      max_length: 100
      pattern: "^[A-Za-z0-9\\s]+$"
    
    traits:
      type: "array"
      min_items: 1
      max_items: 10
      item_validation:
        required_fields: ["trait", "intensity"]
        field_constraints:
          intensity:
            type: "number"
            min_value: 1
            max_value: 10
    
    confidence:
      type: "number"
      min_value: 0.0
      max_value: 1.0
```

#### Custom Validators
```python
# validators/personality_validators.py
def validate_personality_name(name: str) -> bool:
    """Validate personality name format."""
    if not name or len(name) < 2:
        return False
    return not any(char in name for char in ['<', '>', '{', '}'])

def validate_trait_intensity(intensity: int) -> bool:
    """Validate trait intensity is in valid range."""
    return 1 <= intensity <= 10
```

## Template Testing

### Test Configuration
```yaml
# config/prompts/test_config.yaml
test_cases:
  - name: "simple_celebrity"
    template: "simple_personality_analysis"
    input:
      description: "Tony Stark from Iron Man"
    expected_fields: ["name", "type", "traits", "confidence"]
    expected_values:
      type: "fictional"
      name_contains: "Stark"
  
  - name: "complex_character"
    template: "detailed_character_analysis"
    input:
      description: "A brilliant but arrogant surgeon who becomes a mystical protector of reality"
    expected_fields: ["name", "type", "traits", "communication_style", "confidence"]
    min_traits: 4
    
  - name: "technical_personality"
    template: "technical_personality_analysis"
    input:
      description: "Senior software engineer who loves clean code and mentoring junior developers"
    expected_fields: ["technical_mannerisms", "code_style_preferences"]
```

### Running Tests
```bash
# Test all templates
python scripts/test_templates.py

# Test specific template
python scripts/test_templates.py --template simple_personality_analysis

# Test with custom input
python scripts/test_templates.py --template detailed_character_analysis \
  --input "Custom personality description"

# Performance testing
python scripts/benchmark_templates.py --iterations 100
```

## Best Practices

### Template Design
1. **Clear Instructions**: Be explicit about desired output format
2. **Structured Responses**: Always request JSON or other structured formats
3. **Example Outputs**: Include examples in complex templates
4. **Validation Rules**: Define comprehensive validation for reliability
5. **Fallback Options**: Include simpler alternatives for error cases

### Performance Optimization
1. **Token Efficiency**: Minimize unnecessary tokens in prompts
2. **Model Selection**: Match template complexity to model capabilities
3. **Caching**: Enable caching for frequently used templates
4. **Batching**: Group similar requests when possible

### Quality Assurance
1. **Regular Testing**: Test templates with diverse inputs
2. **Human Review**: Have humans validate template outputs
3. **Feedback Loop**: Collect and analyze user feedback
4. **Version Control**: Track template changes and performance

### Security Considerations
1. **Input Sanitization**: Validate all template variables
2. **Output Filtering**: Check responses for sensitive information
3. **Prompt Injection**: Protect against malicious inputs
4. **Access Control**: Restrict template modification permissions

## Troubleshooting

### Common Issues

1. **Validation Failures**
   ```bash
   # Check template syntax
   python scripts/validate_template.py template_name.yaml
   
   # Test response parsing
   python scripts/test_response_parsing.py --template template_name
   ```

2. **Poor Response Quality**
   ```yaml
   # Add more specific instructions
   template: |
     Be very specific and detailed in your analysis.
     Focus on actionable personality traits.
     Provide concrete examples for each trait.
   ```

3. **Inconsistent Results**
   ```yaml
   # Add constraints and examples
   validation:
     response_format: "json"
     schema_validation: true
     example_response: |
       {"name": "Example Name", "type": "fictional", ...}
   ```

4. **Template Selection Issues**
   ```yaml
   # Review selection strategy
   selection_strategy:
     debug_mode: true
     log_selection_reasoning: true
   ```

### Debug Mode
```yaml
debug:
  enabled: true
  log_prompts: true
  log_responses: true
  save_debug_files: true
  debug_directory: "./debug/templates"
```

## Template Migration

### Version Updates
```yaml
# config/prompts/migration.yaml
migrations:
  - from_version: "1.0"
    to_version: "1.1" 
    changes:
      - "Added technical_level field to communication_style"
      - "Increased max_traits from 5 to 8"
    migration_script: "scripts/migrate_v1_0_to_v1_1.py"
    
  - from_version: "1.1"
    to_version: "2.0"
    changes:
      - "Restructured traits format"
      - "Added collaboration_style section"
    migration_script: "scripts/migrate_v1_1_to_v2_0.py"
```

### Backwards Compatibility
```yaml
compatibility:
  maintain_old_versions: true
  deprecation_warnings: true
  automatic_migration: false
  fallback_to_previous: true
```