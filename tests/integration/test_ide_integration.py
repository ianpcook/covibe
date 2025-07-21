"""Integration tests for IDE-specific functionality with real IDE environments."""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

import pytest

from src.covibe.integrations.ide_detection import detect_ide_environment
from src.covibe.integrations.ide_writers import (
    write_cursor_config,
    write_claude_config, 
    write_windsurf_config,
    write_generic_config
)
from src.covibe.models.core import PersonalityConfig, PersonalityProfile


class TestIDEIntegration:
    """Test IDE integration with real IDE environments."""
    
    @pytest.fixture
    def sample_personality_config(self):
        """Create a sample personality configuration for testing."""
        profile = PersonalityProfile(
            id="test-profile-1",
            name="Tony Stark",
            type="fictional",
            traits=[
                {
                    "category": "communication",
                    "trait": "witty",
                    "intensity": 8,
                    "examples": ["Quick comebacks", "Clever remarks"]
                },
                {
                    "category": "personality", 
                    "trait": "confident",
                    "intensity": 9,
                    "examples": ["Self-assured responses", "Bold statements"]
                }
            ],
            communication_style={
                "tone": "confident",
                "formality": "casual",
                "verbosity": "moderate",
                "technical_level": "expert"
            },
            mannerisms=["Uses technical jargon", "Makes pop culture references"],
            sources=[
                {
                    "type": "fictional_character",
                    "url": "https://marvel.com/characters/iron-man-tony-stark",
                    "confidence": 0.9,
                    "last_updated": "2024-01-01T00:00:00Z"
                }
            ]
        )
        
        return PersonalityConfig(
            id="test-config-1",
            profile=profile,
            context="You are Tony Stark, a genius inventor and billionaire. Respond with confidence and wit, using technical knowledge and occasional humor.",
            ide_type="cursor",
            file_path="/cursor/rules/personality.mdc",
            active=True,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_cursor_ide_detection_and_integration(self, temp_project_dir: Path, sample_personality_config):
        """Test Cursor IDE detection and file writing."""
        # Set up Cursor project structure
        cursor_dir = temp_project_dir / "cursor"
        cursor_dir.mkdir()
        rules_dir = cursor_dir / "rules"
        rules_dir.mkdir()
        
        # Create a dummy cursor config file to simulate Cursor project
        (cursor_dir / "cursor.json").write_text('{"version": "1.0"}')
        
        # Test IDE detection
        ide_info = detect_ide_environment(temp_project_dir)
        assert ide_info["detected_ide"] == "cursor"
        assert ide_info["confidence"] > 0.8
        
        # Test file writing
        result = write_cursor_config(sample_personality_config, temp_project_dir)
        assert result["success"] is True
        
        # Verify file was created
        personality_file = rules_dir / "personality.mdc"
        assert personality_file.exists()
        
        # Verify file content
        content = personality_file.read_text()
        assert "Tony Stark" in content
        assert "genius inventor" in content
        assert "confident and wit" in content
    
    def test_claude_ide_detection_and_integration(self, temp_project_dir: Path, sample_personality_config):
        """Test Claude IDE detection and file writing."""
        # Set up Claude project structure
        (temp_project_dir / ".claude").mkdir()
        (temp_project_dir / ".claude" / "config.json").write_text('{"version": "1.0"}')
        
        # Test IDE detection
        ide_info = detect_ide_environment(temp_project_dir)
        assert ide_info["detected_ide"] == "claude"
        
        # Test file writing
        sample_personality_config.ide_type = "claude"
        sample_personality_config.file_path = "CLAUDE.md"
        
        result = write_claude_config(sample_personality_config, temp_project_dir)
        assert result["success"] is True
        
        # Verify file was created
        claude_file = temp_project_dir / "CLAUDE.md"
        assert claude_file.exists()
        
        # Verify file content
        content = claude_file.read_text()
        assert "# Agent Personality Configuration" in content
        assert "Tony Stark" in content
    
    def test_windsurf_ide_detection_and_integration(self, temp_project_dir: Path, sample_personality_config):
        """Test Windsurf IDE detection and file writing."""
        # Set up Windsurf project structure
        (temp_project_dir / ".windsurf").write_text('{"personality": {}}')
        
        # Test IDE detection
        ide_info = detect_ide_environment(temp_project_dir)
        assert ide_info["detected_ide"] == "windsurf"
        
        # Test file writing
        sample_personality_config.ide_type = "windsurf"
        sample_personality_config.file_path = ".windsurf"
        
        result = write_windsurf_config(sample_personality_config, temp_project_dir)
        assert result["success"] is True
        
        # Verify file was updated
        windsurf_file = temp_project_dir / ".windsurf"
        assert windsurf_file.exists()
        
        # Verify file content (should be valid JSON)
        import json
        content = json.loads(windsurf_file.read_text())
        assert "personality" in content
        assert content["personality"]["name"] == "Tony Stark"
    
    def test_multiple_ide_detection(self, temp_project_dir: Path):
        """Test detection when multiple IDEs are present."""
        # Set up multiple IDE markers
        (temp_project_dir / "cursor").mkdir()
        (temp_project_dir / "cursor" / "cursor.json").write_text('{}')
        (temp_project_dir / ".claude").mkdir()
        (temp_project_dir / "CLAUDE.md").write_text("# Existing Claude config")
        
        # Test detection prioritization
        ide_info = detect_ide_environment(temp_project_dir)
        
        # Should detect multiple IDEs and provide options
        assert len(ide_info["detected_ides"]) >= 2
        assert "cursor" in ide_info["detected_ides"]
        assert "claude" in ide_info["detected_ides"]
    
    def test_generic_writer_fallback(self, temp_project_dir: Path, sample_personality_config):
        """Test generic writer when no specific IDE is detected."""
        # No IDE-specific files in temp directory
        
        ide_info = detect_ide_environment(temp_project_dir)
        assert ide_info["detected_ide"] == "unknown"
        
        # Test generic writer
        sample_personality_config.ide_type = "generic"
        result = write_generic_config(sample_personality_config, temp_project_dir)
        
        assert result["success"] is True
        assert len(result["files_created"]) > 0
        
        # Verify multiple format files were created
        formats = ["cursor", "claude", "windsurf", "generic"]
        for fmt in formats:
            assert any(fmt in file_path for file_path in result["files_created"])
    
    def test_file_permission_handling(self, temp_project_dir: Path, sample_personality_config):
        """Test handling of file permission issues."""
        # Create a read-only directory
        readonly_dir = temp_project_dir / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only
        
        try:
            # Attempt to write to read-only directory
            sample_personality_config.file_path = str(readonly_dir / "personality.mdc")
            result = write_cursor_config(sample_personality_config, temp_project_dir)
            
            # Should handle permission error gracefully
            assert result["success"] is False
            assert "permission" in result["error"].lower()
            
        finally:
            # Restore permissions for cleanup
            readonly_dir.chmod(0o755)
    
    def test_existing_file_backup(self, temp_project_dir: Path, sample_personality_config):
        """Test backup of existing configuration files."""
        # Create existing file
        existing_file = temp_project_dir / "CLAUDE.md"
        existing_content = "# Existing configuration\nSome existing content"
        existing_file.write_text(existing_content)
        
        # Write new configuration
        sample_personality_config.ide_type = "claude"
        result = write_claude_config(sample_personality_config, temp_project_dir)
        
        assert result["success"] is True
        
        # Verify backup was created
        backup_files = list(temp_project_dir.glob("CLAUDE.md.backup.*"))
        assert len(backup_files) > 0
        
        # Verify backup contains original content
        backup_content = backup_files[0].read_text()
        assert existing_content in backup_content
    
    def test_configuration_validation(self, temp_project_dir: Path):
        """Test validation of written configuration files."""
        from src.covibe.integrations.ide_writers import validate_cursor_config
        
        # Set up Cursor project
        cursor_dir = temp_project_dir / "cursor"
        cursor_dir.mkdir()
        rules_dir = cursor_dir / "rules"
        rules_dir.mkdir()
        
        # Create invalid configuration file
        invalid_file = rules_dir / "personality.mdc"
        invalid_file.write_text("Invalid content without proper structure")
        
        # Test validation
        validation_result = validate_cursor_config(temp_project_dir)
        assert validation_result["valid"] is False
        assert len(validation_result["errors"]) > 0
        
        # Create valid configuration file
        valid_content = """# Personality Configuration
        
You are a helpful coding assistant with the following personality:
- Trait: Helpful
- Style: Professional
"""
        invalid_file.write_text(valid_content)
        
        # Test validation again
        validation_result = validate_cursor_config(temp_project_dir)
        assert validation_result["valid"] is True
    
    def test_cross_platform_compatibility(self, temp_project_dir: Path, sample_personality_config):
        """Test cross-platform file path handling."""
        import platform
        
        # Test with different path separators
        if platform.system() == "Windows":
            test_path = "cursor\\rules\\personality.mdc"
        else:
            test_path = "cursor/rules/personality.mdc"
        
        sample_personality_config.file_path = test_path
        
        # Set up directory structure
        cursor_dir = temp_project_dir / "cursor"
        cursor_dir.mkdir()
        rules_dir = cursor_dir / "rules"
        rules_dir.mkdir()
        
        # Test file writing with platform-specific paths
        result = write_cursor_config(sample_personality_config, temp_project_dir)
        assert result["success"] is True
        
        # Verify file was created regardless of path separator
        personality_file = rules_dir / "personality.mdc"
        assert personality_file.exists()
    
    def test_concurrent_file_operations(self, temp_project_dir: Path, sample_personality_config):
        """Test handling of concurrent file operations."""
        import asyncio
        import threading
        
        # Set up Claude project
        (temp_project_dir / ".claude").mkdir()
        
        results = []
        
        def write_config(config_id: str):
            """Write configuration in separate thread."""
            config = sample_personality_config.copy()
            config.id = config_id
            config.profile.name = f"Personality {config_id}"
            result = write_claude_config(config, temp_project_dir)
            results.append(result)
        
        # Start multiple threads writing simultaneously
        threads = []
        for i in range(5):
            thread = threading.Thread(target=write_config, args=[f"config-{i}"])
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all operations completed
        assert len(results) == 5
        successful_writes = sum(1 for r in results if r["success"])
        
        # At least some writes should succeed (file locking may prevent all)
        assert successful_writes > 0
        
        # Verify final file exists and is valid
        claude_file = temp_project_dir / "CLAUDE.md"
        assert claude_file.exists()
        content = claude_file.read_text()
        assert "Personality" in content