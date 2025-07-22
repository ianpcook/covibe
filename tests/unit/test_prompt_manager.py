"""Unit tests for prompt configuration management."""

import pytest
import tempfile
import yaml
from pathlib import Path
from src.covibe.services.prompt_manager import (
    PromptConfig,
    PromptConfigError,
    load_prompt_config,
    render_prompt,
    validate_prompt_variables,
    get_default_prompt_config,
)


class TestPromptConfig:
    """Test PromptConfig dataclass."""
    
    def test_prompt_config_creation(self):
        """Test creating PromptConfig with all fields."""
        config = PromptConfig(
            name="test_prompt",
            version="1.0",
            template="Hello {name}!",
            variables={"name": "World"},
            max_tokens=500,
            temperature=0.8,
            model="gpt-3.5-turbo"
        )
        
        assert config.name == "test_prompt"
        assert config.version == "1.0"
        assert config.template == "Hello {name}!"
        assert config.variables == {"name": "World"}
        assert config.max_tokens == 500
        assert config.temperature == 0.8
        assert config.model == "gpt-3.5-turbo"
    
    def test_prompt_config_from_dict_complete(self):
        """Test creating PromptConfig from complete dictionary."""
        data = {
            "name": "test_prompt",
            "version": "1.0",
            "template": "Hello {name}!",
            "variables": {"name": "World"},
            "max_tokens": 500,
            "temperature": 0.8,
            "model": "gpt-3.5-turbo"
        }
        
        config = PromptConfig.from_dict(data)
        assert config.name == "test_prompt"
        assert config.version == "1.0"
        assert config.template == "Hello {name}!"
        assert config.variables == {"name": "World"}
        assert config.max_tokens == 500
        assert config.temperature == 0.8
        assert config.model == "gpt-3.5-turbo"
    
    def test_prompt_config_from_dict_minimal(self):
        """Test creating PromptConfig from minimal dictionary with defaults."""
        data = {
            "name": "test_prompt",
            "version": "1.0",
            "template": "Hello {name}!"
        }
        
        config = PromptConfig.from_dict(data)
        assert config.name == "test_prompt"
        assert config.version == "1.0"
        assert config.template == "Hello {name}!"
        assert config.variables == {}
        assert config.max_tokens == 1000
        assert config.temperature == 0.7
        assert config.model == "gpt-4"


