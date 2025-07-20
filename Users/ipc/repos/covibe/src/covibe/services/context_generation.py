"""Context generation functionality using functional programming principles."""

from typing import Dict, List, Optional
from ..models.core import (
    PersonalityProfile,
    PersonalityTrait,
    CommunicationStyle,
    PersonalityType,
    FormalityLevel,
    VerbosityLevel,
    TechnicalLevel
)


def generate_personality_context(profile: PersonalityProfile) -> str:
    """
    Generate LLM context from a personality profile.
    
    Args:
        profile: PersonalityProfile to generate context for
        
    Returns:
        String containing the generated context for LLM prompting
    """
    context_parts = []
    
    # Add personality introduction
    intro = generate_personality_intro(profile)
    context_parts.append(intro)
    
    # Add communication style guidance
    comm_style = generate_communication_style_context(profile.communication_style)
    context_parts.append(comm_style)
    
    # Add trait-based behavior guidance
    trait_context = generate_trait_context(profile.traits)
    if trait_context:
        context_parts.append(trait_context)
    
    # Add mannerisms and behavioral patterns
    mannerism_context = generate_mannerism_context(profile.mannerisms)
    if mannerism_context:
        context_parts.append(mannerism_context)
    
    # Add response guidelines
    guidelines = generate_response_guidelines(profile)
    context_parts.append(guidelines)
    
    return "\n\n".join(context_parts)


def generate_personality_intro(profile: PersonalityProfile) -> str:
    """Generate personality introduction section."""
    type_descriptions = {
        PersonalityType.CELEBRITY: "real person",
        PersonalityType.FICTIONAL: "fictional character",
        PersonalityType.ARCHETYPE: "personality archetype",
        PersonalityType.CUSTOM: "custom personality"
    }
    
    type_desc = type_descriptions.get(profile.type, "personality")
    
    return f"""# Personality Context: {profile.name}

You are adopting the personality and communication style of {profile.name}, a {type_desc}. 
Your responses should reflect this personality while maintaining technical accuracy and helpfulness in your coding assistance."""


def generate_communication_style_context(style: CommunicationStyle) -> str:
    """Generate communication style guidance."""
    formality_guidance = {
        FormalityLevel.CASUAL: "Use casual, relaxed language. Feel free to use contractions and informal expressions.",
        FormalityLevel.FORMAL: "Maintain formal, professional language. Use complete sentences and proper grammar.",
        FormalityLevel.MIXED: "Adapt your formality to the context - casual for simple questions, formal for complex topics."
    }
    
    verbosity_guidance = {
        VerbosityLevel.CONCISE: "Keep responses brief and to the point. Avoid unnecessary elaboration.",
        VerbosityLevel.MODERATE: "Provide balanced responses with appropriate detail without being overly lengthy.",
        VerbosityLevel.VERBOSE: "Give detailed, comprehensive responses with thorough explanations and examples."
    }
    
    technical_guidance = {
        TechnicalLevel.BEGINNER: "Explain technical concepts in simple terms. Avoid jargon and provide basic context.",
        TechnicalLevel.INTERMEDIATE: "Use standard technical terminology with brief explanations when needed.",
        TechnicalLevel.EXPERT: "Use advanced technical language freely. Assume familiarity with complex concepts."
    }
    
    return f"""## Communication Style

**Tone**: {style.tone.title()}
Adopt a {style.tone} tone in your responses.

**Formality**: {style.formality.value.title()}
{formality_guidance[style.formality]}

**Verbosity**: {style.verbosity.value.title()}
{verbosity_guidance[style.verbosity]}

**Technical Level**: {style.technical_level.value.title()}
{technical_guidance[style.technical_level]}"""


def generate_trait_context(traits: List[PersonalityTrait]) -> str:
    """Generate context based on personality traits."""
    if not traits:
        return ""
    
    trait_behaviors = {
        "intelligent": "Demonstrate analytical thinking and provide insightful solutions.",
        "confident": "Express ideas with certainty and conviction.",
        "analytical": "Break down problems systematically and logically.",
        "creative": "Suggest innovative approaches and think outside the box.",
        "leadership": "Take charge of conversations and guide toward solutions.",
        "humorous": "Include appropriate wit and light humor when suitable.",
        "determined": "Show persistence and focus on achieving goals.",
        "empathetic": "Show understanding and consideration for user needs.",
        "independent": "Emphasize self-reliance and individual problem-solving.",
        "direct": "Communicate straightforwardly without unnecessary complexity.",
        "practical": "Focus on actionable, real-world solutions.",
        "resilient": "Maintain optimism and persistence through challenges.",
        "logical": "Emphasize rational, systematic thinking processes.",
        "precise": "Be exact and accurate in explanations and solutions.",
        "systematic": "Approach problems with organized, methodical thinking.",
        "wise": "Share thoughtful insights and learned perspectives.",
        "patient": "Take time to explain concepts thoroughly and calmly.",
        "supportive": "Encourage and assist users in their learning journey.",
        "knowledgeable": "Draw from deep understanding to provide comprehensive help.",
        "authoritative": "Speak with confidence and expertise on technical matters.",
        "disciplined": "Maintain structured, organized approaches to problem-solving.",
        "demanding": "Set high standards and push for excellence in solutions.",
        "adventurous": "Suggest bold, innovative approaches to challenges.",
        "bold": "Take confident stances and propose ambitious solutions.",
        "colorful": "Use vivid language and engaging expressions.",
        "free-spirited": "Embrace unconventional approaches and creative freedom."
    }
    
    context_lines = ["## Personality Traits"]
    context_lines.append("Embody these key personality characteristics in your responses:")
    
    for trait in traits:
        behavior = trait_behaviors.get(trait.trait.lower())
        if behavior:
            intensity_modifier = get_intensity_modifier(trait.intensity)
            context_lines.append(f"- **{trait.trait.title()}** ({intensity_modifier}): {behavior}")
    
    return "\n".join(context_lines)


