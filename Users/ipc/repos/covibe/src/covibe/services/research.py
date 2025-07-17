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
MARVEL_API_BASE = "https://gateway.marvel.com/v1/public"
REQUEST_TIMEOUT = 10.0
MAX_CONCURRENT_REQUESTS = 3


async def research_wikipedia(
    query: str, 
    client: httpx.AsyncClient
) -> Tuple[Optional[Dict[str, Any]], float]:
    """
    Research personality information from Wikipedia.
    
    Args:
        query: Search query for the personality
        client: HTTP client for making requests
        
    Returns:
        Tuple of (research_data, confidence_score)
    """
    try:
        # Search for the page
        search_url = f"{WIKIPEDIA_API_BASE}/page/summary/{query.replace(' ', '_')}"
        
        response = await client.get(search_url, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract relevant information
            research_data = {
                "title": data.get("title", ""),
                "description": data.get("description", ""),
                "extract": data.get("extract", ""),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                "source_type": "wikipedia"
            }
            
            # Calculate confidence based on data quality
            confidence = calculate_wikipedia_confidence(research_data)
            
            return research_data, confidence
            
    except (httpx.RequestError, httpx.TimeoutException, json.JSONDecodeError) as e:
        print(f"Wikipedia research failed for {query}: {e}")
        
    return None, 0.0


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


async def research_character_database(
    query: str,
    client: httpx.AsyncClient
) -> Tuple[Optional[Dict[str, Any]], float]:
    """
    Research fictional characters from character databases.
    
    Note: This is a placeholder implementation. In production, you would
    integrate with actual character APIs like Marvel, DC, or other databases.
    """
    try:
        # For now, return mock data for common fictional characters
        fictional_characters = {
            "sherlock holmes": {
                "name": "Sherlock Holmes",
                "description": "Brilliant detective with exceptional deductive reasoning",
                "traits": ["analytical", "observant", "logical", "eccentric"],
                "source": "Arthur Conan Doyle stories",
                "personality_notes": "Highly intelligent, sometimes arrogant, socially awkward but brilliant"
            },
            "tony stark": {
                "name": "Tony Stark",
                "description": "Genius inventor and Iron Man",
                "traits": ["intelligent", "sarcastic", "confident", "innovative"],
                "source": "Marvel Comics",
                "personality_notes": "Brilliant engineer, witty, sometimes arrogant, heroic"
            },
            "yoda": {
                "name": "Yoda",
                "description": "Wise Jedi Master",
                "traits": ["wise", "patient", "cryptic", "powerful"],
                "source": "Star Wars",
                "personality_notes": "Ancient wisdom, speaks in unique syntax, calm and patient"
            }
        }
        
        query_lower = query.lower()
        for key, character_data in fictional_characters.items():
            if key in query_lower or any(word in query_lower for word in key.split()):
                return character_data, 0.8
                
    except Exception as e:
        print(f"Character database research failed for {query}: {e}")
        
    return None, 0.0


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
            "mannerisms": ["uses simple, direct language", "values actions over words", "practical approach"]
        },
        "robot": {
            "name": "Robot/AI",
            "description": "Logical, precise, analytical personality",
            "traits": ["logical", "precise", "analytical", "systematic"],
            "communication_style": {
                "tone": "neutral",
                "formality": "formal",
                "verbosity": "precise"
            },
            "mannerisms": ["uses technical language", "focuses on facts", "systematic thinking"]
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
            "mannerisms": ["uses imperative language", "focuses on discipline", "direct commands"]
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
            "mannerisms": ["asks guiding questions", "shares wisdom", "patient explanations"]
        },
        "pirate": {
            "name": "Pirate",
            "description": "Adventurous, bold, colorful personality",
            "traits": ["adventurous", "bold", "colorful", "free-spirited"],
            "communication_style": {
                "tone": "colorful",
                "formality": "casual",
                "verbosity": "moderate"
            },
            "mannerisms": ["uses nautical terms", "tells stories", "bold expressions"]
        }
    }
    
    query_lower = query.lower()
    
    for archetype_key, archetype_data in archetypes.items():
        if archetype_key in query_lower:
            return archetype_data, 0.9
            
    # Check for related terms
    archetype_keywords = {
        "teacher": "mentor",
        "coach": "mentor",
        "guide": "mentor",
        "military": "drill sergeant",
        "soldier": "drill sergeant",
        "commander": "drill sergeant",
        "western": "cowboy",
        "frontier": "cowboy",
        "android": "robot",
        "ai": "robot",
        "artificial intelligence": "robot",
        "buccaneer": "pirate",
        "sailor": "pirate"
    }
    
    for keyword, archetype_key in archetype_keywords.items():
        if keyword in query_lower and archetype_key in archetypes:
            return archetypes[archetype_key], 0.7
            
    return None, 0.0


