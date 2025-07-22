"""Unit tests for IDE writers with LLM enhancement support."""

import pytest
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from src.covibe.integrations.ide_writers import (
    write_cursor_config,
    write_claude_config,
    write_windsurf_config,
    write_to_ide,
    get_llm_metadata,
    format_llm_metadata_comment,
    format_trait_details,
    format_enhanced_mannerisms,
    WriteResult
)
from src.covibe.models.core import (
    PersonalityConfig,
    PersonalityProfile,
    PersonalityTrait,
    CommunicationStyle,
    ResearchSource,
    PersonalityType,
    FormalityLevel,
    VerbosityLevel,
    TechnicalLevel
)


@pytest.fixture
def traditional_personality_config():
    """Create a traditional (non-LLM) personality configuration for testing."""
    profile = PersonalityProfile(
        id="test-profile-1",
        name="Sherlock Holmes",
        type=PersonalityType.FICTIONAL,
        traits=[
            PersonalityTrait(
                category="character",
                trait="analytical",
                intensity=9,
                examples=["Analyzes evidence methodically", "Thinks logically"]
            ),
            PersonalityTrait(
                category="character",
                trait="observant",
                intensity=10,
                examples=["Notices small details", "Sees what others miss"]
            )
        ],
        communication_style=CommunicationStyle(
            tone="analytical",
            formality=FormalityLevel.FORMAL,
            verbosity=VerbosityLevel.MODERATE,
            technical_level=TechnicalLevel.EXPERT
        ),
        mannerisms=[
            "Makes logical deductions",
            "Speaks with precision",
            "Uses methodical reasoning"
        ],
        sources=[
            ResearchSource(
                type="character_database",
                url=None,
                confidence=0.95,
                last_updated=datetime.now()
            )
        ]
    )
    
    return PersonalityConfig(
        id="test-config-1",
        profile=profile,
        context="A brilliant detective with exceptional analytical abilities and keen observation skills.",
        ide_type="cursor",
        file_path="/test/.cursor/rules/personality.mdc",
        active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def llm_personality_config():
    """Create an LLM-generated personality configuration for testing."""
    profile = PersonalityProfile(
        id="test-profile-2",
        name="Steve Jobs",
        type=PersonalityType.CELEBRITY,
        traits=[
            PersonalityTrait(
                category="llm_generated",
                trait="innovative",
                intensity=10,
                examples=["Thinks different", "Challenges status quo"]
            ),
            PersonalityTrait(
                category="llm_generated", 
                trait="perfectionist",
                intensity=9,
                examples=["Attention to detail", "High standards"]
            ),
            PersonalityTrait(
                category="llm_generated",
                trait="visionary",
                intensity=9,
                examples=["Sees future possibilities", "Long-term thinking"]
            )
        ],
        communication_style=CommunicationStyle(
            tone="inspiring",
            formality=FormalityLevel.CASUAL,
            verbosity=VerbosityLevel.MODERATE,
            technical_level=TechnicalLevel.EXPERT
        ),
        mannerisms=[
            "Uses simple, powerful language",
            "Focuses on user experience",
            "Emphasizes design and simplicity",
            "Tells compelling stories"
        ],
        sources=[
            ResearchSource(
                type="llm_openai",
                url=None,
                confidence=0.87,
                last_updated=datetime(2024, 1, 15, 10, 30, 0)
            )
        ]
    )
    
    return PersonalityConfig(
        id="test-config-2",
        profile=profile,
        context="An innovative tech leader known for revolutionary product design and compelling presentations.",
        ide_type="claude",
        file_path="/test/CLAUDE.md",
        active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


class TestLLMMetadataExtraction:
    """Test LLM metadata extraction and formatting."""
    
    def test_get_llm_metadata_from_llm_source(self, llm_personality_config):
        """Test extracting LLM metadata from LLM-generated profile."""
        metadata = get_llm_metadata(llm_personality_config)
        
        assert metadata is not None
        assert metadata["is_llm_generated"] is True
        assert metadata["provider"] == "openai"
        assert metadata["confidence"] == 0.87
        assert isinstance(metadata["generated_at"], datetime)
    
    def test_get_llm_metadata_from_traditional_source(self, traditional_personality_config):
        """Test extracting metadata from traditional (non-LLM) profile."""
        metadata = get_llm_metadata(traditional_personality_config)
        
        assert metadata is not None
        assert metadata["is_llm_generated"] is False
    
    def test_get_llm_metadata_no_sources(self):
        """Test metadata extraction when no sources are present."""
        profile = PersonalityProfile(
            id="test-no-sources",
            name="Test Profile",
            type=PersonalityType.CUSTOM,
            traits=[],
            communication_style=CommunicationStyle(
                tone="neutral",
                formality=FormalityLevel.MIXED,
                verbosity=VerbosityLevel.MODERATE,
                technical_level=TechnicalLevel.INTERMEDIATE
            ),
            mannerisms=[],
            sources=[]
        )
        
        config = PersonalityConfig(
            id="test-config-no-sources",
            profile=profile,
            context="Test context",
            ide_type="cursor",
            file_path="/test/.cursor/rules/personality.mdc",
            active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        metadata = get_llm_metadata(config)
        assert metadata is None


class TestMetadataFormatting:
    """Test LLM metadata comment formatting."""
    
    def test_format_llm_metadata_comment_markdown(self):
        """Test formatting LLM metadata as markdown comments."""
        metadata = {
            "is_llm_generated": True,
            "provider": "openai",
            "confidence": 0.87,
            "generated_at": datetime(2024, 1, 15, 10, 30, 0)
        }
        
        comment = format_llm_metadata_comment(metadata, "markdown")
        
        assert "<!-- LLM-Generated Personality Configuration -->" in comment
        assert "<!-- Provider: Openai -->" in comment
        assert "<!-- Confidence: 87% -->" in comment
        assert "<!-- Generated: 2024-01-15 10:30:00 UTC -->" in comment
    
    def test_format_llm_metadata_comment_html(self):
        """Test formatting LLM metadata as HTML comments."""
        metadata = {
            "is_llm_generated": True,
            "provider": "anthropic",
            "confidence": 0.92,
            "generated_at": datetime(2024, 1, 15, 14, 45, 30)
        }
        
        comment = format_llm_metadata_comment(metadata, "html")
        
        assert "Provider: Anthropic" in comment
        assert "Confidence: 92%" in comment
        assert "Generated: 2024-01-15 14:45:30 UTC" in comment
    
    def test_format_llm_metadata_comment_non_llm(self):
        """Test formatting metadata for non-LLM generated content."""
        metadata = {"is_llm_generated": False}
        
        comment = format_llm_metadata_comment(metadata, "markdown")
        
        assert comment == ""
    
    def test_format_llm_metadata_comment_none(self):
        """Test formatting when metadata is None."""
        comment = format_llm_metadata_comment(None, "markdown")
        
        assert comment == ""


class TestTraitFormatting:
    """Test trait detail formatting."""
    
    def test_format_trait_details_with_traits(self, llm_personality_config):
        """Test formatting trait details with multiple traits."""
        trait_details = format_trait_details(llm_personality_config)
        
        assert "**Innovative** (10/10): ●●●●●●●●●●" in trait_details
        assert "**Perfectionist** (9/10): ●●●●●●●●●○" in trait_details
        assert "**Visionary** (9/10): ●●●●●●●●●○" in trait_details
        assert "Thinks different" in trait_details
        assert "Attention to detail" in trait_details
    
    def test_format_trait_details_no_traits(self):
        """Test formatting when no traits are present."""
        profile = PersonalityProfile(
            id="test-no-traits",
            name="Test Profile",
            type=PersonalityType.CUSTOM,
            traits=[],
            communication_style=CommunicationStyle(
                tone="neutral",
                formality=FormalityLevel.MIXED,
                verbosity=VerbosityLevel.MODERATE,
                technical_level=TechnicalLevel.INTERMEDIATE
            ),
            mannerisms=[],
            sources=[]
        )
        
        config = PersonalityConfig(
            id="test-config-no-traits",
            profile=profile,
            context="Test context",
            ide_type="cursor",
            file_path="/test/.cursor/rules/personality.mdc",
            active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        trait_details = format_trait_details(config)
        
        assert trait_details == "No specific traits identified."


class TestMannerismFormatting:
    """Test mannerism formatting."""
    
    def test_format_enhanced_mannerisms_with_mannerisms(self, llm_personality_config):
        """Test formatting mannerisms when present."""
        mannerisms = format_enhanced_mannerisms(llm_personality_config)
        
        assert "- Uses simple, powerful language" in mannerisms
        assert "- Focuses on user experience" in mannerisms
        assert "- Emphasizes design and simplicity" in mannerisms
        assert "- Tells compelling stories" in mannerisms
    
    def test_format_enhanced_mannerisms_no_mannerisms(self):
        """Test formatting when no mannerisms are present."""
        profile = PersonalityProfile(
            id="test-no-mannerisms",
            name="Test Profile",
            type=PersonalityType.CUSTOM,
            traits=[],
            communication_style=CommunicationStyle(
                tone="neutral",
                formality=FormalityLevel.MIXED,
                verbosity=VerbosityLevel.MODERATE,
                technical_level=TechnicalLevel.INTERMEDIATE
            ),
            mannerisms=[],
            sources=[]
        )
        
        config = PersonalityConfig(
            id="test-config-no-mannerisms",
            profile=profile,
            context="Test context",
            ide_type="cursor",
            file_path="/test/.cursor/rules/personality.mdc",
            active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        mannerisms = format_enhanced_mannerisms(config)
        
        assert mannerisms == "- No specific mannerisms identified"


class TestCursorWriter:
    """Test Cursor IDE configuration writer."""
    
    @pytest.mark.asyncio
    async def test_write_cursor_config_llm_generated(self, llm_personality_config, tmp_path):
        """Test writing Cursor config for LLM-generated personality."""
        result = await write_cursor_config(llm_personality_config, tmp_path)
        
        assert result.success is True
        assert result.file_path == str(tmp_path / ".cursor" / "rules" / "personality.mdc")
        
        # Check file was created
        config_file = tmp_path / ".cursor" / "rules" / "personality.mdc"
        assert config_file.exists()
        
        # Check file content
        content = config_file.read_text()
        assert "<!-- LLM-Generated Personality Configuration -->" in content
        assert "Steve Jobs" in content
        assert "> **AI Analysis** (Openai): 87% confidence" in content
        assert "**Innovative** (10/10): ●●●●●●●●●●" in content
        assert "Uses simple, powerful language" in content
    
    @pytest.mark.asyncio
    async def test_write_cursor_config_traditional(self, traditional_personality_config, tmp_path):
        """Test writing Cursor config for traditional personality."""
        result = await write_cursor_config(traditional_personality_config, tmp_path)
        
        assert result.success is True
        
        # Check file content
        config_file = tmp_path / ".cursor" / "rules" / "personality.mdc"
        content = config_file.read_text()
        
        # Should not have LLM metadata comments
        assert "<!-- LLM-Generated" not in content
        assert "AI Analysis" not in content
        # But should have personality content
        assert "Sherlock Holmes" in content
        assert "**Analytical** (9/10)" in content


class TestClaudeWriter:
    """Test Claude IDE configuration writer."""
    
    @pytest.mark.asyncio
    async def test_write_claude_config_llm_generated(self, llm_personality_config, tmp_path):
        """Test writing Claude config for LLM-generated personality."""
        result = await write_claude_config(llm_personality_config, tmp_path)
        
        assert result.success is True
        assert result.file_path == str(tmp_path / "CLAUDE.md")
        
        # Check file was created
        config_file = tmp_path / "CLAUDE.md"
        assert config_file.exists()
        
        # Check file content
        content = config_file.read_text()
        assert "<!-- LLM-Generated Personality Configuration -->" in content
        assert "## AI Analysis Details" in content
        assert "**Provider**: Openai" in content
        assert "**Confidence**: 87%" in content
        assert "This personality configuration was created using advanced AI analysis" in content
        assert "Implementation Notes" in content
    
    @pytest.mark.asyncio
    async def test_write_claude_config_traditional(self, traditional_personality_config, tmp_path):
        """Test writing Claude config for traditional personality."""
        result = await write_claude_config(traditional_personality_config, tmp_path)
        
        assert result.success is True
        
        # Check file content
        config_file = tmp_path / "CLAUDE.md"
        content = config_file.read_text()
        
        # Should not have AI analysis section
        assert "## AI Analysis Details" not in content
        assert "This personality configuration was created using advanced AI analysis" not in content
        # But should have personality content
        assert "Sherlock Holmes" in content


class TestWindsurfWriter:
    """Test Windsurf IDE configuration writer."""
    
    @pytest.mark.asyncio
    async def test_write_windsurf_config_llm_generated(self, llm_personality_config, tmp_path):
        """Test writing Windsurf config for LLM-generated personality."""
        result = await write_windsurf_config(llm_personality_config, tmp_path)
        
        assert result.success is True
        assert result.file_path == str(tmp_path / ".windsurf")
        
        # Check file was created
        config_file = tmp_path / ".windsurf"
        assert config_file.exists()
        
        # Check JSON content
        with open(config_file) as f:
            config_data = json.load(f)
        
        assert config_data["personality"]["name"] == "Steve Jobs"
        assert config_data["personality"]["type"] == "celebrity"
        assert config_data["metadata"]["llm_generated"] is True
        assert config_data["metadata"]["llm_provider"] == "openai"
        assert config_data["metadata"]["confidence"] == 0.87
        assert "llm_generated_at" in config_data["metadata"]
        
        # Check traits structure
        traits = config_data["personality"]["traits"]
        assert len(traits) == 3
        assert traits[0]["name"] == "innovative"
        assert traits[0]["intensity"] == 10
        assert "Thinks different" in traits[0]["examples"]
    
    @pytest.mark.asyncio
    async def test_write_windsurf_config_traditional(self, traditional_personality_config, tmp_path):
        """Test writing Windsurf config for traditional personality."""
        result = await write_windsurf_config(traditional_personality_config, tmp_path)
        
        assert result.success is True
        
        # Check JSON content
        config_file = tmp_path / ".windsurf"
        with open(config_file) as f:
            config_data = json.load(f)
        
        assert config_data["personality"]["name"] == "Sherlock Holmes"
        assert "llm_generated" not in config_data["metadata"]
        assert "llm_provider" not in config_data["metadata"]


class TestIDEWriterInterface:
    """Test the main IDE writer interface."""
    
    @pytest.mark.asyncio
    async def test_write_to_ide_cursor(self, llm_personality_config, tmp_path):
        """Test writing to Cursor IDE through main interface."""
        result = await write_to_ide("cursor", llm_personality_config, tmp_path)
        
        assert result.success is True
        assert ".cursor/rules/personality.mdc" in result.file_path
    
    @pytest.mark.asyncio
    async def test_write_to_ide_claude(self, llm_personality_config, tmp_path):
        """Test writing to Claude IDE through main interface."""
        result = await write_to_ide("claude", llm_personality_config, tmp_path)
        
        assert result.success is True
        assert "CLAUDE.md" in result.file_path
    
    @pytest.mark.asyncio
    async def test_write_to_ide_windsurf(self, llm_personality_config, tmp_path):
        """Test writing to Windsurf IDE through main interface."""
        result = await write_to_ide("windsurf", llm_personality_config, tmp_path)
        
        assert result.success is True
        assert ".windsurf" in result.file_path
    
    @pytest.mark.asyncio
    async def test_write_to_ide_unsupported(self, llm_personality_config, tmp_path):
        """Test writing to unsupported IDE type."""
        result = await write_to_ide("unsupported_ide", llm_personality_config, tmp_path)
        
        assert result.success is False
        assert "Unsupported IDE type" in result.message
        assert "cursor, claude, windsurf" in result.message
    
    @pytest.mark.asyncio
    async def test_write_to_ide_case_insensitive(self, llm_personality_config, tmp_path):
        """Test that IDE type matching is case insensitive."""
        result = await write_to_ide("CURSOR", llm_personality_config, tmp_path)
        
        assert result.success is True
        assert ".cursor/rules/personality.mdc" in result.file_path


class TestErrorHandling:
    """Test error handling in IDE writers."""
    
    @pytest.mark.asyncio
    async def test_write_cursor_config_permission_error(self, llm_personality_config):
        """Test handling permission errors when writing Cursor config."""
        # Try to write to a non-existent/non-writable path
        invalid_path = Path("/invalid/nonexistent/path")
        
        result = await write_cursor_config(llm_personality_config, invalid_path)
        
        assert result.success is False
        assert "Failed to write Cursor configuration" in result.message
    
    @pytest.mark.asyncio
    async def test_write_claude_config_permission_error(self, llm_personality_config):
        """Test handling permission errors when writing Claude config."""
        invalid_path = Path("/invalid/nonexistent/path")
        
        result = await write_claude_config(llm_personality_config, invalid_path)
        
        assert result.success is False
        assert "Failed to write Claude configuration" in result.message
    
    @pytest.mark.asyncio
    async def test_write_windsurf_config_permission_error(self, llm_personality_config):
        """Test handling permission errors when writing Windsurf config."""
        invalid_path = Path("/invalid/nonexistent/path")
        
        result = await write_windsurf_config(llm_personality_config, invalid_path)
        
        assert result.success is False
        assert "Failed to write Windsurf configuration" in result.message