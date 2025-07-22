"""Configuration validation utilities for prompt templates and LLM providers."""

import json
import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass
from jinja2 import Template, Environment, meta, exceptions

from ..services.prompt_manager import PromptConfig, PromptConfigError
from ..models.llm import LLMPersonalityResponse


@dataclass
class ValidationIssue:
    """Represents a configuration validation issue."""
    level: str  # 'error', 'warning', 'info'
    category: str  # 'syntax', 'semantic', 'security', 'performance'
    message: str
    location: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    valid: bool
    issues: List[ValidationIssue]
    
    @property
    def errors(self) -> List[ValidationIssue]:
        """Get only error-level issues."""
        return [issue for issue in self.issues if issue.level == 'error']
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get only warning-level issues."""
        return [issue for issue in self.issues if issue.level == 'warning']
    
    @property
    def infos(self) -> List[ValidationIssue]:
        """Get only info-level issues."""
        return [issue for issue in self.issues if issue.level == 'info']


class PromptTemplateValidator:
    """Validator for prompt templates."""
    
    # Security patterns to check for
    SECURITY_PATTERNS = [
        (r'\beval\s*\(', 'Potential code execution risk with eval()'),
        (r'\bexec\s*\(', 'Potential code execution risk with exec()'),
        (r'\b__import__\s*\(', 'Potential import injection risk'),
        (r'\bopen\s*\(', 'Potential file access risk'),
        (r'\bos\.\w+', 'Potential OS command execution risk'),
        (r'\bsubprocess\.\w+', 'Potential subprocess execution risk'),
        (r'{{.*\|.*safe.*}}', 'Unsafe Jinja2 filter usage'),
        (r'password|secret|key|token', 'Potential sensitive information exposure'),
    ]
    
    # Performance patterns to check for
    PERFORMANCE_PATTERNS = [
        (r'{%\s*for\s+.*%}.*{%\s*for\s+.*%}', 'Nested loops may impact performance'),
        (r'{{.*\|.*length.*}}.*{{.*\|.*length.*}}', 'Multiple length operations may be inefficient'),
    ]
    
    def __init__(self):
        """Initialize the validator."""
        self.jinja_env = Environment()
    
    def validate_prompt_file(self, file_path: Path) -> ValidationResult:
        """Validate a prompt template file.
        
        Args:
            file_path: Path to the prompt template YAML file
            
        Returns:
            ValidationResult with validation issues
        """
        issues = []
        
        # Check file existence
        if not file_path.exists():
            issues.append(ValidationIssue(
                level='error',
                category='file',
                message=f"File not found: {file_path}",
                suggestion="Check the file path and ensure the file exists"
            ))
            return ValidationResult(valid=False, issues=issues)
        
        # Check file extension
        if file_path.suffix.lower() not in ['.yaml', '.yml']:
            issues.append(ValidationIssue(
                level='warning',
                category='file',
                message=f"Expected .yaml or .yml extension, got {file_path.suffix}",
                suggestion="Use .yaml or .yml extension for prompt templates"
            ))
        
        try:
            # Load YAML content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                data = yaml.safe_load(content)
            except yaml.YAMLError as e:
                issues.append(ValidationIssue(
                    level='error',
                    category='syntax',
                    message=f"Invalid YAML syntax: {e}",
                    suggestion="Fix YAML syntax errors"
                ))
                return ValidationResult(valid=False, issues=issues)
            
            # Validate YAML structure
            structure_issues = self._validate_yaml_structure(data)
            issues.extend(structure_issues)
            
            # Validate template content
            if 'template' in data:
                template_issues = self._validate_template_content(data['template'])
                issues.extend(template_issues)
                
                # Validate variable consistency
                var_issues = self._validate_template_variables(data['template'], data.get('variables', {}))
                issues.extend(var_issues)
            
            # Validate model configuration
            model_issues = self._validate_model_config(data)
            issues.extend(model_issues)
            
        except Exception as e:
            issues.append(ValidationIssue(
                level='error',
                category='file',
                message=f"Error reading file: {e}",
                suggestion="Check file permissions and encoding"
            ))
        
        # Determine overall validity
        has_errors = any(issue.level == 'error' for issue in issues)
        
        return ValidationResult(valid=not has_errors, issues=issues)
    
    def _validate_yaml_structure(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate the YAML structure of a prompt template."""
        issues = []
        required_fields = ['name', 'template']
        optional_fields = ['version', 'model', 'max_tokens', 'temperature', 'variables']
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                issues.append(ValidationIssue(
                    level='error',
                    category='structure',
                    message=f"Missing required field: {field}",
                    suggestion=f"Add the '{field}' field to the template configuration"
                ))
            elif not data[field]:
                issues.append(ValidationIssue(
                    level='error',
                    category='structure',
                    message=f"Empty required field: {field}",
                    suggestion=f"Provide a value for the '{field}' field"
                ))
        
        # Check field types
        type_checks = {
            'name': str,
            'version': str,
            'model': str,
            'template': str,
            'max_tokens': int,
            'temperature': (int, float),
            'variables': dict
        }
        
        for field, expected_type in type_checks.items():
            if field in data and not isinstance(data[field], expected_type):
                issues.append(ValidationIssue(
                    level='error',
                    category='structure',
                    message=f"Field '{field}' must be of type {expected_type.__name__ if isinstance(expected_type, type) else 'number'}",
                    suggestion=f"Change '{field}' to the correct type"
                ))
        
        # Validate numeric ranges
        if 'max_tokens' in data and isinstance(data['max_tokens'], int):
            if data['max_tokens'] <= 0:
                issues.append(ValidationIssue(
                    level='error',
                    category='structure',
                    message="max_tokens must be positive",
                    suggestion="Set max_tokens to a positive integer"
                ))
            elif data['max_tokens'] > 32000:
                issues.append(ValidationIssue(
                    level='warning',
                    category='performance',
                    message="max_tokens is very high, may cause performance issues",
                    suggestion="Consider reducing max_tokens for better performance"
                ))
        
        if 'temperature' in data and isinstance(data['temperature'], (int, float)):
            if not (0.0 <= data['temperature'] <= 2.0):
                issues.append(ValidationIssue(
                    level='error',
                    category='structure',
                    message="temperature must be between 0.0 and 2.0",
                    suggestion="Set temperature to a value between 0.0 and 2.0"
                ))
        
        # Check for unknown fields
        all_known_fields = set(required_fields + optional_fields)
        unknown_fields = set(data.keys()) - all_known_fields
        
        if unknown_fields:
            issues.append(ValidationIssue(
                level='warning',
                category='structure',
                message=f"Unknown fields: {', '.join(unknown_fields)}",
                suggestion="Remove unknown fields or check for typos"
            ))
        
        return issues
    
    def _validate_template_content(self, template: str) -> List[ValidationIssue]:
        """Validate Jinja2 template content."""
        issues = []
        
        # Check for empty template
        if not template.strip():
            issues.append(ValidationIssue(
                level='error',
                category='template',
                message="Template content is empty",
                suggestion="Add content to the template"
            ))
            return issues
        
        # Validate Jinja2 syntax
        try:
            parsed = self.jinja_env.parse(template)
        except exceptions.TemplateSyntaxError as e:
            issues.append(ValidationIssue(
                level='error',
                category='syntax',
                message=f"Jinja2 syntax error: {e}",
                location=f"Line {e.lineno}" if hasattr(e, 'lineno') else None,
                suggestion="Fix the Jinja2 syntax error"
            ))
            return issues
        except Exception as e:
            issues.append(ValidationIssue(
                level='error',
                category='syntax',
                message=f"Template parsing error: {e}",
                suggestion="Check template syntax"
            ))
            return issues
        
        # Security checks
        for pattern, message in self.SECURITY_PATTERNS:
            if re.search(pattern, template, re.IGNORECASE):
                issues.append(ValidationIssue(
                    level='warning',
                    category='security',
                    message=message,
                    suggestion="Review template for security implications"
                ))
        
        # Performance checks
        for pattern, message in self.PERFORMANCE_PATTERNS:
            if re.search(pattern, template, re.IGNORECASE | re.DOTALL):
                issues.append(ValidationIssue(
                    level='info',
                    category='performance',
                    message=message,
                    suggestion="Consider optimizing template for better performance"
                ))
        
        # Check template length
        if len(template) > 10000:
            issues.append(ValidationIssue(
                level='warning',
                category='performance',
                message="Template is very long, may impact performance",
                suggestion="Consider breaking into smaller templates"
            ))
        
        # Check for hardcoded values that should be variables
        hardcoded_patterns = [
            (r'\b(gpt-[34]|claude-\d+)', 'Model name appears to be hardcoded'),
            (r'\b\d{4}-\d{2}-\d{2}\b', 'Date appears to be hardcoded'),
            (r'\b[A-Z]{3,}\b', 'Constant appears to be hardcoded'),
        ]
        
        for pattern, message in hardcoded_patterns:
            if re.search(pattern, template):
                issues.append(ValidationIssue(
                    level='info',
                    category='template',
                    message=message,
                    suggestion="Consider using variables for dynamic values"
                ))
        
        return issues
    
    def _validate_template_variables(self, template: str, variables: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate consistency between template variables and defined variables."""
        issues = []
        
        try:
            # Extract variables from template
            ast = self.jinja_env.parse(template)
            template_vars = meta.find_undeclared_variables(ast)
            defined_vars = set(variables.keys())
            
            # Check for undefined variables
            undefined_vars = template_vars - defined_vars
            if undefined_vars:
                issues.append(ValidationIssue(
                    level='error',
                    category='template',
                    message=f"Undefined variables in template: {', '.join(sorted(undefined_vars))}",
                    suggestion="Define these variables in the 'variables' section"
                ))
            
            # Check for unused variables
            unused_vars = defined_vars - template_vars
            if unused_vars:
                issues.append(ValidationIssue(
                    level='warning',
                    category='template',
                    message=f"Unused variables defined: {', '.join(sorted(unused_vars))}",
                    suggestion="Remove unused variables or use them in the template"
                ))
            
            # Validate variable values
            for var_name, var_value in variables.items():
                if var_value is None:
                    issues.append(ValidationIssue(
                        level='warning',
                        category='variables',
                        message=f"Variable '{var_name}' has null value",
                        suggestion="Provide a default value for the variable"
                    ))
                elif isinstance(var_value, str) and not var_value.strip():
                    issues.append(ValidationIssue(
                        level='warning',
                        category='variables',
                        message=f"Variable '{var_name}' has empty string value",
                        suggestion="Provide a meaningful default value"
                    ))
        
        except Exception as e:
            issues.append(ValidationIssue(
                level='warning',
                category='template',
                message=f"Could not validate template variables: {e}",
                suggestion="Check template syntax"
            ))
        
        return issues
    
    def _validate_model_config(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate model configuration."""
        issues = []
        
        # Known model patterns
        known_models = {
            'openai': [r'gpt-4', r'gpt-3\.5-turbo', r'text-davinci-\d+'],
            'anthropic': [r'claude-3-opus', r'claude-3-sonnet', r'claude-\d+'],
            'local': [r'llama\d*', r'mistral', r'codellama']
        }
        
        model = data.get('model', '')
        if model:
            # Check if model follows known patterns
            model_recognized = False
            for provider, patterns in known_models.items():
                for pattern in patterns:
                    if re.match(pattern, model, re.IGNORECASE):
                        model_recognized = True
                        break
                if model_recognized:
                    break
            
            if not model_recognized:
                issues.append(ValidationIssue(
                    level='info',
                    category='model',
                    message=f"Unrecognized model name: {model}",
                    suggestion="Verify that the model name is correct and supported"
                ))
        
        return issues


class LLMProviderValidator:
    """Validator for LLM provider configurations."""
    
    def validate_provider_config(self, file_path: Path) -> ValidationResult:
        """Validate an LLM provider configuration file.
        
        Args:
            file_path: Path to the provider configuration YAML file
            
        Returns:
            ValidationResult with validation issues
        """
        issues = []
        
        # Check file existence
        if not file_path.exists():
            issues.append(ValidationIssue(
                level='error',
                category='file',
                message=f"File not found: {file_path}",
                suggestion="Check the file path and ensure the file exists"
            ))
            return ValidationResult(valid=False, issues=issues)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Validate structure
            structure_issues = self._validate_provider_structure(data)
            issues.extend(structure_issues)
            
            # Validate individual providers
            if 'providers' in data:
                for provider_name, provider_config in data['providers'].items():
                    provider_issues = self._validate_individual_provider(provider_name, provider_config)
                    issues.extend(provider_issues)
            
            # Validate default and fallback settings
            settings_issues = self._validate_provider_settings(data)
            issues.extend(settings_issues)
            
        except yaml.YAMLError as e:
            issues.append(ValidationIssue(
                level='error',
                category='syntax',
                message=f"Invalid YAML syntax: {e}",
                suggestion="Fix YAML syntax errors"
            ))
        except Exception as e:
            issues.append(ValidationIssue(
                level='error',
                category='file',
                message=f"Error reading file: {e}",
                suggestion="Check file permissions and encoding"
            ))
        
        # Determine overall validity
        has_errors = any(issue.level == 'error' for issue in issues)
        
        return ValidationResult(valid=not has_errors, issues=issues)
    
    def _validate_provider_structure(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate the overall structure of provider configuration."""
        issues = []
        
        required_sections = ['providers']
        optional_sections = ['default_provider', 'fallback_providers', 'rate_limits', 'retry_config']
        
        # Check required sections
        for section in required_sections:
            if section not in data:
                issues.append(ValidationIssue(
                    level='error',
                    category='structure',
                    message=f"Missing required section: {section}",
                    suggestion=f"Add the '{section}' section to the configuration"
                ))
        
        # Check if providers section is a dictionary
        if 'providers' in data and not isinstance(data['providers'], dict):
            issues.append(ValidationIssue(
                level='error',
                category='structure',
                message="'providers' section must be a dictionary",
                suggestion="Structure providers as key-value pairs"
            ))
        
        # Check for unknown sections
        all_known_sections = set(required_sections + optional_sections)
        unknown_sections = set(data.keys()) - all_known_sections
        
        if unknown_sections:
            issues.append(ValidationIssue(
                level='warning',
                category='structure',
                message=f"Unknown sections: {', '.join(unknown_sections)}",
                suggestion="Remove unknown sections or check for typos"
            ))
        
        return issues
    
    def _validate_individual_provider(self, provider_name: str, config: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate configuration for an individual provider."""
        issues = []
        location = f"providers.{provider_name}"
        
        required_fields = {
            'openai': ['api_key_env', 'base_url', 'models', 'default_model'],
            'anthropic': ['api_key_env', 'base_url', 'models', 'default_model'],
            'local': ['base_url', 'models', 'default_model']
        }
        
        # Determine required fields for provider type
        if provider_name in required_fields:
            provider_required = required_fields[provider_name]
        else:
            # Generic requirements for unknown providers
            provider_required = ['models', 'default_model']
            issues.append(ValidationIssue(
                level='info',
                category='provider',
                message=f"Unknown provider type: {provider_name}",
                location=location,
                suggestion="Verify provider name and configuration requirements"
            ))
        
        # Check required fields
        for field in provider_required:
            if field not in config:
                issues.append(ValidationIssue(
                    level='error',
                    category='provider',
                    message=f"Missing required field '{field}' for provider {provider_name}",
                    location=f"{location}.{field}",
                    suggestion=f"Add the '{field}' field to the provider configuration"
                ))
        
        # Validate specific fields
        if 'api_key_env' in config:
            env_var = config['api_key_env']
            if not os.getenv(env_var):
                issues.append(ValidationIssue(
                    level='warning',
                    category='environment',
                    message=f"Environment variable '{env_var}' not set for provider {provider_name}",
                    location=f"{location}.api_key_env",
                    suggestion=f"Set the {env_var} environment variable"
                ))
        
        if 'base_url' in config:
            url = config['base_url']
            if not (url.startswith('http://') or url.startswith('https://')):
                issues.append(ValidationIssue(
                    level='error',
                    category='provider',
                    message=f"Invalid base_url format for provider {provider_name}",
                    location=f"{location}.base_url",
                    suggestion="Use a valid HTTP or HTTPS URL"
                ))
        
        if 'models' in config:
            models = config['models']
            if not isinstance(models, list) or not models:
                issues.append(ValidationIssue(
                    level='error',
                    category='provider',
                    message=f"'models' must be a non-empty list for provider {provider_name}",
                    location=f"{location}.models",
                    suggestion="Provide a list of supported model names"
                ))
        
        if 'default_model' in config and 'models' in config:
            default_model = config['default_model']
            models = config.get('models', [])
            if isinstance(models, list) and default_model not in models:
                issues.append(ValidationIssue(
                    level='error',
                    category='provider',
                    message=f"Default model '{default_model}' not in models list for provider {provider_name}",
                    location=f"{location}.default_model",
                    suggestion="Choose a default model from the models list"
                ))
        
        return issues
    
    def _validate_provider_settings(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate provider settings like defaults and fallbacks."""
        issues = []
        
        providers = data.get('providers', {})
        provider_names = set(providers.keys())
        
        # Validate default provider
        if 'default_provider' in data:
            default_provider = data['default_provider']
            if default_provider not in provider_names:
                issues.append(ValidationIssue(
                    level='error',
                    category='settings',
                    message=f"Default provider '{default_provider}' not defined in providers",
                    location="default_provider",
                    suggestion="Choose a provider that is defined in the providers section"
                ))
        
        # Validate fallback providers
        if 'fallback_providers' in data:
            fallback_providers = data['fallback_providers']
            if not isinstance(fallback_providers, list):
                issues.append(ValidationIssue(
                    level='error',
                    category='settings',
                    message="'fallback_providers' must be a list",
                    location="fallback_providers",
                    suggestion="Structure fallback providers as a list"
                ))
            else:
                for fallback in fallback_providers:
                    if fallback not in provider_names:
                        issues.append(ValidationIssue(
                            level='error',
                            category='settings',
                            message=f"Fallback provider '{fallback}' not defined in providers",
                            location="fallback_providers",
                            suggestion="Choose fallback providers that are defined in the providers section"
                        ))
        
        # Validate rate limits
        if 'rate_limits' in data:
            rate_limits = data['rate_limits']
            if not isinstance(rate_limits, dict):
                issues.append(ValidationIssue(
                    level='error',
                    category='settings',
                    message="'rate_limits' must be a dictionary",
                    location="rate_limits",
                    suggestion="Structure rate limits as provider: limits pairs"
                ))
            else:
                for provider, limits in rate_limits.items():
                    if provider not in provider_names:
                        issues.append(ValidationIssue(
                            level='warning',
                            category='settings',
                            message=f"Rate limits defined for undefined provider '{provider}'",
                            location=f"rate_limits.{provider}",
                            suggestion="Remove rate limits for undefined providers"
                        ))
                    
                    if isinstance(limits, dict):
                        for limit_type, value in limits.items():
                            if limit_type in ['requests_per_minute', 'tokens_per_minute'] and not isinstance(value, int):
                                issues.append(ValidationIssue(
                                    level='error',
                                    category='settings',
                                    message=f"Rate limit '{limit_type}' must be an integer",
                                    location=f"rate_limits.{provider}.{limit_type}",
                                    suggestion="Use integer values for rate limits"
                                ))
        
        return issues


def validate_prompt_output_format(response_text: str) -> ValidationResult:
    """Validate that LLM response matches expected personality format.
    
    Args:
        response_text: Raw LLM response text
        
    Returns:
        ValidationResult indicating if response is valid
    """
    issues = []
    
    try:
        # Try to parse as JSON
        data = json.loads(response_text)
        
        # Check for required fields
        required_fields = ['name', 'type', 'description', 'traits', 'communication_style', 'confidence']
        for field in required_fields:
            if field not in data:
                issues.append(ValidationIssue(
                    level='error',
                    category='format',
                    message=f"Missing required field: {field}",
                    suggestion="Ensure LLM response includes all required fields"
                ))
        
        # Validate field types and values
        if 'type' in data and data['type'] not in ['celebrity', 'fictional', 'archetype', 'custom']:
            issues.append(ValidationIssue(
                level='error',
                category='format',
                message=f"Invalid personality type: {data['type']}",
                suggestion="Use one of: celebrity, fictional, archetype, custom"
            ))
        
        if 'confidence' in data:
            confidence = data['confidence']
            if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
                issues.append(ValidationIssue(
                    level='error',
                    category='format',
                    message="Confidence must be a number between 0.0 and 1.0",
                    suggestion="Provide confidence as a decimal between 0 and 1"
                ))
        
        if 'traits' in data:
            traits = data['traits']
            if not isinstance(traits, list):
                issues.append(ValidationIssue(
                    level='error',
                    category='format',
                    message="Traits must be a list",
                    suggestion="Structure traits as a list of trait objects"
                ))
            else:
                for i, trait in enumerate(traits):
                    if not isinstance(trait, dict):
                        issues.append(ValidationIssue(
                            level='error',
                            category='format',
                            message=f"Trait {i} must be an object",
                            location=f"traits[{i}]",
                            suggestion="Each trait should be an object with trait, intensity, and description"
                        ))
                    else:
                        trait_required = ['trait', 'intensity', 'description']
                        for field in trait_required:
                            if field not in trait:
                                issues.append(ValidationIssue(
                                    level='error',
                                    category='format',
                                    message=f"Trait {i} missing field: {field}",
                                    location=f"traits[{i}].{field}",
                                    suggestion=f"Add {field} to trait object"
                                ))
                        
                        if 'intensity' in trait:
                            intensity = trait['intensity']
                            if not isinstance(intensity, int) or not (1 <= intensity <= 10):
                                issues.append(ValidationIssue(
                                    level='error',
                                    category='format',
                                    message=f"Trait {i} intensity must be integer 1-10",
                                    location=f"traits[{i}].intensity",
                                    suggestion="Use integer values between 1 and 10"
                                ))
        
        # Try to create LLMPersonalityResponse to validate further
        try:
            LLMPersonalityResponse.model_validate(data)
        except Exception as e:
            issues.append(ValidationIssue(
                level='error',
                category='format',
                message=f"Pydantic validation failed: {e}",
                suggestion="Fix data structure to match expected schema"
            ))
    
    except json.JSONDecodeError as e:
        issues.append(ValidationIssue(
            level='error',
            category='format',
            message=f"Invalid JSON format: {e}",
            suggestion="Ensure response is valid JSON"
        ))
    except Exception as e:
        issues.append(ValidationIssue(
            level='error',
            category='format',
            message=f"Validation error: {e}",
            suggestion="Check response format and structure"
        ))
    
    # Determine overall validity
    has_errors = any(issue.level == 'error' for issue in issues)
    
    return ValidationResult(valid=not has_errors, issues=issues)