async def research_personality(
    description: str,
    max_concurrent: int = MAX_CONCURRENT_REQUESTS
) -> ResearchResult:
    """
    Research a personality from multiple sources using async composition.
    
    Args:
        description: Personality description to research
        max_concurrent: Maximum concurrent API requests
        
    Returns:
        ResearchResult with profiles, confidence, and suggestions
    """
    description = sanitize_text(description)
    profiles = []
    errors = []
    suggestions = []
    
    # Detect personality type
    detected_type = detect_personality_type(description)
    
    try:
        # Create semaphore for concurrent request limiting
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async with httpx.AsyncClient() as client:
            # Research tasks
            tasks = []
            
            # Wikipedia research
            async def wikipedia_research():
                async with semaphore:
                    return await research_wikipedia(description, client)
            
            # Character database research
            async def character_research():
                async with semaphore:
                    return await research_character_database(description, client)
            
            tasks.extend([wikipedia_research(), character_research()])
            
            # Execute research tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process Wikipedia results
            if len(results) > 0 and not isinstance(results[0], Exception):
                wiki_data, wiki_confidence = results[0]
                if wiki_data and wiki_confidence > 0.3:
                    profile = create_profile_from_wikipedia(wiki_data, wiki_confidence)
                    if profile:
                        profiles.append(profile)
            
            # Process character database results
            if len(results) > 1 and not isinstance(results[1], Exception):
                char_data, char_confidence = results[1]
                if char_data and char_confidence > 0.3:
                    profile = create_profile_from_character_data(char_data, char_confidence)
                    if profile:
                        profiles.append(profile)
        
        # Check archetype data (synchronous)
        archetype_data, archetype_confidence = get_archetype_data(description)
        if archetype_data and archetype_confidence > 0.3:
            profile = create_profile_from_archetype(archetype_data, archetype_confidence)
            if profile:
                profiles.append(profile)
        
        # Generate suggestions if no good results
        if not profiles:
            suggestions = generate_research_suggestions(description, detected_type)
        
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


def create_profile_from_wikipedia(
    data: Dict[str, Any], 
    confidence: float
) -> Optional[PersonalityProfile]:
    """Create a personality profile from Wikipedia data."""
    try:
        # Extract traits from description and extract
        text_content = f"{data.get('description', '')} {data.get('extract', '')}"
        traits = extract_traits_from_text(text_content)
        
        # Create communication style based on available information
        comm_style = CommunicationStyle(
            tone="informative",
            formality=FormalityLevel.FORMAL,
            verbosity=VerbosityLevel.MODERATE,
            technical_level=TechnicalLevel.INTERMEDIATE
        )
        
        # Create research source
        source = ResearchSource(
            type="wikipedia",
            url=data.get("url", ""),
            confidence=confidence,
            last_updated=datetime.now()
        )
        
        return PersonalityProfile(
            id=f"wiki_{data.get('title', 'unknown').replace(' ', '_').lower()}",
            name=data.get("title", "Unknown"),
            type=PersonalityType.CELEBRITY,  # Assume celebrity for Wikipedia entries
            traits=traits,
            communication_style=comm_style,
            mannerisms=extract_mannerisms_from_text(text_content),
            sources=[source]
        )
        
    except Exception as e:
        print(f"Failed to create profile from Wikipedia data: {e}")
        return None