def get_intensity_modifier(intensity: int) -> str:
    """Get intensity modifier based on trait intensity score."""
    if intensity >= 9:
        return "Very Strong"
    elif intensity >= 7:
        return "Strong"
    elif intensity >= 5:
        return "Moderate"
    elif intensity >= 3:
        return "Mild"
    else:
        return "Subtle"


def generate_mannerism_context(mannerisms: List[str]) -> str:
    """Generate context for behavioral mannerisms."""
    if not mannerisms:
        return ""
    
    context_lines = ["## Behavioral Patterns"]
    context_lines.append("Incorporate these characteristic behaviors and speech patterns:")
    
    for mannerism in mannerisms:
        if mannerism.strip():
            context_lines.append(f"- {mannerism}")
    
    return "\n".join(context_lines)


def generate_response_guidelines(profile: PersonalityProfile) -> str:
    """Generate specific response guidelines based on personality type."""
    base_guidelines = [
        "Always maintain technical accuracy in your coding assistance",
        "Adapt your personality expression to the context and user needs",
        "Balance personality expression with practical helpfulness"
    ]
    
    type_specific_guidelines = {
        PersonalityType.CELEBRITY: [
            "Reference your background and experiences when relevant",
            "Maintain the public persona associated with this personality"
        ],
        PersonalityType.FICTIONAL: [
            "Stay true to the character's established traits and worldview",
            "Reference the character's fictional context when appropriate"
        ],
        PersonalityType.ARCHETYPE: [
            "Embody the archetypal role consistently",
            "Use language and approaches typical of this archetype"
        ],
        PersonalityType.CUSTOM: [
            "Express the unique combination of traits consistently",
            "Maintain coherence in your personality expression"
        ]
    }
    
    guidelines = base_guidelines + type_specific_guidelines.get(profile.type, [])
    
    context_lines = ["## Response Guidelines"]
    for guideline in guidelines:
        context_lines.append(f"- {guideline}")
    
    return "\n".join(context_lines)


def generate_context_for_ide(profile: PersonalityProfile, ide_type: str) -> str:
    """
    Generate IDE-specific context formatting.
    
    Args:
        profile: PersonalityProfile to generate context for
        ide_type: Target IDE type (cursor, claude, windsurf, etc.)
        
    Returns:
        Formatted context string for the specific IDE
    """
    base_context = generate_personality_context(profile)
    
    ide_formatters = {
        "cursor": format_cursor_context,
        "claude": format_claude_context,
        "windsurf": format_windsurf_context,
        "vscode": format_vscode_context,
        "generic": format_generic_context
    }
    
    formatter = ide_formatters.get(ide_type.lower(), format_generic_context)
    return formatter(base_context, profile)


def format_cursor_context(context: str, profile: PersonalityProfile) -> str:
    """Format context for Cursor IDE (.mdc format)."""
    return f"""---
title: {profile.name} Personality
description: Personality context for coding assistant
---

{context}

## Integration Notes
This personality context is designed to work with Cursor's AI assistant to provide coding help with the personality traits of {profile.name}."""


def format_claude_context(context: str, profile: PersonalityProfile) -> str:
    """Format context for Claude IDE (CLAUDE.md format)."""
    return f"""# Claude Personality Configuration: {profile.name}

{context}

---
*This configuration enhances Claude's responses with the personality traits of {profile.name} while maintaining technical accuracy.*"""


def format_windsurf_context(context: str, profile: PersonalityProfile) -> str:
    """Format context for Windsurf IDE (.windsurf format)."""
    return f"""# Windsurf AI Personality: {profile.name}

{context}

## Windsurf Integration
This personality context integrates with Windsurf's AI capabilities to provide {profile.name}-style coding assistance."""


def format_vscode_context(context: str, profile: PersonalityProfile) -> str:
    """Format context for VS Code (settings.json format guidance)."""
    return f"""// VS Code AI Personality Configuration: {profile.name}
// Add this to your settings.json or workspace configuration

{context}

// Note: Integration method depends on your AI extension (GitHub Copilot, etc.)"""


def format_generic_context(context: str, profile: PersonalityProfile) -> str:
    """Format context for generic use."""
    return f"""# AI Personality Context: {profile.name}

{context}

## Usage Instructions
Copy this context into your AI assistant's system prompt or configuration to enable {profile.name} personality traits in coding assistance."""


def create_context_variations(profile: PersonalityProfile) -> Dict[str, str]:
    """
    Create multiple context variations for different use cases.
    
    Args:
        profile: PersonalityProfile to generate contexts for
        
    Returns:
        Dictionary with different context variations
    """
    return {
        "full": generate_personality_context(profile),
        "brief": generate_brief_context(profile),
        "traits_only": generate_trait_context(profile.traits),
        "style_only": generate_communication_style_context(profile.communication_style)
    }


def generate_brief_context(profile: PersonalityProfile) -> str:
    """Generate a brief version of the personality context."""
    key_traits = [t.trait for t in profile.traits[:3]]  # Top 3 traits
    traits_text = ", ".join(key_traits) if key_traits else "balanced"
    
    return f"""# {profile.name} Personality (Brief)

Adopt the personality of {profile.name} in your coding assistance. Key traits: {traits_text}.
Communication style: {profile.communication_style.tone} tone, {profile.communication_style.formality.value} formality, {profile.communication_style.verbosity.value} responses.

Maintain technical accuracy while expressing this personality in your help and explanations."""