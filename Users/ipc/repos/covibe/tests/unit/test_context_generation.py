"""Unit tests for context generation functionality."""

import pytest
from covibe.services.context_generation import (
    generate_personality_context,
    generate_personality_intro,
    generate_communication_style_context,
    generate_trait_context,
    generate_mannerism_context,
    generate_response_guidelines,
    generate_context_for_ide,
    create_context_variations,
    generate_brief_context,
    get_intensity_modifier
)
from covibe.models.core import (
    PersonalityProfile,
    PersonalityTrait,
    CommunicationStyle,
    PersonalityType,
    FormalityLevel,
    VerbosityLevel,
    TechnicalLevel,
    ResearchSource
)
from datetime import datetime


@pytest.fixture
def sample_profile():
    """Create a sample personality profile for testing."""
    traits = [
        PersonalityTrait(
            category="personality",
            trait="intelligent",
            intensity=8,
            examples=["Shows analytical thinking"]
        ),
        PersonalityTrait(
            category="personality", 
            trait="humorous",
            intensity=6,
            examples=["Uses wit appropriately"]
        )
    ]
    
    comm_style = CommunicationStyle(
        tone="friendly",
        formality=FormalityLevel.CASUAL,
        verbosity=VerbosityLevel.MODERATE,
        technical_level=TechnicalLevel.INTERMEDIATE
    )
    
    source = ResearchSource(
        type="test",
        url=None,
        confidence=0.9,
        last_updated=datetime.now()
    )
    
    return PersonalityProfile(
        id="test_profile",
        name="Test Personality",
        type=PersonalityType.ARCHETYPE,
        traits=traits,
        communication_style=comm_style,
        mannerisms=["uses clear examples", "asks clarifying questions"],
        sources=[source]
    )


