"""Configuration management CLI utilities for prompt templates and LLM providers."""

import argparse
import asyncio
import json
import os
import shutil
import sys
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Import configuration management modules
from ..services.prompt_manager import (
    PromptConfig, 
    load_prompt_config, 
    get_default_prompt_config,
    PromptConfigError
)
from ..services.llm_provider_config import (
    ProvidersConfig,
    ProviderConfig,
    ProviderHealth,
    load_provider_config
)
from ..services.llm_client import (
    create_openai_client,
    create_anthropic_client,
    create_local_client,
    LLMConnectionError
)


class ConfigManager:
    """Configuration management utilities."""
    
    def __init__(self, config_root: Optional[Path] = None):
        """Initialize configuration manager.
        
        Args:
            config_root: Root directory for configuration files
        """
        self.config_root = config_root or Path("config")
        self.prompts_dir = self.config_root / "prompts"
        self.llm_dir = self.config_root / "llm"
        self.backups_dir = self.config_root / "backups"
        
        # Ensure directories exist
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self.llm_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)
    
    def list_prompt_templates(self) -> List[Dict[str, Any]]:
        """List all available prompt templates.
        
        Returns:
            List of prompt template information
        """
        templates = []
        
        for yaml_file in self.prompts_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r') as f:
                    data = yaml.safe_load(f)
                
                templates.append({
                    "file": yaml_file.name,
                    "name": data.get("name", "Unknown"),
                    "version": data.get("version", "Unknown"),
                    "model": data.get("model", "Unknown"),
                    "size": yaml_file.stat().st_size,
                    "modified": datetime.fromtimestamp(yaml_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                })
                
            except Exception as e:
                templates.append({
                    "file": yaml_file.name,
                    "name": "ERROR",
                    "version": "ERROR",
                    "model": "ERROR",
                    "size": yaml_file.stat().st_size,
                    "modified": datetime.fromtimestamp(yaml_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "error": str(e)
                })
        
        return templates
    
    def create_prompt_template(self, name: str, template: str, **kwargs) -> Path:
        """Create a new prompt template.
        
        Args:
            name: Template name
            template: Prompt template content
            **kwargs: Additional configuration options
            
        Returns:
            Path to created template file
        """
        config = {
            "name": name,
            "version": kwargs.get("version", "1.0"),
            "model": kwargs.get("model", "gpt-4"),
            "max_tokens": kwargs.get("max_tokens", 1000),
            "temperature": kwargs.get("temperature", 0.7),
            "template": template,
            "variables": kwargs.get("variables", {})
        }
        
        # Sanitize filename
        filename = f"{name.lower().replace(' ', '_').replace('-', '_')}.yaml"
        file_path = self.prompts_dir / filename
        
        with open(file_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        return file_path
    
    def update_prompt_template(self, template_file: str, **updates) -> bool:
        """Update an existing prompt template.
        
        Args:
            template_file: Template filename
            **updates: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        file_path = self.prompts_dir / template_file
        
        if not file_path.exists():
            print(f"Template file {template_file} not found")
            return False
        
        try:
            with open(file_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Update fields
            for key, value in updates.items():
                if key in config:
                    config[key] = value
            
            # Update version if other changes made
            if updates and "version" not in updates:
                try:
                    version_parts = config.get("version", "1.0").split(".")
                    minor = int(version_parts[-1]) + 1
                    version_parts[-1] = str(minor)
                    config["version"] = ".".join(version_parts)
                except:
                    config["version"] = "1.1"
            
            with open(file_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
            return True
            
        except Exception as e:
            print(f"Error updating template: {e}")
            return False
    
    def delete_prompt_template(self, template_file: str, backup: bool = True) -> bool:
        """Delete a prompt template.
        
        Args:
            template_file: Template filename
            backup: Whether to create backup before deletion
            
        Returns:
            True if successful, False otherwise
        """
        file_path = self.prompts_dir / template_file
        
        if not file_path.exists():
            print(f"Template file {template_file} not found")
            return False
        
        try:
            if backup:
                self.backup_prompt_template(template_file)
            
            file_path.unlink()
            return True
            
        except Exception as e:
            print(f"Error deleting template: {e}")
            return False
    
    async def validate_prompt_template(self, template_file: str) -> Dict[str, Any]:
        """Validate a prompt template.
        
        Args:
            template_file: Template filename
            
        Returns:
            Validation results
        """
        file_path = self.prompts_dir / template_file
        
        if not file_path.exists():
            return {
                "valid": False,
                "errors": [f"Template file {template_file} not found"]
            }
        
        errors = []
        warnings = []
        
        try:
            # Load and validate configuration
            config = await load_prompt_config(file_path)
            
            # Validate required fields
            if not config.name:
                errors.append("Template name is required")
            
            if not config.template:
                errors.append("Template content is required")
            
            if config.max_tokens <= 0:
                errors.append("max_tokens must be positive")
            
            if not (0.0 <= config.temperature <= 2.0):
                errors.append("temperature must be between 0.0 and 2.0")
            
            # Validate template syntax (basic Jinja2 check)
            try:
                from jinja2 import Template
                Template(config.template)
            except Exception as e:
                errors.append(f"Template syntax error: {e}")
            
            # Check for unused variables
            template_vars = set()
            import re
            var_pattern = r'\{\{\s*(\w+)\s*\}\}'
            template_vars.update(re.findall(var_pattern, config.template))
            
            defined_vars = set(config.variables.keys())
            unused_vars = defined_vars - template_vars
            undefined_vars = template_vars - defined_vars
            
            if unused_vars:
                warnings.append(f"Unused variables: {', '.join(unused_vars)}")
            
            if undefined_vars:
                warnings.append(f"Undefined variables: {', '.join(undefined_vars)}")
            
        except PromptConfigError as e:
            errors.append(f"Configuration error: {e}")
        except Exception as e:
            errors.append(f"Unexpected error: {e}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    async def test_llm_providers(self) -> Dict[str, Dict[str, Any]]:
        """Test connectivity to all configured LLM providers.
        
        Returns:
            Dictionary of provider test results
        """
        provider_config_file = self.llm_dir / "providers.yaml"
        
        if not provider_config_file.exists():
            return {
                "error": f"LLM provider config file not found: {provider_config_file}"
            }
        
        try:
            with open(provider_config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            results = {}
            
            for provider_name, provider_config in config.get("providers", {}).items():
                result = {
                    "name": provider_name,
                    "connected": False,
                    "error": None,
                    "response_time": None
                }
                
                try:
                    start_time = datetime.now()
                    
                    # Create client based on provider type
                    if provider_name == "openai":
                        api_key = os.getenv(provider_config.get("api_key_env", "OPENAI_API_KEY"))
                        if not api_key:
                            result["error"] = f"API key not found in environment: {provider_config.get('api_key_env')}"
                        else:
                            client = await create_openai_client(api_key, provider_config.get("default_model"))
                            connected = await client.validate_connection()
                            result["connected"] = connected
                    
                    elif provider_name == "anthropic":
                        api_key = os.getenv(provider_config.get("api_key_env", "ANTHROPIC_API_KEY"))
                        if not api_key:
                            result["error"] = f"API key not found in environment: {provider_config.get('api_key_env')}"
                        else:
                            client = await create_anthropic_client(api_key, provider_config.get("default_model"))
                            connected = await client.validate_connection()
                            result["connected"] = connected
                    
                    elif provider_name == "local":
                        endpoint = provider_config.get("base_url", "http://localhost:11434")
                        client = await create_local_client(endpoint, provider_config.get("default_model"))
                        connected = await client.validate_connection()
                        result["connected"] = connected
                    
                    else:
                        result["error"] = f"Unknown provider type: {provider_name}"
                    
                    end_time = datetime.now()
                    result["response_time"] = (end_time - start_time).total_seconds()
                    
                except Exception as e:
                    result["error"] = str(e)
                
                results[provider_name] = result
            
            return results
            
        except Exception as e:
            return {
                "error": f"Error loading provider config: {e}"
            }
    
    def backup_prompt_template(self, template_file: str) -> Path:
        """Create backup of a prompt template.
        
        Args:
            template_file: Template filename
            
        Returns:
            Path to backup file
        """
        source_path = self.prompts_dir / template_file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{template_file}_{timestamp}.backup"
        backup_path = self.backups_dir / backup_name
        
        shutil.copy2(source_path, backup_path)
        return backup_path
    
    def restore_prompt_template(self, backup_file: str) -> bool:
        """Restore prompt template from backup.
        
        Args:
            backup_file: Backup filename
            
        Returns:
            True if successful, False otherwise
        """
        backup_path = self.backups_dir / backup_file
        
        if not backup_path.exists():
            print(f"Backup file {backup_file} not found")
            return False
        
        try:
            # Extract original filename from backup name
            original_name = backup_file.replace(".backup", "").split("_")[0] + ".yaml"
            if "_" in backup_file:
                parts = backup_file.split("_")
                if len(parts) >= 2:
                    original_name = "_".join(parts[:-2]) + ".yaml"
            
            restore_path = self.prompts_dir / original_name
            shutil.copy2(backup_path, restore_path)
            return True
            
        except Exception as e:
            print(f"Error restoring template: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups.
        
        Returns:
            List of backup information
        """
        backups = []
        
        for backup_file in self.backups_dir.glob("*.backup"):
            backups.append({
                "file": backup_file.name,
                "size": backup_file.stat().st_size,
                "created": datetime.fromtimestamp(backup_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return sorted(backups, key=lambda x: x["created"], reverse=True)


def create_cli_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(description="Covibe Configuration Manager")
    parser.add_argument("--config-dir", type=Path, default="config", 
                       help="Configuration directory path")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Prompt template commands
    prompt_parser = subparsers.add_parser("prompt", help="Prompt template management")
    prompt_subparsers = prompt_parser.add_subparsers(dest="prompt_action")
    
    # List prompts
    prompt_subparsers.add_parser("list", help="List all prompt templates")
    
    # Create prompt
    create_prompt = prompt_subparsers.add_parser("create", help="Create new prompt template")
    create_prompt.add_argument("name", help="Template name")
    create_prompt.add_argument("template", help="Template content or file path")
    create_prompt.add_argument("--model", default="gpt-4", help="Default model")
    create_prompt.add_argument("--version", default="1.0", help="Template version")
    create_prompt.add_argument("--max-tokens", type=int, default=1000, help="Max tokens")
    create_prompt.add_argument("--temperature", type=float, default=0.7, help="Temperature")
    
    # Update prompt
    update_prompt = prompt_subparsers.add_parser("update", help="Update prompt template")
    update_prompt.add_argument("file", help="Template filename")
    update_prompt.add_argument("--template", help="New template content")
    update_prompt.add_argument("--model", help="New default model")
    update_prompt.add_argument("--max-tokens", type=int, help="New max tokens")
    update_prompt.add_argument("--temperature", type=float, help="New temperature")
    
    # Delete prompt
    delete_prompt = prompt_subparsers.add_parser("delete", help="Delete prompt template")
    delete_prompt.add_argument("file", help="Template filename")
    delete_prompt.add_argument("--no-backup", action="store_true", help="Don't create backup")
    
    # Validate prompt
    validate_prompt = prompt_subparsers.add_parser("validate", help="Validate prompt template")
    validate_prompt.add_argument("file", help="Template filename")
    
    # LLM provider commands
    llm_parser = subparsers.add_parser("llm", help="LLM provider management")
    llm_subparsers = llm_parser.add_subparsers(dest="llm_action")
    
    # Test providers
    llm_subparsers.add_parser("test", help="Test LLM provider connectivity")
    
    # Backup commands
    backup_parser = subparsers.add_parser("backup", help="Backup management")
    backup_subparsers = backup_parser.add_subparsers(dest="backup_action")
    
    # List backups
    backup_subparsers.add_parser("list", help="List all backups")
    
    # Create backup
    backup_create = backup_subparsers.add_parser("create", help="Create backup")
    backup_create.add_argument("file", help="Template filename to backup")
    
    # Restore backup
    backup_restore = backup_subparsers.add_parser("restore", help="Restore from backup")
    backup_restore.add_argument("backup_file", help="Backup filename")
    
    return parser


async def main():
    """Main CLI entry point."""
    parser = create_cli_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize configuration manager
    config_manager = ConfigManager(args.config_dir)
    
    try:
        if args.command == "prompt":
            await handle_prompt_commands(config_manager, args)
        elif args.command == "llm":
            await handle_llm_commands(config_manager, args)
        elif args.command == "backup":
            await handle_backup_commands(config_manager, args)
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


async def handle_prompt_commands(config_manager: ConfigManager, args):
    """Handle prompt template commands."""
    if args.prompt_action == "list":
        templates = config_manager.list_prompt_templates()
        
        if not templates:
            print("No prompt templates found.")
            return
        
        print(f"{'File':<30} {'Name':<20} {'Version':<10} {'Model':<15} {'Modified':<20}")
        print("-" * 95)
        
        for template in templates:
            if "error" in template:
                print(f"{template['file']:<30} {'ERROR':<20} {'ERROR':<10} {'ERROR':<15} {template['modified']:<20}")
            else:
                print(f"{template['file']:<30} {template['name']:<20} {template['version']:<10} {template['model']:<15} {template['modified']:<20}")
    
    elif args.prompt_action == "create":
        # Check if template content is a file path
        template_content = args.template
        if Path(args.template).exists():
            with open(args.template, 'r') as f:
                template_content = f.read()
        
        file_path = config_manager.create_prompt_template(
            args.name,
            template_content,
            model=args.model,
            version=args.version,
            max_tokens=args.max_tokens,
            temperature=args.temperature
        )
        
        print(f"Created prompt template: {file_path}")
    
    elif args.prompt_action == "update":
        updates = {}
        if args.template:
            # Check if template content is a file path
            if Path(args.template).exists():
                with open(args.template, 'r') as f:
                    updates["template"] = f.read()
            else:
                updates["template"] = args.template
        
        if args.model:
            updates["model"] = args.model
        if args.max_tokens:
            updates["max_tokens"] = args.max_tokens
        if args.temperature:
            updates["temperature"] = args.temperature
        
        if updates:
            success = config_manager.update_prompt_template(args.file, **updates)
            if success:
                print(f"Updated prompt template: {args.file}")
            else:
                print(f"Failed to update prompt template: {args.file}")
        else:
            print("No updates specified")
    
    elif args.prompt_action == "delete":
        success = config_manager.delete_prompt_template(args.file, backup=not args.no_backup)
        if success:
            action = "Deleted" if args.no_backup else "Deleted (with backup)"
            print(f"{action} prompt template: {args.file}")
        else:
            print(f"Failed to delete prompt template: {args.file}")
    
    elif args.prompt_action == "validate":
        result = await config_manager.validate_prompt_template(args.file)
        
        if result["valid"]:
            print(f"✓ Template {args.file} is valid")
        else:
            print(f"✗ Template {args.file} has errors:")
            for error in result["errors"]:
                print(f"  - {error}")
        
        if result["warnings"]:
            print("Warnings:")
            for warning in result["warnings"]:
                print(f"  - {warning}")


async def handle_llm_commands(config_manager: ConfigManager, args):
    """Handle LLM provider commands."""
    if args.llm_action == "test":
        print("Testing LLM provider connectivity...")
        results = await config_manager.test_llm_providers()
        
        if "error" in results:
            print(f"Error: {results['error']}")
            return
        
        print(f"{'Provider':<15} {'Status':<12} {'Response Time':<15} {'Error':<50}")
        print("-" * 92)
        
        for provider_name, result in results.items():
            status = "✓ Connected" if result["connected"] else "✗ Failed"
            response_time = f"{result['response_time']:.2f}s" if result["response_time"] else "N/A"
            error = result["error"] or ""
            
            print(f"{provider_name:<15} {status:<12} {response_time:<15} {error:<50}")


async def handle_backup_commands(config_manager: ConfigManager, args):
    """Handle backup commands."""
    if args.backup_action == "list":
        backups = config_manager.list_backups()
        
        if not backups:
            print("No backups found.")
            return
        
        print(f"{'Backup File':<50} {'Size':<10} {'Created':<20}")
        print("-" * 80)
        
        for backup in backups:
            size_kb = backup["size"] // 1024
            print(f"{backup['file']:<50} {size_kb}KB{'':<6} {backup['created']:<20}")
    
    elif args.backup_action == "create":
        backup_path = config_manager.backup_prompt_template(args.file)
        print(f"Created backup: {backup_path}")
    
    elif args.backup_action == "restore":
        success = config_manager.restore_prompt_template(args.backup_file)
        if success:
            print(f"Restored from backup: {args.backup_file}")
        else:
            print(f"Failed to restore from backup: {args.backup_file}")


if __name__ == "__main__":
    asyncio.run(main())