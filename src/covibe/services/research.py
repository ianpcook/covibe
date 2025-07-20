"""Personality research functionality using functional programming principles."""

import asyncio
import httpx
import json
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from ..models.core import (
    PersonalityProfile,
    PersonalityTrait,
    CommunicationStyle,
    ResearchSource,
    PersonalityType,
    FormalityLevel,
    VerbosityLevel,
    TechnicalLevel,
    ResearchResult
)
from ..utils.validation import sanitize_text, detect_personality_type


# Research configuration
WIKIPEDIA_API_BASE = "https://en.wikipedia.org/api/rest_v1"
REQUEST_TIMEOUT = 10.0
MAX_CONCURRENT_REQUESTS = 3


def get_archetype_data(query: str) -> Tuple[Optional[Dict[str, Any]], float]:
    """
    Get personality data for common archetypes.
    
    Args:
        query: Description that might contain archetype keywords
        
    Returns:
        Tuple of (archetype_data, confidence_score)
    """
    archetypes = {
        "cowboy": {
            "name": "Cowboy",
            "description": "Independent, rugged, straightforward personality",
            "traits": ["independent", "direct", "practical", "resilient"],
            "communication_style": {
                "tone": "straightforward",
                "formality": "casual",
                "verbosity": "concise"
            },
            "mannerisms": ["uses simple, direct language", "values actions over words"]
        },
        "robot": {
            "name": "Robot/AI",
            "description": "Logical, precise, analytical personality",
            "traits": ["logical", "precise", "analytical", "systematic"],
            "communication_style": {
                "tone": "neutral",
                "formality": "formal",
                "verbosity": "concise"
            },
            "mannerisms": ["uses technical language", "focuses on facts"]
        },
        "drill sergeant": {
            "name": "Drill Sergeant",
            "description": "Authoritative, disciplined, direct personality",
            "traits": ["authoritative", "disciplined", "direct", "demanding"],
            "communication_style": {
                "tone": "commanding",
                "formality": "formal",
                "verbosity": "concise"
            },
            "mannerisms": ["uses imperative language", "focuses on discipline"]
        },
        "mentor": {
            "name": "Wise Mentor",
            "description": "Supportive, knowledgeable, patient personality",
            "traits": ["wise", "patient", "supportive", "knowledgeable"],
            "communication_style": {
                "tone": "encouraging",
                "formality": "mixed",
                "verbosity": "moderate"
            },
            "mannerisms": ["asks guiding questions", "shares wisdom"]
        },
        "monk": {
            "name": "Wise Monk",
            "description": "Peaceful, contemplative, wise personality",
            "traits": ["peaceful", "wise", "contemplative", "patient"],
            "communication_style": {
                "tone": "calm",
                "formality": "formal",
                "verbosity": "moderate"
            },
            "mannerisms": ["speaks thoughtfully", "uses philosophical language", "emphasizes mindfulness"]
        },
        "genius": {
            "name": "Brilliant Genius",
            "description": "Highly intelligent, analytical, innovative personality",
            "traits": ["intelligent", "analytical", "creative", "confident"],
            "communication_style": {
                "tone": "intellectual",
                "formality": "mixed",
                "verbosity": "verbose"
            },
            "mannerisms": ["uses complex explanations", "references advanced concepts"]
        },
        "teacher": {
            "name": "Patient Teacher",
            "description": "Educational, patient, encouraging personality",
            "traits": ["patient", "knowledgeable", "encouraging", "systematic"],
            "communication_style": {
                "tone": "educational",
                "formality": "mixed",
                "verbosity": "moderate"
            },
            "mannerisms": ["explains step by step", "asks clarifying questions"]
        }
    }
    
    query_lower = query.lower()
    
    for archetype_key, archetype_data in archetypes.items():
        if archetype_key in query_lower:
            return archetype_data, 0.9
            
    # Check for related terms
    archetype_keywords = {
        "teacher": "teacher",
        "coach": "mentor",
        "military": "drill sergeant",
        "soldier": "drill sergeant",
        "android": "robot",
        "ai": "robot",
        "artificial intelligence": "robot",
        "buddhist": "monk",
        "meditation": "monk",
        "zen": "monk",
        "spiritual": "monk",
        "smart": "genius",
        "brilliant": "genius",
        "intelligent": "genius"
    }
    
    for keyword, archetype_key in archetype_keywords.items():
        if keyword in query_lower and archetype_key in archetypes:
            return archetypes[archetype_key], 0.7
            
    return None, 0.0


