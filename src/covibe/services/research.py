"""Personality research functionality using functional programming principles - Updated."""

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
from ..utils.error_handling import (
    ResearchError, NetworkError, InputValidationError, RateLimitError,
    error_handler, ErrorCategory, RetryConfig, with_retry, ErrorContext
)
from ..utils.monitoring import record_error, performance_monitor


# Research configuration
WIKIPEDIA_API_BASE = "https://en.wikipedia.org/api/rest_v1"
REQUEST_TIMEOUT = 10.0
MAX_CONCURRENT_REQUESTS = 3


def get_character_data(query: str) -> Tuple[Optional[Dict[str, Any]], float]:
    """
    Get personality data for specific characters with fuzzy matching.
    
    Args:
        query: Description that might contain character names
        
    Returns:
        Tuple of (character_data, confidence_score)
    """
    characters = {
        "tony stark": {
            "name": "Tony Stark",
            "description": "Genius inventor, confident, witty, and innovative",
            "traits": ["genius", "confident", "witty", "innovative", "sarcastic"],
            "communication_style": {
                "tone": "confident",
                "formality": "casual",
                "verbosity": "moderate"
            },
            "mannerisms": ["makes witty remarks", "uses technical jargon", "shows confidence"]
        },
        "iron man": {
            "name": "Tony Stark (Iron Man)",
            "description": "Genius inventor, confident, witty, and innovative",
            "traits": ["genius", "confident", "witty", "innovative", "sarcastic"],
            "communication_style": {
                "tone": "confident",
                "formality": "casual",
                "verbosity": "moderate"
            },
            "mannerisms": ["makes witty remarks", "uses technical jargon", "shows confidence"]
        },
        "sherlock holmes": {
            "name": "Sherlock Holmes",
            "description": "Brilliant detective, analytical, observant, and logical",
            "traits": ["analytical", "observant", "logical", "brilliant", "deductive"],
            "communication_style": {
                "tone": "precise",
                "formality": "formal",
                "verbosity": "moderate"
            },
            "mannerisms": ["makes logical deductions", "notices small details", "speaks precisely"]
        },
        "yoda": {
            "name": "Yoda",
            "description": "Wise Jedi master, patient, philosophical, and insightful",
            "traits": ["wise", "patient", "philosophical", "insightful", "calm"],
            "communication_style": {
                "tone": "wise",
                "formality": "formal",
                "verbosity": "concise"
            },
            "mannerisms": ["speaks in inverted syntax", "shares wisdom", "uses metaphors"]
        },
        "einstein": {
            "name": "Albert Einstein",
            "description": "Brilliant physicist, curious, thoughtful, and innovative",
            "traits": ["brilliant", "curious", "thoughtful", "innovative", "humble"],
            "communication_style": {
                "tone": "thoughtful",
                "formality": "mixed",
                "verbosity": "moderate"
            },
            "mannerisms": ["explains complex concepts simply", "asks profound questions"]
        },
        "captain america": {
            "name": "Captain America",
            "description": "Heroic leader, patriotic, moral, and inspiring",
            "traits": ["heroic", "patriotic", "moral", "inspiring", "determined"],
            "communication_style": {
                "tone": "inspiring",
                "formality": "formal",
                "verbosity": "moderate"
            },
            "mannerisms": ["speaks with conviction", "emphasizes values", "leads by example"]
        },
        "steve rogers": {
            "name": "Captain America (Steve Rogers)",
            "description": "Heroic leader, patriotic, moral, and inspiring",
            "traits": ["heroic", "patriotic", "moral", "inspiring", "determined"],
            "communication_style": {
                "tone": "inspiring",
                "formality": "formal",
                "verbosity": "moderate"
            },
            "mannerisms": ["speaks with conviction", "emphasizes values", "leads by example"]
        }
    }
    
    query_lower = query.lower()
    
    # Direct character name matching (highest confidence)
    for char_key, char_data in characters.items():
        if char_key in query_lower:
            return char_data, 0.95
    
    # Fuzzy matching for typos and similar names
    def simple_fuzzy_match(text1: str, text2: str) -> float:
        """Simple fuzzy matching based on character overlap and length similarity."""
        if not text1 or not text2:
            return 0.0
        
        # Calculate character overlap
        set1, set2 = set(text1.lower()), set(text2.lower())
        overlap = len(set1.intersection(set2))
        total_chars = len(set1.union(set2))
        char_similarity = overlap / total_chars if total_chars > 0 else 0.0
        
        # Calculate length similarity
        len_diff = abs(len(text1) - len(text2))
        max_len = max(len(text1), len(text2))
        len_similarity = 1.0 - (len_diff / max_len) if max_len > 0 else 0.0
        
        # Combined similarity score
        return (char_similarity * 0.7) + (len_similarity * 0.3)
    
    # Check for fuzzy matches
    best_match = None
    best_score = 0.0
    
    for char_key, char_data in characters.items():
        # Check fuzzy match against character key
        key_similarity = simple_fuzzy_match(query_lower, char_key)
        
        # Also check against character name
        char_name = char_data.get("name", "").lower()
        name_similarity = simple_fuzzy_match(query_lower, char_name)
        
        # Use the better of the two similarities
        similarity = max(key_similarity, name_similarity)
        
        # If similarity is good enough and better than previous matches
        if similarity > 0.6 and similarity > best_score:
            best_match = char_data
            best_score = similarity
    
    if best_match:
        # Return with confidence based on similarity (0.6-0.9 range)
        confidence = 0.6 + (best_score - 0.6) * 0.75  # Scale to 0.6-0.9
        return best_match, confidence
    
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
            
    # Check for related terms using word boundaries to avoid false matches
    import re
    archetype_keywords = {
        "teacher": "teacher",
        "coach": "mentor",
        "military": "drill sergeant",
        "soldier": "drill sergeant",
        "android": "robot",
        r"\bai\b": "robot",  # Use word boundary for "ai" to avoid matching "America"
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
        if keyword.startswith(r'\b') and keyword.endswith(r'\b'):
            # Use regex for word boundary patterns
            if re.search(keyword, query_lower) and archetype_key in archetypes:
                return archetypes[archetype_key], 0.7
        elif keyword in query_lower and archetype_key in archetypes:
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


@performance_monitor("wikipedia_research", "research")
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
        elif response.status_code == 404:
            raise ResearchError(
                f"No Wikipedia page found for '{query}'",
                source="wikipedia",
                suggestions=[
                    "Check the spelling of the name",
                    "Try a more common name or alias",
                    "Use the full name instead of nickname"
                ]
            )
        elif response.status_code == 429:
            raise RateLimitError(
                "Wikipedia API rate limit exceeded",
                retry_after=60,
                suggestions=["Wait a minute before trying again"]
            )
        else:
            raise NetworkError(
                f"Wikipedia API returned status {response.status_code}",
                url=search_url
            )
            
    except httpx.TimeoutException:
        raise NetworkError(
            f"Wikipedia request timed out after {REQUEST_TIMEOUT}s",
            url=search_url,
            suggestions=["Check your internet connection", "Try again later"]
        )
    except httpx.RequestError as e:
        raise NetworkError(
            f"Failed to connect to Wikipedia: {str(e)}",
            url=search_url,
            suggestions=["Check your internet connection", "Try again later"]
        )
    except (ResearchError, NetworkError, RateLimitError):
        # Re-raise our custom errors
        raise
    except Exception as e:
        raise ResearchError(
            f"Unexpected error during Wikipedia research: {str(e)}",
            source="wikipedia"
        )
        
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


def create_profile_from_character(data: Dict[str, Any], confidence: float) -> Optional[PersonalityProfile]:
    """Create a personality profile from character data."""
    try:
        traits = []
        for trait_name in data.get("traits", []):
            trait = PersonalityTrait(
                category="character",
                trait=trait_name,
                intensity=8,
                examples=[f"Known for being {trait_name}"]
            )
            traits.append(trait)
        
        style_data = data.get("communication_style", {})
        comm_style = CommunicationStyle(
            tone=style_data.get("tone", "neutral"),
            formality=FormalityLevel(style_data.get("formality", "mixed")),
            verbosity=VerbosityLevel(style_data.get("verbosity", "moderate")),
            technical_level=TechnicalLevel.EXPERT
        )
        
        source = ResearchSource(
            type="character_database",
            url=None,
            confidence=confidence,
            last_updated=datetime.now()
        )
        
        return PersonalityProfile(
            id=f"char_{data.get('name', 'unknown').replace(' ', '_').lower()}",
            name=data.get("name", "Unknown Character"),
            type=PersonalityType.FICTIONAL,
            traits=traits,
            communication_style=comm_style,
            mannerisms=data.get("mannerisms", []),
            sources=[source]
        )
        
    except Exception as e:
        print(f"Failed to create profile from character data: {e}")
        return None


def create_profile_from_wikipedia(data: Dict[str, Any], confidence: float) -> Optional[PersonalityProfile]:
    """Create a personality profile from Wikipedia data."""
    try:
        # Extract traits from Wikipedia description and extract
        text_content = f"{data.get('description', '')} {data.get('extract', '')}"
        traits = extract_traits_from_text(text_content)
        
        # If no traits found, create some basic ones
        if not traits:
            traits = [
                PersonalityTrait(
                    category="wikipedia",
                    trait="notable",
                    intensity=6,
                    examples=["Notable figure with Wikipedia page"]
                )
            ]
        
        # Create basic communication style
        comm_style = CommunicationStyle(
            tone="informative",
            formality=FormalityLevel.MIXED,
            verbosity=VerbosityLevel.MODERATE,
            technical_level=TechnicalLevel.INTERMEDIATE
        )
        
        source = ResearchSource(
            type="wikipedia",
            url=data.get("url"),
            confidence=confidence,
            last_updated=datetime.now()
        )
        
        return PersonalityProfile(
            id=f"wiki_{data.get('title', 'unknown').replace(' ', '_').lower()}",
            name=data.get("title", "Unknown Person"),
            type=PersonalityType.CELEBRITY,
            traits=traits,
            communication_style=comm_style,
            mannerisms=[f"Known for: {data.get('description', 'various achievements')}"],
            sources=[source]
        )
        
    except Exception as e:
        print(f"Failed to create profile from Wikipedia data: {e}")
        return None


def generate_research_suggestions(description: str) -> List[str]:
    """Generate helpful suggestions for research queries."""
    suggestions = []
    
    # Basic suggestions
    base_suggestions = [
        "Try using specific character names like 'Tony Stark', 'Sherlock Holmes', or 'Einstein'",
        "Try archetype descriptions like 'genius', 'mentor', 'drill sergeant', or 'robot'",
        "Include more details in your description"
    ]
    
    # Add specific suggestions based on the query
    description_lower = description.lower()
    
    if any(word in description_lower for word in ["smart", "intelligent", "clever"]):
        suggestions.append("Try 'genius' or 'Einstein' for intelligent personalities")
    
    if any(word in description_lower for word in ["funny", "humor", "joke"]):
        suggestions.append("Try 'Tony Stark' for witty, humorous personalities")
    
    if any(word in description_lower for word in ["wise", "old", "sage"]):
        suggestions.append("Try 'Yoda' or 'mentor' for wise personalities")
    
    if any(word in description_lower for word in ["detective", "logical", "analytical"]):
        suggestions.append("Try 'Sherlock Holmes' for analytical personalities")
    
    if any(word in description_lower for word in ["military", "strict", "discipline"]):
        suggestions.append("Try 'drill sergeant' for authoritative personalities")
    
    if any(word in description_lower for word in ["robot", "machine", "ai", "artificial"]):
        suggestions.append("Try 'robot' for logical, systematic personalities")
    
    # Return suggestions with base suggestions as fallback
    return suggestions if suggestions else base_suggestions


@error_handler(
    category=ErrorCategory.RESEARCH,
    operation="personality_research",
    component="research",
    retry_config=RetryConfig(max_attempts=2, base_delay=1.0)
)
@performance_monitor("personality_research", "research")
async def research_personality(description: str) -> ResearchResult:
    """Research a personality from multiple sources with comprehensive error handling."""
    
    # Input validation
    if not description or not description.strip():
        raise InputValidationError(
            "Personality description cannot be empty",
            field="description",
            suggestions=["Provide a personality name or description"]
        )
    
    description = sanitize_text(description)
    profiles = []
    errors = []
    suggestions = []
    
    context = ErrorContext(
        operation="personality_research",
        component="research",
        additional_data={"query": description}
    )
    
    try:
        # Primary research path: Check character data first (highest priority)
        character_data, character_confidence = get_character_data(description)
        if character_data and character_confidence > 0.8:
            profile = create_profile_from_character(character_data, character_confidence)
            if profile:
                profiles.append(profile)
        
        # Fallback 1: Check archetype data if no character found
        if not profiles:
            archetype_data, archetype_confidence = get_archetype_data(description)
            if archetype_data and archetype_confidence > 0.3:
                profile = create_profile_from_archetype(archetype_data, archetype_confidence)
                if profile:
                    profiles.append(profile)
        
        # Fallback 2: Try Wikipedia research (with retry logic)
        if not profiles:
            try:
                async with httpx.AsyncClient() as client:
                    wikipedia_data, wikipedia_confidence = await with_retry(
                        research_wikipedia,
                        description,
                        client,
                        retry_config=RetryConfig(max_attempts=3, base_delay=2.0),
                        retryable_exceptions=(NetworkError, RateLimitError),
                        context=context
                    )
                    
                    if wikipedia_data and wikipedia_confidence > 0.5:
                        # Create profile from Wikipedia data
                        profile = create_profile_from_wikipedia(wikipedia_data, wikipedia_confidence)
                        if profile:
                            profiles.append(profile)
                            
            except (NetworkError, RateLimitError, ResearchError) as e:
                # Log the error but don't fail the entire research
                record_error(e, "research")
                errors.append(f"Wikipedia research failed: {e.message}")
        
        # Generate helpful suggestions if no good results
        if not profiles:
            suggestions = generate_research_suggestions(description)
            
            # If we still have no results, this is a research failure
            if not suggestions:
                raise ResearchError(
                    f"No personality information found for '{description}'",
                    suggestions=[
                        "Try using specific character names like 'Tony Stark', 'Sherlock Holmes', or 'Einstein'",
                        "Try archetype descriptions like 'genius', 'mentor', 'drill sergeant', or 'robot'",
                        "Include more details in your description"
                    ]
                )
        
        # Calculate overall confidence
        overall_confidence = max([0.0] + [p.sources[0].confidence for p in profiles if p.sources])
        
        return ResearchResult(
            query=description,
            profiles=profiles,
            confidence=overall_confidence,
            suggestions=suggestions,
            errors=errors
        )
        
    except (InputValidationError, ResearchError):
        # Re-raise our custom errors
        raise
    except Exception as e:
        # Convert unexpected errors to ResearchError
        raise ResearchError(
            f"Unexpected error during personality research: {str(e)}",
            context=context
        )
