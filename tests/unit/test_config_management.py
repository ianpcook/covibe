"""Unit tests for configuration management utilities."""

import json
import os
import pytest
import tempfile
import time
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from src.covibe.cli.config_manager import ConfigManager
from src.covibe.utils.config_validation import (
    PromptTemplateValidator,
    LLMProviderValidator,
    ValidationIssue,
    ValidationResult,
    validate_prompt_output_format
)
from src.covibe.utils.config_hot_reload import (
    HotReloadManager,
    ConfigurationCache,
    get_hot_reload_manager
)


class TestConfigManager:
    """Test configuration manager functionality."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            yield config_dir
    
    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """Create config manager with temporary directory."""
        return ConfigManager(temp_config_dir)
    
    @pytest.fixture
    def sample_prompt_template(self):
        """Sample prompt template content."""
        return {
            "name": "test_prompt",
            "version": "1.0",
            "model": "gpt-4",
            "max_tokens": 1000,
            "temperature": 0.7,
            "template": "You are a helpful assistant. Task: {{task}}",
            "variables": {
                "task": "Default task description"
            }
        }
    
    def test_list_prompt_templates_empty(self, config_manager):
        """Test listing prompt templates when directory is empty."""
        templates = config_manager.list_prompt_templates()
        assert templates == []
    
    def test_create_prompt_template(self, config_manager, sample_prompt_template):
        """Test creating a new prompt template."""
        file_path = config_manager.create_prompt_template(
            name=sample_prompt_template["name"],
            template=sample_prompt_template["template"],
            model=sample_prompt_template["model"],
            version=sample_prompt_template["version"],
            max_tokens=sample_prompt_template["max_tokens"],
            temperature=sample_prompt_template["temperature"],
            variables=sample_prompt_template["variables"]
        )
        
        # Check file was created
        assert file_path.exists()
        assert file_path.name == "test_prompt.yaml"
        
        # Check file content
        with open(file_path, 'r') as f:
            content = yaml.safe_load(f)
        
        assert content["name"] == sample_prompt_template["name"]
        assert content["template"] == sample_prompt_template["template"]
        assert content["model"] == sample_prompt_template["model"]
    
    def test_list_prompt_templates_with_content(self, config_manager, sample_prompt_template):
        """Test listing prompt templates with content."""
        # Create a template
        config_manager.create_prompt_template(
            name=sample_prompt_template["name"],
            template=sample_prompt_template["template"]
        )
        
        templates = config_manager.list_prompt_templates()
        
        assert len(templates) == 1
        template = templates[0]
        assert template["name"] == sample_prompt_template["name"]
        assert template["file"] == "test_prompt.yaml"
        assert template["version"] == "1.0"
        assert "modified" in template
        assert "size" in template
    
    def test_update_prompt_template(self, config_manager, sample_prompt_template):
        """Test updating an existing prompt template."""
        # Create template
        file_path = config_manager.create_prompt_template(
            name=sample_prompt_template["name"],
            template=sample_prompt_template["template"]
        )
        
        # Update template
        success = config_manager.update_prompt_template(
            file_path.name,
            template="Updated template content",
            model="gpt-3.5-turbo"
        )
        
        assert success is True
        
        # Check updated content
        with open(file_path, 'r') as f:
            content = yaml.safe_load(f)
        
        assert content["template"] == "Updated template content"
        assert content["model"] == "gpt-3.5-turbo"
        assert content["version"] == "1.1"  # Version should auto-increment
    
    def test_update_nonexistent_template(self, config_manager):
        """Test updating a template that doesn't exist."""
        success = config_manager.update_prompt_template(
            "nonexistent.yaml",
            template="Some content"
        )
        
        assert success is False
    
    def test_delete_prompt_template(self, config_manager, sample_prompt_template):
        """Test deleting a prompt template."""
        # Create template
        file_path = config_manager.create_prompt_template(
            name=sample_prompt_template["name"],
            template=sample_prompt_template["template"]
        )
        
        assert file_path.exists()
        
        # Delete template (with backup)
        success = config_manager.delete_prompt_template(file_path.name, backup=True)
        
        assert success is True
        assert not file_path.exists()
        
        # Check backup was created
        backups = config_manager.list_backups()
        assert len(backups) == 1
        assert "test_prompt.yaml" in backups[0]["file"]
    
    def test_delete_template_no_backup(self, config_manager, sample_prompt_template):
        """Test deleting a template without backup."""
        # Create template
        file_path = config_manager.create_prompt_template(
            name=sample_prompt_template["name"],
            template=sample_prompt_template["template"]
        )
        
        # Delete without backup
        success = config_manager.delete_prompt_template(file_path.name, backup=False)
        
        assert success is True
        assert not file_path.exists()
        
        # Check no backup was created
        backups = config_manager.list_backups()
        assert len(backups) == 0
    
    @pytest.mark.asyncio
    async def test_validate_prompt_template(self, config_manager, sample_prompt_template):
        """Test validating a prompt template."""
        # Create valid template
        file_path = config_manager.create_prompt_template(
            name=sample_prompt_template["name"],
            template=sample_prompt_template["template"],
            variables=sample_prompt_template["variables"]
        )
        
        result = await config_manager.validate_prompt_template(file_path.name)
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_validate_invalid_template(self, config_manager):
        """Test validating an invalid prompt template."""
        # Create invalid template (missing required fields)
        invalid_template = {
            "template": "Hello {{undefined_var}}"
        }
        
        file_path = config_manager.prompts_dir / "invalid.yaml"
        with open(file_path, 'w') as f:
            yaml.dump(invalid_template, f)
        
        result = await config_manager.validate_prompt_template("invalid.yaml")
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
    
    def test_backup_and_restore(self, config_manager, sample_prompt_template):
        """Test backup and restore functionality."""
        # Create template
        file_path = config_manager.create_prompt_template(
            name=sample_prompt_template["name"],
            template=sample_prompt_template["template"]
        )
        
        # Create backup
        backup_path = config_manager.backup_prompt_template(file_path.name)
        
        assert backup_path.exists()
        assert backup_path.parent == config_manager.backups_dir
        
        # Delete original
        file_path.unlink()
        assert not file_path.exists()
        
        # Restore from backup
        success = config_manager.restore_prompt_template(backup_path.name)
        
        assert success is True
        assert file_path.exists()
    
    @pytest.mark.asyncio
    async def test_test_llm_providers_missing_config(self, config_manager):
        """Test LLM provider testing with missing config file."""
        results = await config_manager.test_llm_providers()
        
        assert "error" in results
        assert "not found" in results["error"]
    
    @pytest.mark.asyncio
    async def test_test_llm_providers_with_config(self, config_manager):
        """Test LLM provider testing with config file."""
        # Create provider config
        provider_config = {
            "providers": {
                "openai": {
                    "api_key_env": "OPENAI_API_KEY",
                    "base_url": "https://api.openai.com/v1",
                    "models": ["gpt-4"],
                    "default_model": "gpt-4"
                }
            }
        }
        
        provider_file = config_manager.llm_dir / "providers.yaml"
        with open(provider_file, 'w') as f:
            yaml.dump(provider_config, f)
        
        with patch.dict(os.environ, {}, clear=True):  # Clear environment
            results = await config_manager.test_llm_providers()
        
        assert "openai" in results
        assert results["openai"]["connected"] is False
        assert "API key not found" in results["openai"]["error"]