def extract_traits_from_text(text: str) -> List[PersonalityTrait]:
    """Extract personality traits from descriptive text."""
    trait_keywords = {
        "intelligent": ["smart", "brilliant", "genius", "clever"],
        "confident": ["confident", "self-assured", "bold"],
        "analytical": ["analytical", "logical", "systematic"],
        "creative": ["creative", "innovative", "imaginative"],
        "leadership": ["leader", "leadership", "commanding"],
        "humorous": ["funny", "witty", "humorous"],
        "determined": ["determined", "persistent", "driven"],
        "empathetic": ["empathetic", "compassionate", "caring"]
    }
    
    text_lower = text.lower()
    traits = []
    
    for trait_name, keywords in trait_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                trait = PersonalityTrait(
                    category="extracted",
                    trait=trait_name,
                    intensity=6,
                    examples=[f"Described as {keyword}"]
                )
                traits.append(trait)
                break
    
    return traits


def calculate_wikipedia_confidence(data: Dict[str, Any]) -> float:
    """Calculate confidence score for Wikipedia research results."""
    confidence = 0.0
    
    if data.get("title"):
        confidence += 0.3
    if data.get("description"):
        confidence += 0.2
    if data.get("extract") and len(data["extract"]) > 100:
        confidence += 0.4
    if data.get("url"):
        confidence += 0.1
        
    return min(confidence, 1.0)


async def research_wikipedia(query: str, client: httpx.AsyncClient) -> Tuple[Optional[Dict[str, Any]], float]:
    """Research personality information from Wikipedia."""
    try:
        search_url = f"{WIKIPEDIA_API_BASE}/page/summary/{query.replace(' ', '_')}"
        response = await client.get(search_url, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            research_data = {
                "title": data.get("title", ""),
                "description": data.get("description", ""),
                "extract": data.get("extract", ""),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                "source_type": "wikipedia"
            }
            confidence = calculate_wikipedia_confidence(research_data)
            return research_data, confidence
            
    except Exception as e:
        print(f"Wikipedia research failed for {query}: {e}")
        
    return None, 0.0


def create_profile_from_archetype(data: Dict[str, Any], confidence: float) -> Optional[PersonalityProfile]:
    """Create a personality profile from archetype data."""
    try:
        traits = []
        for trait_name in data.get("traits", []):
            trait = PersonalityTrait(
                category="archetype",
                trait=trait_name,
                intensity=8,
                examples=[f"Embodies {trait_name} characteristics"]
            )
            traits.append(trait)
        
        style_data = data.get("communication_style", {})
        comm_style = CommunicationStyle(
            tone=style_data.get("tone", "neutral"),
            formality=FormalityLevel(style_data.get("formality", "mixed")),
            verbosity=VerbosityLevel(style_data.get("verbosity", "moderate")),
            technical_level=TechnicalLevel.INTERMEDIATE
        )
        
        source = ResearchSource(
            type="archetype_database",
            url=None,
            confidence=confidence,
            last_updated=datetime.now()
        )
        
        return PersonalityProfile(
            id=f"arch_{data.get('name', 'unknown').replace(' ', '_').lower()}",
            name=data.get("name", "Unknown Archetype"),
            type=PersonalityType.ARCHETYPE,
            traits=traits,
            communication_style=comm_style,
            mannerisms=data.get("mannerisms", []),
            sources=[source]
        )
        
    except Exception as e:
        print(f"Failed to create profile from archetype data: {e}")
        return None


async def research_personality(description: str) -> ResearchResult:
    """Research a personality from multiple sources."""
    description = sanitize_text(description)
    profiles = []
    errors = []
    suggestions = []
    
    try:
        # Check archetype data first (synchronous)
        archetype_data, archetype_confidence = get_archetype_data(description)
        if archetype_data and archetype_confidence > 0.3:
            profile = create_profile_from_archetype(archetype_data, archetype_confidence)
            if profile:
                profiles.append(profile)
        
        # TODO: Add Wikipedia and character database research
        
        # Generate suggestions if no good results
        if not profiles:
            suggestions = ["Try being more specific about the personality type",
                         "Include more details in your description"]
        
        # Calculate overall confidence
        overall_confidence = max([0.0] + [p.sources[0].confidence for p in profiles if p.sources])
        
    except Exception as e:
        errors.append(f"Research failed: {str(e)}")
        overall_confidence = 0.0
    
    return ResearchResult(
        query=description,
        profiles=profiles,
        confidence=overall_confidence,
        suggestions=suggestions,
        errors=errors
    )