class TestPersonalityContextGeneration:
    """Tests for main personality context generation."""
    
    def test_generate_personality_context(self, sample_profile):
        """Test complete personality context generation."""
        context = generate_personality_context(sample_profile)
        
        assert "Test Personality" in context
        assert "personality archetype" in context
        assert "Communication Style" in context
        assert "Personality Traits" in context
        assert "Behavioral Patterns" in context
        assert "Response Guidelines" in context
    
    def test_generate_personality_intro(self, sample_profile):
        """Test personality introduction generation."""
        intro = generate_personality_intro(sample_profile)
        
        assert "Test Personality" in intro
        assert "personality archetype" in intro
        assert "technical accuracy" in intro
    
    def test_generate_personality_intro_different_types(self):
        """Test intro generation for different personality types."""
        types_and_descriptions = [
            (PersonalityType.CELEBRITY, "real person"),
            (PersonalityType.FICTIONAL, "fictional character"),
            (PersonalityType.CUSTOM, "custom personality")
        ]
        
        for ptype, expected_desc in types_and_descriptions:
            profile = PersonalityProfile(
                id="test",
                name="Test",
                type=ptype,
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
            
            intro = generate_personality_intro(profile)
            assert expected_desc in intro


class TestCommunicationStyleContext:
    """Tests for communication style context generation."""
    
    def test_generate_communication_style_context(self, sample_profile):
        """Test communication style context generation."""
        context = generate_communication_style_context(sample_profile.communication_style)
        
        assert "Communication Style" in context
        assert "Tone" in context
        assert "friendly" in context
        assert "Formality" in context
        assert "Casual" in context
        assert "Verbosity" in context
        assert "Moderate" in context
        assert "Technical Level" in context
        assert "Intermediate" in context
    
    def test_formality_levels(self):
        """Test different formality level guidance."""
        formality_levels = [
            FormalityLevel.CASUAL,
            FormalityLevel.FORMAL,
            FormalityLevel.MIXED
        ]
        
        for formality in formality_levels:
            style = CommunicationStyle(
                tone="neutral",
                formality=formality,
                verbosity=VerbosityLevel.MODERATE,
                technical_level=TechnicalLevel.INTERMEDIATE
            )
            
            context = generate_communication_style_context(style)
            assert formality.value.title() in context
    
    def test_verbosity_levels(self):
        """Test different verbosity level guidance."""
        verbosity_levels = [
            VerbosityLevel.CONCISE,
            VerbosityLevel.MODERATE,
            VerbosityLevel.VERBOSE
        ]
        
        for verbosity in verbosity_levels:
            style = CommunicationStyle(
                tone="neutral",
                formality=FormalityLevel.MIXED,
                verbosity=verbosity,
                technical_level=TechnicalLevel.INTERMEDIATE
            )
            
            context = generate_communication_style_context(style)
            assert verbosity.value.title() in context


class TestTraitContext:
    """Tests for trait context generation."""
    
    def test_generate_trait_context(self, sample_profile):
        """Test trait context generation."""
        context = generate_trait_context(sample_profile.traits)
        
        assert "Personality Traits" in context
        assert "Intelligent" in context
        assert "Humorous" in context
        assert "analytical thinking" in context
    
    def test_generate_trait_context_empty(self):
        """Test trait context generation with empty traits."""
        context = generate_trait_context([])
        assert context == ""
    
    def test_trait_intensity_modifiers(self):
        """Test trait intensity modifier generation."""
        intensities_and_modifiers = [
            (10, "Very Strong"),
            (8, "Strong"),
            (6, "Moderate"),
            (4, "Mild"),
            (2, "Subtle")
        ]
        
        for intensity, expected_modifier in intensities_and_modifiers:
            modifier = get_intensity_modifier(intensity)
            assert modifier == expected_modifier
    
    def test_unknown_trait_handling(self):
        """Test handling of unknown traits."""
        unknown_trait = PersonalityTrait(
            category="test",
            trait="unknown_trait_xyz",
            intensity=5,
            examples=["test example"]
        )
        
        context = generate_trait_context([unknown_trait])
        # Should still generate context even for unknown traits
        assert "Personality Traits" in context


class TestMannerismContext:
    """Tests for mannerism context generation."""
    
    def test_generate_mannerism_context(self, sample_profile):
        """Test mannerism context generation."""
        context = generate_mannerism_context(sample_profile.mannerisms)
        
        assert "Behavioral Patterns" in context
        assert "uses clear examples" in context
        assert "asks clarifying questions" in context
    
    def test_generate_mannerism_context_empty(self):
        """Test mannerism context generation with empty list."""
        context = generate_mannerism_context([])
        assert context == ""
    
    def test_generate_mannerism_context_with_empty_strings(self):
        """Test mannerism context generation filtering empty strings."""
        mannerisms = ["valid mannerism", "", "  ", "another valid one"]
        context = generate_mannerism_context(mannerisms)
        
        assert "valid mannerism" in context
        assert "another valid one" in context
        # Empty strings should be filtered out


class TestResponseGuidelines:
    """Tests for response guidelines generation."""
    
    def test_generate_response_guidelines(self, sample_profile):
        """Test response guidelines generation."""
        guidelines = generate_response_guidelines(sample_profile)
        
        assert "Response Guidelines" in guidelines
        assert "technical accuracy" in guidelines
        assert "archetypal role" in guidelines  # Archetype-specific
    
    def test_response_guidelines_different_types(self):
        """Test response guidelines for different personality types."""
        type_specific_content = {
            PersonalityType.CELEBRITY: "public persona",
            PersonalityType.FICTIONAL: "character's established traits",
            PersonalityType.CUSTOM: "unique combination"
        }
        
        for ptype, expected_content in type_specific_content.items():
            profile = PersonalityProfile(
                id="test",
                name="Test",
                type=ptype,
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
            
            guidelines = generate_response_guidelines(profile)
            assert expected_content in guidelines


class TestIDEContextFormatting:
    """Tests for IDE-specific context formatting."""
    
    def test_generate_context_for_cursor(self, sample_profile):
        """Test Cursor IDE context formatting."""
        context = generate_context_for_ide(sample_profile, "cursor")
        
        assert "---" in context  # YAML frontmatter
        assert "title:" in context
        assert "Test Personality" in context
        assert "Cursor" in context
    
    def test_generate_context_for_claude(self, sample_profile):
        """Test Claude IDE context formatting."""
        context = generate_context_for_ide(sample_profile, "claude")
        
        assert "# Claude Personality Configuration" in context
        assert "Test Personality" in context
        assert "Claude's responses" in context
    
    def test_generate_context_for_windsurf(self, sample_profile):
        """Test Windsurf IDE context formatting."""
        context = generate_context_for_ide(sample_profile, "windsurf")
        
        assert "# Windsurf AI Personality" in context
        assert "Test Personality" in context
        assert "Windsurf" in context
    
    def test_generate_context_for_vscode(self, sample_profile):
        """Test VS Code context formatting."""
        context = generate_context_for_ide(sample_profile, "vscode")
        
        assert "// VS Code AI Personality Configuration" in context
        assert "settings.json" in context
        assert "Test Personality" in context
    
    def test_generate_context_for_generic(self, sample_profile):
        """Test generic context formatting."""
        context = generate_context_for_ide(sample_profile, "unknown_ide")
        
        assert "# AI Personality Context" in context
        assert "Usage Instructions" in context
        assert "Test Personality" in context


class TestContextVariations:
    """Tests for context variation generation."""
    
    def test_create_context_variations(self, sample_profile):
        """Test creating multiple context variations."""
        variations = create_context_variations(sample_profile)
        
        assert "full" in variations
        assert "brief" in variations
        assert "traits_only" in variations
        assert "style_only" in variations
        
        # Each variation should contain relevant content
        assert "Test Personality" in variations["full"]
        assert "Test Personality" in variations["brief"]
        assert "Personality Traits" in variations["traits_only"]
        assert "Communication Style" in variations["style_only"]
    
    def test_generate_brief_context(self, sample_profile):
        """Test brief context generation."""
        brief = generate_brief_context(sample_profile)
        
        assert "Test Personality" in brief
        assert "Brief" in brief
        assert "intelligent" in brief  # Should include key traits
        assert len(brief) < len(generate_personality_context(sample_profile))
    
    def test_brief_context_with_no_traits(self):
        """Test brief context generation with no traits."""
        profile = PersonalityProfile(
            id="test",
            name="Test",
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
        
        brief = generate_brief_context(profile)
        assert "balanced" in brief  # Should use fallback for no traits