class TestLoadPromptConfig:
    """Test prompt configuration loading."""
    
    @pytest.mark.asyncio
    async def test_load_valid_prompt_config(self):
        """Test loading valid prompt configuration file."""
        config_data = {
            "name": "test_prompt",
            "version": "1.0",
            "template": "Analyze: {description}",
            "variables": {"description": "test input"},
            "max_tokens": 800,
            "temperature": 0.6,
            "model": "gpt-4"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = Path(f.name)
        
        try:
            config = await load_prompt_config(temp_path)
            assert config.name == "test_prompt"
            assert config.version == "1.0"
            assert config.template == "Analyze: {description}"
            assert config.variables == {"description": "test input"}
            assert config.max_tokens == 800
            assert config.temperature == 0.6
            assert config.model == "gpt-4"
        finally:
            temp_path.unlink()
    
    @pytest.mark.asyncio
    async def test_load_minimal_prompt_config(self):
        """Test loading minimal prompt configuration with defaults."""
        config_data = {
            "name": "minimal_prompt",
            "version": "2.0",
            "template": "Simple template"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = Path(f.name)
        
        try:
            config = await load_prompt_config(temp_path)
            assert config.name == "minimal_prompt"
            assert config.version == "2.0"
            assert config.template == "Simple template"
            assert config.variables == {}
            assert config.max_tokens == 1000
            assert config.temperature == 0.7
            assert config.model == "gpt-4"
        finally:
            temp_path.unlink()
    
    @pytest.mark.asyncio
    async def test_load_nonexistent_file(self):
        """Test loading non-existent file raises FileNotFoundError."""
        nonexistent_path = Path("/nonexistent/path/config.yaml")
        
        with pytest.raises(FileNotFoundError, match="Prompt file not found"):
            await load_prompt_config(nonexistent_path)
    
    @pytest.mark.asyncio
    async def test_load_invalid_yaml(self):
        """Test loading invalid YAML raises PromptConfigError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(PromptConfigError, match="Invalid YAML"):
                await load_prompt_config(temp_path)
        finally:
            temp_path.unlink()
    
    @pytest.mark.asyncio
    async def test_load_missing_required_fields(self):
        """Test loading config missing required fields raises PromptConfigError."""
        config_data = {
            "name": "incomplete_prompt",
            # Missing version and template
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(PromptConfigError, match="Missing required fields"):
                await load_prompt_config(temp_path)
        finally:
            temp_path.unlink()
    
    @pytest.mark.asyncio
    async def test_load_non_dict_yaml(self):
        """Test loading YAML that's not a dictionary raises PromptConfigError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(["list", "instead", "of", "dict"], f)
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(PromptConfigError, match="Invalid YAML structure"):
                await load_prompt_config(temp_path)
        finally:
            temp_path.unlink()


class TestRenderPrompt:
    """Test prompt template rendering."""
    
    @pytest.mark.asyncio
    async def test_render_simple_template(self):
        """Test rendering simple template with variables."""
        config = PromptConfig(
            name="test",
            version="1.0",
            template="Hello {{name}}! You are {{age}} years old.",
            variables={"name": "Alice"},
            max_tokens=1000,
            temperature=0.7,
            model="gpt-4"
        )
        
        result = await render_prompt(config, age=25)
        assert result == "Hello Alice! You are 25 years old."
    
    @pytest.mark.asyncio
    async def test_render_template_override_config_vars(self):
        """Test rendering template with kwargs overriding config variables."""
        config = PromptConfig(
            name="test",
            version="1.0",
            template="Hello {{name}}!",
            variables={"name": "Alice"},
            max_tokens=1000,
            temperature=0.7,
            model="gpt-4"
        )
        
        result = await render_prompt(config, name="Bob")
        assert result == "Hello Bob!"
    
    @pytest.mark.asyncio
    async def test_render_template_no_variables(self):
        """Test rendering template with no variables."""
        config = PromptConfig(
            name="test",
            version="1.0",
            template="Static template with no variables.",
            variables={},
            max_tokens=1000,
            temperature=0.7,
            model="gpt-4"
        )
        
        result = await render_prompt(config)
        assert result == "Static template with no variables."
    
    @pytest.mark.asyncio
    async def test_render_template_complex(self):
        """Test rendering complex template with multiple variables."""
        config = PromptConfig(
            name="test",
            version="1.0",
            template="Analyze: {{description}}\nContext: {{context}}\nOutput format: {{format}}",
            variables={"format": "JSON"},
            max_tokens=1000,
            temperature=0.7,
            model="gpt-4"
        )
        
        result = await render_prompt(
            config, 
            description="personality analysis", 
            context="coding assistant"
        )
        expected = "Analyze: personality analysis\nContext: coding assistant\nOutput format: JSON"
        assert result == expected


class TestValidatePromptVariables:
    """Test prompt variable validation."""
    
    @pytest.mark.asyncio
    async def test_validate_prompt_variables_basic(self):
        """Test basic prompt variable validation."""
        config = PromptConfig(
            name="test",
            version="1.0",
            template="Hello {name}!",
            variables={},
            max_tokens=1000,
            temperature=0.7,
            model="gpt-4"
        )
        
        # For now, this returns empty list - full implementation in later tasks
        missing = await validate_prompt_variables(config, name="Alice")
        assert isinstance(missing, list)


class TestGetDefaultPromptConfig:
    """Test default prompt configuration."""
    
    def test_get_default_prompt_config(self):
        """Test getting default prompt configuration."""
        config = get_default_prompt_config()
        
        assert config.name == "personality_analysis_default"
        assert config.version == "1.0"
        assert "personality analysis expert" in config.template.lower()
        assert "description" in config.variables
        assert config.max_tokens == 1000
        assert config.temperature == 0.7
        assert config.model == "gpt-4"