def create_profile_from_character_data(
    data: Dict[str, Any], 
    confidence: float
) -> Optional[PersonalityProfile]:
    """Create a personality profile from character database data."""
    try:
        # Convert traits to PersonalityTrait objects
        traits = []
        for trait_name in data.get("traits", []):
            trait = PersonalityTrait(
                category="personality",
                trait=trait_name,
                intensity=7,  # Default intensity
                examples=[f"Shows {trait_name} behavior"]
            )
            traits.append(trait)
        
        # Create communication style
        comm_style = CommunicationStyle(
            tone="characteristic",
            formality=FormalityLevel.MIXED,
            verbosity=VerbosityLevel.MODERATE,
            technical_level=TechnicalLevel.INTERMEDIATE
        )
        
        # Create research source
        source = ResearchSource(
            type="character_database",
            url="",
            confidence=confidence,
            last_updated=datetime.now()
        )
        
        return PersonalityProfile(
            id=f"char_{data.get('name', 'unknown').replace(' ', '_').lower()}",
            name=data.get("name", "Unknown Character"),
            type=PersonalityType.FICTIONAL,
            traits=traits,
            communication_style=comm_style,
            mannerisms=[data.get("personality_notes", "")],
            sources=[source]
        )
        
    except Exception as e:
        print(f"Failed to create profile from character data: {e}")
        return None


def create_profile_from_archetype(
    data: Dict[str, Any], 
    confidence: float
) -> Optional[PersonalityProfile]:
    """Create a personality profile from archetype data."""
    try:
        # Convert traits to PersonalityTrait objects
        traits = []
        for trait_name in data.get("traits", []):
            trait = PersonalityTrait(
                category="archetype",
                trait=trait_name,
                intensity=8,  # Archetypes tend to have strong traits
                examples=[f"Embodies {trait_name} characteristics"]
            )
            traits.append(trait)
        
        # Create communication style from archetype data
        style_data = data.get("communication_style", {})
        comm_style = CommunicationStyle(
            tone=style_data.get("tone", "neutral"),
            formality=FormalityLevel(style_data.get("formality", "mixed")),
            verbosity=VerbosityLevel(style_data.get("verbosity", "moderate")),
            technical_level=TechnicalLevel.INTERMEDIATE
        )
        
        # Create research source
        source = ResearchSource(
            type="archetype_database",
            url="",
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


def extract_traits_from_text(text: str) -> List[PersonalityTrait]:
    """Extract personality traits from descriptive text."""
    # Simple keyword-based trait extraction
    trait_keywords = {
        "intelligent": ["smart", "brilliant", "genius", "clever", "intellectual"],
        "confident": ["confident", "self-assured", "bold", "assertive"],
        "analytical": ["analytical", "logical", "systematic", "methodical"],
        "creative": ["creative", "innovative", "imaginative", "artistic"],
        "leadership": ["leader", "leadership", "commanding", "authoritative"],
        "humorous": ["funny", "witty", "humorous", "comedic", "amusing"],
        "determined": ["determined", "persistent", "tenacious", "driven"],
        "empathetic": ["empathetic", "compassionate", "understanding", "caring"]
    }
    
    text_lower = text.lower()
    traits = []
    
    for trait_name, keywords in trait_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                trait = PersonalityTrait(
                    category="extracted",
                    trait=trait_name,
                    intensity=6,  # Medium intensity for extracted traits
                    examples=[f"Described as {keyword}"]
                )
                traits.append(trait)
                break  # Only add each trait once
    
    return traits


def extract_mannerisms_from_text(text: str) -> List[str]:
    """Extract behavioral mannerisms from descriptive text."""
    mannerisms = []
    
    # Look for speech patterns and behavioral descriptions
    if "speaks" in text.lower():
        mannerisms.append("Has distinctive speaking patterns")
    if "known for" in text.lower():
        mannerisms.append("Has characteristic behaviors")
    if len(text) > 200:
        mannerisms.append("Complex personality with multiple facets")
        
    return mannerisms


def generate_research_suggestions(
    description: str, 
    detected_type: Optional[str]
) -> List[str]:
    """Generate suggestions when research yields poor results."""
    suggestions = []
    
    if detected_type is None:
        suggestions.append("Try being more specific about the personality type (celebrity, fictional character, or archetype)")
        suggestions.append("Include the full name if referring to a specific person or character")
    
    if len(description.split()) < 3:
        suggestions.append("Provide more details in your description")
        suggestions.append("Include context like 'from [movie/book/show]' for fictional characters")
    
    suggestions.append("Try alternative names or spellings")
    suggestions.append("Consider using a more well-known personality as a starting point")
    
    return suggestions