class TestPromptTemplateValidator:
    """Test prompt template validation."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return PromptTemplateValidator()
    
    @pytest.fixture
    def valid_prompt_file(self, tmp_path):
        """Create valid prompt template file."""
        content = {
            "name": "test_prompt",
            "version": "1.0",
            "model": "gpt-4",
            "max_tokens": 1000,
            "temperature": 0.7,
            "template": "Hello {{name}}, how are you?",
            "variables": {
                "name": "World"
            }
        }
        
        file_path = tmp_path / "valid_prompt.yaml"
        with open(file_path, 'w') as f:
            yaml.dump(content, f)
        
        return file_path
    
    @pytest.fixture
    def invalid_prompt_file(self, tmp_path):
        """Create invalid prompt template file."""
        content = {
            "template": "Hello {{undefined_var}}"
            # Missing required fields
        }
        
        file_path = tmp_path / "invalid_prompt.yaml"
        with open(file_path, 'w') as f:
            yaml.dump(content, f)
        
        return file_path
    
    def test_validate_valid_prompt(self, validator, valid_prompt_file):
        """Test validating a valid prompt template."""
        result = validator.validate_prompt_file(valid_prompt_file)
        
        assert result.valid is True
        assert len(result.errors) == 0
    
    def test_validate_invalid_prompt(self, validator, invalid_prompt_file):
        """Test validating an invalid prompt template."""
        result = validator.validate_prompt_file(invalid_prompt_file)
        
        assert result.valid is False
        assert len(result.errors) > 0
        
        # Check for missing required field error
        error_messages = [issue.message for issue in result.errors]
        assert any("Missing required field: name" in msg for msg in error_messages)
    
    def test_validate_nonexistent_file(self, validator, tmp_path):
        """Test validating a file that doesn't exist."""
        nonexistent_file = tmp_path / "nonexistent.yaml"
        
        result = validator.validate_prompt_file(nonexistent_file)
        
        assert result.valid is False
        assert len(result.errors) == 1
        assert "File not found" in result.errors[0].message
    
    def test_validate_template_with_security_issues(self, validator, tmp_path):
        """Test detecting security issues in templates."""
        content = {
            "name": "security_test",
            "template": "{{data|safe}} and eval(malicious_code)",
            "variables": {}
        }
        
        file_path = tmp_path / "security_test.yaml"
        with open(file_path, 'w') as f:
            yaml.dump(content, f)
        
        result = validator.validate_prompt_file(file_path)
        
        # Should detect security warnings
        security_warnings = [issue for issue in result.warnings if issue.category == 'security']
        assert len(security_warnings) > 0
    
    def test_validate_template_syntax_error(self, validator, tmp_path):
        """Test detecting Jinja2 syntax errors."""
        content = {
            "name": "syntax_error",
            "template": "Hello {{name}",  # Missing closing brace
            "variables": {"name": "World"}
        }
        
        file_path = tmp_path / "syntax_error.yaml"
        with open(file_path, 'w') as f:
            yaml.dump(content, f)
        
        result = validator.validate_prompt_file(file_path)
        
        assert result.valid is False
        syntax_errors = [issue for issue in result.errors if issue.category == 'syntax']
        assert len(syntax_errors) > 0


