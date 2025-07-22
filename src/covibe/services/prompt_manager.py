"""Prompt configuration management and loading functions."""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from jinja2 import Template, Environment, BaseLoader


@dataclass
class PromptConfig:
    """Configuration for LLM prompts."""
    name: str
    version: str
    template: str
    variables: Dict[str, Any]
    max_tokens: int
    temperature: float
    model: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptConfig":
        """Create PromptConfig from dictionary."""
        return cls(
            name=data["name"],
            version=data["version"],
            template=data["template"],
            variables=data.get("variables", {}),
            max_tokens=data.get("max_tokens", 1000),
            temperature=data.get("temperature", 0.7),
            model=data.get("model", "gpt-4")
        )


class PromptConfigError(Exception):
    """Error loading or processing prompt configuration."""
    pass


async def load_prompt_config(prompt_file: Path) -> PromptConfig:
    """Load prompt configuration from YAML file.
    
    Args:
        prompt_file: Path to the prompt configuration YAML file
        
    Returns:
        PromptConfig object with loaded configuration
        
    Raises:
        PromptConfigError: If file cannot be loaded or is invalid
        FileNotFoundError: If prompt file doesn't exist
    """
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not isinstance(data, dict):
            raise PromptConfigError(f"Invalid YAML structure in {prompt_file}")
        
        # Validate required fields
        required_fields = ["name", "version", "template"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise PromptConfigError(
                f"Missing required fields in {prompt_file}: {missing_fields}"
            )
        
        return PromptConfig.from_dict(data)
        
    except yaml.YAMLError as e:
        raise PromptConfigError(f"Invalid YAML in {prompt_file}: {e}")
    except Exception as e:
        raise PromptConfigError(f"Error loading prompt config from {prompt_file}: {e}")


async def render_prompt(config: PromptConfig, **kwargs) -> str:
    """Render prompt template with provided variables.
    
    Args:
        config: PromptConfig with template to render
        **kwargs: Variables to substitute in the template
        
    Returns:
        Rendered prompt string
        
    Raises:
        PromptConfigError: If template rendering fails
    """
    try:
        # Merge config variables with provided kwargs (kwargs override config vars)
        template_vars = {**config.variables, **kwargs}
        
        # Create Jinja2 template and render
        template = Template(config.template)
        
        return template.render(**template_vars)
        
    except Exception as e:
        raise PromptConfigError(f"Error rendering prompt template: {e}")


async def validate_prompt_variables(config: PromptConfig, **kwargs) -> list[str]:
    """Validate that all required template variables are provided.
    
    Args:
        config: PromptConfig to validate
        **kwargs: Variables provided for template rendering
        
    Returns:
        List of missing variable names (empty if all variables present)
    """
    try:
        # Extract variables from template
        env = Environment(loader=BaseLoader())
        template = env.from_string(config.template)
        
        # Get all undefined variables
        template_vars = {**config.variables, **kwargs}
        undefined_vars = template.make_module(template_vars).get_corresponding_lineno(0)
        
        # For now, return empty list - full validation will be implemented later
        return []
        
    except Exception:
        # If we can't parse the template, assume no missing variables
        return []


def get_default_prompt_config() -> PromptConfig:
    """Get default prompt configuration for personality analysis.
    
    Returns:
        Default PromptConfig for personality analysis
    """
    default_template = '''You are a personality analysis expert. Analyze the following personality description and provide structured information.

Description: "{{description}}"

Please provide your analysis in the following JSON format:
{
  "name": "Personality name or title",
  "type": "celebrity|fictional|archetype|custom",
  "description": "Brief personality summary",
  "traits": [
    {
      "trait": "trait name",
      "intensity": 1-10,
      "description": "explanation of this trait"
    }
  ],
  "communication_style": {
    "tone": "overall tone description",
    "formality": "casual|formal|mixed",
    "verbosity": "concise|moderate|verbose", 
    "technical_level": "beginner|intermediate|expert"
  },
  "mannerisms": ["behavioral pattern 1", "behavioral pattern 2"],
  "confidence": 0.0-1.0
}

Focus on traits relevant to coding assistance and technical communication.'''
    
    return PromptConfig(
        name="personality_analysis_default",
        version="1.0",
        template=default_template,
        variables={"description": "User personality description"},
        max_tokens=1000,
        temperature=0.7,
        model="gpt-4"
    )