class TestLLMProviderValidator:
    """Test LLM provider validation."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return LLMProviderValidator()
    
    @pytest.fixture
    def valid_provider_file(self, tmp_path):
        """Create valid provider configuration file."""
        content = {
            "providers": {
                "openai": {
                    "api_key_env": "OPENAI_API_KEY",
                    "base_url": "https://api.openai.com/v1",
                    "models": ["gpt-4", "gpt-3.5-turbo"],
                    "default_model": "gpt-4"
                },
                "local": {
                    "base_url": "http://localhost:11434",
                    "models": ["llama2"],
                    "default_model": "llama2"
                }
            },
            "default_provider": "openai",
            "fallback_providers": ["local"]
        }
        
        file_path = tmp_path / "providers.yaml"
        with open(file_path, 'w') as f:
            yaml.dump(content, f)
        
        return file_path
    
    def test_validate_valid_provider_config(self, validator, valid_provider_file):
        """Test validating a valid provider configuration."""
        result = validator.validate_provider_config(valid_provider_file)
        
        assert result.valid is True
        assert len(result.errors) == 0
    
    def test_validate_missing_providers_section(self, validator, tmp_path):
        """Test validation with missing providers section."""
        content = {
            "default_provider": "openai"
        }
        
        file_path = tmp_path / "missing_providers.yaml"
        with open(file_path, 'w') as f:
            yaml.dump(content, f)
        
        result = validator.validate_provider_config(file_path)
        
        assert result.valid is False
        error_messages = [issue.message for issue in result.errors]
        assert any("Missing required section: providers" in msg for msg in error_messages)
    
    def test_validate_invalid_default_provider(self, validator, tmp_path):
        """Test validation with invalid default provider."""
        content = {
            "providers": {
                "openai": {
                    "api_key_env": "OPENAI_API_KEY",
                    "base_url": "https://api.openai.com/v1",
                    "models": ["gpt-4"],
                    "default_model": "gpt-4"
                }
            },
            "default_provider": "nonexistent"
        }
        
        file_path = tmp_path / "invalid_default.yaml"
        with open(file_path, 'w') as f:
            yaml.dump(content, f)
        
        result = validator.validate_provider_config(file_path)
        
        assert result.valid is False
        error_messages = [issue.message for issue in result.errors]
        assert any("Default provider 'nonexistent' not defined" in msg for msg in error_messages)
    
    def test_validate_missing_required_fields(self, validator, tmp_path):
        """Test validation with missing required fields."""
        content = {
            "providers": {
                "openai": {
                    "base_url": "https://api.openai.com/v1"
                    # Missing api_key_env, models, default_model
                }
            }
        }
        
        file_path = tmp_path / "missing_fields.yaml"
        with open(file_path, 'w') as f:
            yaml.dump(content, f)
        
        result = validator.validate_provider_config(file_path)
        
        assert result.valid is False
        assert len(result.errors) >= 3  # Missing api_key_env, models, default_model


class TestPromptOutputValidation:
    """Test prompt output format validation."""
    
    def test_validate_valid_output(self):
        """Test validating valid LLM output."""
        valid_output = {
            "name": "Test Personality",
            "type": "fictional",
            "description": "A test personality",
            "traits": [
                {
                    "trait": "creative",
                    "intensity": 8,
                    "description": "Very creative person"
                }
            ],
            "communication_style": {
                "tone": "friendly",
                "formality": "casual",
                "verbosity": "moderate",
                "technical_level": "intermediate"
            },
            "mannerisms": ["Uses creative examples"],
            "confidence": 0.9
        }
        
        result = validate_prompt_output_format(json.dumps(valid_output))
        
        assert result.valid is True
        assert len(result.errors) == 0
    
    def test_validate_invalid_json(self):
        """Test validating invalid JSON."""
        invalid_json = '{"name": "Test", "type": '  # Incomplete JSON
        
        result = validate_prompt_output_format(invalid_json)
        
        assert result.valid is False
        assert len(result.errors) > 0
        assert "Invalid JSON format" in result.errors[0].message
    
    def test_validate_missing_required_fields(self):
        """Test validating output with missing required fields."""
        incomplete_output = {
            "name": "Test Personality"
            # Missing type, description, traits, communication_style, confidence
        }
        
        result = validate_prompt_output_format(json.dumps(incomplete_output))
        
        assert result.valid is False
        assert len(result.errors) >= 5  # Missing required fields
    
    def test_validate_invalid_confidence_value(self):
        """Test validating output with invalid confidence value."""
        invalid_output = {
            "name": "Test Personality",
            "type": "fictional",
            "description": "A test personality",
            "traits": [],
            "communication_style": {
                "tone": "friendly",
                "formality": "casual",
                "verbosity": "moderate",
                "technical_level": "intermediate"
            },
            "confidence": 1.5  # Invalid: > 1.0
        }
        
        result = validate_prompt_output_format(json.dumps(invalid_output))
        
        assert result.valid is False
        confidence_errors = [e for e in result.errors if "confidence" in e.message.lower()]
        assert len(confidence_errors) > 0


class TestHotReloadManager:
    """Test hot reload functionality."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            (config_dir / "prompts").mkdir()
            (config_dir / "llm").mkdir()
            yield config_dir
    
    @pytest.fixture
    def hot_reload_manager(self, temp_config_dir):
        """Create hot reload manager with temporary directory."""
        return HotReloadManager(temp_config_dir)
    
    def test_configuration_cache(self):
        """Test configuration caching functionality."""
        cache = ConfigurationCache()
        
        # Test empty cache
        assert cache.get_prompt_config(Path("nonexistent.yaml")) is None
        assert cache.get_provider_config(Path("nonexistent.yaml")) is None
    
    @pytest.mark.asyncio
    async def test_hot_reload_manager_initialization(self, hot_reload_manager):
        """Test hot reload manager initialization."""
        assert not hot_reload_manager.is_watching
        assert len(hot_reload_manager.prompt_change_callbacks) == 0
        assert len(hot_reload_manager.provider_change_callbacks) == 0
    
    def test_callback_management(self, hot_reload_manager):
        """Test adding and removing callbacks."""
        # Test callback functions
        def prompt_callback(path, config):
            pass
        
        def provider_callback(config):
            pass
        
        def error_callback(path, error):
            pass
        
        # Add callbacks
        hot_reload_manager.add_prompt_change_callback(prompt_callback)
        hot_reload_manager.add_provider_change_callback(provider_callback)
        hot_reload_manager.add_error_callback(error_callback)
        
        assert len(hot_reload_manager.prompt_change_callbacks) == 1
        assert len(hot_reload_manager.provider_change_callbacks) == 1
        assert len(hot_reload_manager.error_callbacks) == 1
        
        # Remove callbacks
        hot_reload_manager.remove_prompt_change_callback(prompt_callback)
        hot_reload_manager.remove_provider_change_callback(provider_callback)
        hot_reload_manager.remove_error_callback(error_callback)
        
        assert len(hot_reload_manager.prompt_change_callbacks) == 0
        assert len(hot_reload_manager.provider_change_callbacks) == 0
        assert len(hot_reload_manager.error_callbacks) == 0
    
    def test_get_cache_stats(self, hot_reload_manager):
        """Test getting cache statistics."""
        stats = hot_reload_manager.get_cache_stats()
        
        assert "prompt_configs_cached" in stats
        assert "provider_config_cached" in stats
        assert "total_files_tracked" in stats
        assert "is_watching" in stats
        assert stats["is_watching"] is False
    
    def test_force_reload_all(self, hot_reload_manager):
        """Test forcing reload of all configurations."""
        # This should not raise any exceptions
        hot_reload_manager.force_reload_all()
        
        # Check cache is cleared
        stats = hot_reload_manager.get_cache_stats()
        assert stats["prompt_configs_cached"] == 0
        assert stats["provider_config_cached"] is False
    
    def test_global_hot_reload_manager(self, temp_config_dir):
        """Test global hot reload manager singleton."""
        manager1 = get_hot_reload_manager(temp_config_dir)
        manager2 = get_hot_reload_manager()
        
        # Should return same instance
        assert manager1 is manager2


class TestValidationResult:
    """Test validation result functionality."""
    
    def test_validation_result_properties(self):
        """Test validation result property access."""
        issues = [
            ValidationIssue(level='error', category='test', message='Error message'),
            ValidationIssue(level='warning', category='test', message='Warning message'),
            ValidationIssue(level='info', category='test', message='Info message'),
        ]
        
        result = ValidationResult(valid=False, issues=issues)
        
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert len(result.infos) == 1
        
        assert result.errors[0].level == 'error'
        assert result.warnings[0].level == 'warning'
        assert result.infos[0].level == 'info'
    
    def test_validation_issue_creation(self):
        """Test validation issue creation."""
        issue = ValidationIssue(
            level='error',
            category='syntax',
            message='Test error message',
            location='line 10',
            suggestion='Fix the syntax'
        )
        
        assert issue.level == 'error'
        assert issue.category == 'syntax'
        assert issue.message == 'Test error message'
        assert issue.location == 'line 10'
        assert issue.suggestion == 'Fix the syntax'