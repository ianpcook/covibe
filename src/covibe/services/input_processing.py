"""Advanced personality input processing with fuzzy matching and combination handling."""

import re
import asyncio
from typing import List, Dict, Optional, Tuple, Any, Set
from dataclasses import dataclass
from enum import Enum

from ..models.core import PersonalityProfile, PersonalityType, ResearchResult
from .research import research_personality, get_character_data, get_archetype_data
from ..utils.validation import sanitize_text


class InputType(Enum):
    """Types of personality input detected."""
    SPECIFIC_NAME = "specific_name"
    DESCRIPTIVE_PHRASE = "descriptive_phrase"
    COMBINATION = "combination"
    AMBIGUOUS = "ambiguous"
    UNCLEAR = "unclear"


class CombinationType(Enum):
    """Types of personality combinations."""
    BUT_MORE = "but_more"  # "Tony Stark but more patient"
    BUT_LESS = "but_less"  # "Tony Stark but less arrogant"
    MIXED_WITH = "mixed_with"  # "Tony Stark mixed with Einstein"
    LIKE_BUT = "like_but"  # "like Tony Stark but calmer"


@dataclass
class InputAnalysis:
    """Analysis of personality input."""
    input_type: InputType
    confidence: float
    primary_personality: Optional[str] = None
    modifiers: List[str] = None
    combination_type: Optional[CombinationType] = None
    secondary_personality: Optional[str] = None
    suggestions: List[str] = None
    clarification_questions: List[str] = None


@dataclass
class PersonalitySuggestion:
    """Suggestion for personality resolution."""
    name: str
    confidence: float
    reason: str
    personality_type: PersonalityType


@dataclass
class ClarificationQuestion:
    """Question to clarify ambiguous input."""
    question: str
    options: List[str]
    context: str


class FuzzyMatcher:
    """Fuzzy matching utilities for personality names."""
    
    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return FuzzyMatcher.levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    @staticmethod
    def similarity_score(s1: str, s2: str) -> float:
        """Calculate similarity score between two strings (0.0 to 1.0)."""
        if not s1 or not s2:
            return 0.0
        
        distance = FuzzyMatcher.levenshtein_distance(s1.lower(), s2.lower())
        max_len = max(len(s1), len(s2))
        return 1.0 - (distance / max_len)
    
    @staticmethod
    def find_best_matches(query: str, candidates: List[str], threshold: float = 0.6) -> List[Tuple[str, float]]:
        """Find best matching candidates above threshold."""
        matches = []
        for candidate in candidates:
            score = FuzzyMatcher.similarity_score(query, candidate)
            if score >= threshold:
                matches.append((candidate, score))
        
        # Sort by score descending
        return sorted(matches, key=lambda x: x[1], reverse=True)


class PersonalityKnowledgeBase:
    """Knowledge base of known personalities for fuzzy matching."""
    
    def __init__(self):
        self.characters = {
            "tony stark": {"aliases": ["iron man", "stark"], "type": PersonalityType.FICTIONAL},
            "sherlock holmes": {"aliases": ["holmes", "detective"], "type": PersonalityType.FICTIONAL},
            "yoda": {"aliases": ["master yoda", "jedi master"], "type": PersonalityType.FICTIONAL},
            "einstein": {"aliases": ["albert einstein", "professor einstein"], "type": PersonalityType.CELEBRITY},
            "captain america": {"aliases": ["steve rogers", "cap"], "type": PersonalityType.FICTIONAL},
            "batman": {"aliases": ["bruce wayne", "dark knight"], "type": PersonalityType.FICTIONAL},
            "spiderman": {"aliases": ["spider-man", "peter parker"], "type": PersonalityType.FICTIONAL},
            "gandalf": {"aliases": ["gandalf the grey", "gandalf the white"], "type": PersonalityType.FICTIONAL},
            "dumbledore": {"aliases": ["albus dumbledore", "professor dumbledore"], "type": PersonalityType.FICTIONAL},
            "hermione": {"aliases": ["hermione granger"], "type": PersonalityType.FICTIONAL},
            "spock": {"aliases": ["mr spock", "vulcan"], "type": PersonalityType.FICTIONAL},
            "data": {"aliases": ["lieutenant commander data", "android"], "type": PersonalityType.FICTIONAL},
        }
        
        self.archetypes = {
            "mentor": {"aliases": ["teacher", "guide", "coach"], "type": PersonalityType.ARCHETYPE},
            "genius": {"aliases": ["brilliant", "smart", "intelligent"], "type": PersonalityType.ARCHETYPE},
            "robot": {"aliases": ["android", "ai", "artificial intelligence"], "type": PersonalityType.ARCHETYPE},
            "drill sergeant": {"aliases": ["military", "commander", "strict"], "type": PersonalityType.ARCHETYPE},
            "cowboy": {"aliases": ["western", "gunslinger", "ranger"], "type": PersonalityType.ARCHETYPE},
            "monk": {"aliases": ["zen master", "buddhist", "spiritual"], "type": PersonalityType.ARCHETYPE},
            "pirate": {"aliases": ["buccaneer", "seafarer"], "type": PersonalityType.ARCHETYPE},
            "knight": {"aliases": ["paladin", "crusader", "chivalrous"], "type": PersonalityType.ARCHETYPE},
        }
    
    def get_all_names(self) -> List[str]:
        """Get all known personality names and aliases."""
        names = []
        
        # Add character names and aliases
        for name, data in self.characters.items():
            names.append(name)
            names.extend(data["aliases"])
        
        # Add archetype names and aliases
        for name, data in self.archetypes.items():
            names.append(name)
            names.extend(data["aliases"])
        
        return names
    
    def find_personality_type(self, name: str) -> Optional[PersonalityType]:
        """Find the personality type for a given name."""
        name_lower = name.lower()
        
        # Check characters
        for char_name, data in self.characters.items():
            if name_lower == char_name or name_lower in [alias.lower() for alias in data["aliases"]]:
                return data["type"]
        
        # Check archetypes
        for arch_name, data in self.archetypes.items():
            if name_lower == arch_name or name_lower in [alias.lower() for alias in data["aliases"]]:
                return data["type"]
        
        return None


class CombinationParser:
    """Parser for combination personality requests."""
    
    # Patterns for different combination types
    COMBINATION_PATTERNS = {
        CombinationType.BUT_MORE: [
            r"(.+?)\s+but\s+more\s+(.+)",
            r"(.+?)\s+but\s+with\s+more\s+(.+)",
            r"(.+?)\s+but\s+extra\s+(.+)",
        ],
        CombinationType.BUT_LESS: [
            r"(.+?)\s+but\s+less\s+(.+)",
            r"(.+?)\s+but\s+without\s+(.+)",
            r"(.+?)\s+but\s+minus\s+(.+)",
        ],
        CombinationType.MIXED_WITH: [
            r"(.+?)\s+mixed\s+with\s+(.+)",
            r"(.+?)\s+combined\s+with\s+(.+)",
            r"(.+?)\s+and\s+(.+?)\s+combined",
        ],
        CombinationType.LIKE_BUT: [
            r"like\s+(.+?)\s+but\s+(.+)",
            r"similar\s+to\s+(.+?)\s+but\s+(.+)",
            r"(.+?)\s+style\s+but\s+(.+)",
        ],
    }
    
    @classmethod
    def parse_combination(cls, text: str) -> Optional[Tuple[CombinationType, str, str]]:
        """Parse combination personality request."""
        text_lower = text.lower().strip()
        
        for combo_type, patterns in cls.COMBINATION_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower)
                if match:
                    primary = match.group(1).strip()
                    modifier = match.group(2).strip()
                    return combo_type, primary, modifier
        
        return None


class AdvancedInputProcessor:
    """Advanced processor for personality input with fuzzy matching and combinations."""
    
    def __init__(self):
        self.knowledge_base = PersonalityKnowledgeBase()
        self.fuzzy_matcher = FuzzyMatcher()
        self.combination_parser = CombinationParser()
    
    async def analyze_input(self, description: str) -> InputAnalysis:
        """Analyze personality input and determine type and characteristics."""
        original_description = description
        description = sanitize_text(description)
        
        # If sanitization removed too much, try with just basic cleanup
        if not description.strip():
            description = original_description.strip()
        
        # Remove excessive special characters but keep basic punctuation
        import string
        cleaned_description = ''.join(c for c in description if c.isalnum() or c.isspace() or c in "'-.")
        if cleaned_description.strip():
            description = cleaned_description.strip()
        
        # Check for combination patterns first
        combination_result = self.combination_parser.parse_combination(description)
        if combination_result:
            combo_type, primary, modifier = combination_result
            return InputAnalysis(
                input_type=InputType.COMBINATION,
                confidence=0.9,
                primary_personality=primary,
                modifiers=[modifier],
                combination_type=combo_type,
                secondary_personality=modifier if combo_type == CombinationType.MIXED_WITH else None
            )
        
        # Check for specific names with fuzzy matching
        all_names = self.knowledge_base.get_all_names()
        matches = self.fuzzy_matcher.find_best_matches(description, all_names, threshold=0.6)
        
        if matches and matches[0][1] >= 0.95:
            # Very high confidence - exact or near-exact match
            return InputAnalysis(
                input_type=InputType.SPECIFIC_NAME,
                confidence=matches[0][1],
                primary_personality=matches[0][0]
            )
        elif matches and matches[0][1] > 0.8:
            # High confidence but not perfect - could be typo
            return InputAnalysis(
                input_type=InputType.AMBIGUOUS,
                confidence=matches[0][1],
                primary_personality=description,
                suggestions=[match[0] for match in matches[:3]],
                clarification_questions=[
                    f"Did you mean '{matches[0][0]}'?",
                    f"Or perhaps one of these: {', '.join([m[0] for m in matches[1:3]])}" if len(matches) > 1 else None
                ]
            )
        elif matches and matches[0][1] > 0.6:
            # Medium confidence - ambiguous
            suggestions = [PersonalitySuggestion(
                name=match[0],
                confidence=match[1],
                reason=f"Similar to '{description}'",
                personality_type=self.knowledge_base.find_personality_type(match[0]) or PersonalityType.CUSTOM
            ) for match in matches[:3]]
            
            return InputAnalysis(
                input_type=InputType.AMBIGUOUS,
                confidence=matches[0][1],
                primary_personality=description,
                suggestions=[s.name for s in suggestions],
                clarification_questions=[
                    f"Did you mean '{matches[0][0]}'?",
                    f"Or perhaps one of these: {', '.join([m[0] for m in matches[1:3]])}" if len(matches) > 1 else None
                ]
            )
        
        # Check if it's a descriptive phrase
        if self._is_descriptive_phrase(description):
            return InputAnalysis(
                input_type=InputType.DESCRIPTIVE_PHRASE,
                confidence=0.7,
                primary_personality=description
            )
        
        # If nothing else matches, it's unclear
        return InputAnalysis(
            input_type=InputType.UNCLEAR,
            confidence=0.3,
            primary_personality=description,
            clarification_questions=self._generate_clarification_questions(description)
        )
    
    def _is_descriptive_phrase(self, text: str) -> bool:
        """Check if text appears to be a descriptive phrase."""
        descriptive_keywords = [
            "friendly", "patient", "smart", "funny", "serious", "calm", "energetic",
            "helpful", "strict", "gentle", "confident", "shy", "outgoing", "quiet",
            "creative", "logical", "emotional", "rational", "optimistic", "pessimistic",
            "mentor", "teacher", "guide", "leader", "follower", "genius", "expert"
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in descriptive_keywords)
    
    def _generate_clarification_questions(self, description: str) -> List[str]:
        """Generate clarification questions for unclear input."""
        questions = [
            "Could you be more specific about the personality you want?",
            "Are you looking for a specific character (like Tony Stark, Sherlock Holmes)?",
            "Or would you prefer a personality type (like genius, mentor, robot)?",
        ]
        
        # Add context-specific questions based on keywords
        description_lower = description.lower()
        
        if any(word in description_lower for word in ["smart", "intelligent", "clever"]):
            questions.append("For intelligence, you might try 'genius', 'Einstein', or 'Sherlock Holmes'")
        
        if any(word in description_lower for word in ["funny", "humor", "joke"]):
            questions.append("For humor, you might try 'Tony Stark' or 'witty genius'")
        
        if any(word in description_lower for word in ["wise", "old", "sage"]):
            questions.append("For wisdom, you might try 'Yoda', 'mentor', or 'wise monk'")
        
        return questions
    
    async def generate_suggestions(self, description: str, max_suggestions: int = 5) -> List[PersonalitySuggestion]:
        """Generate personality suggestions for ambiguous input."""
        all_names = self.knowledge_base.get_all_names()
        matches = self.fuzzy_matcher.find_best_matches(description, all_names, threshold=0.4)
        
        suggestions = []
        for name, confidence in matches[:max_suggestions]:
            # Ensure minimum confidence threshold
            if confidence < 0.4:
                continue
                
            personality_type = self.knowledge_base.find_personality_type(name) or PersonalityType.CUSTOM
            reason = f"Similar to '{description}' (confidence: {confidence:.2f})"
            
            suggestions.append(PersonalitySuggestion(
                name=name,
                confidence=confidence,
                reason=reason,
                personality_type=personality_type
            ))
        
        return suggestions
    
    async def process_combination(self, analysis: InputAnalysis) -> Optional[PersonalityProfile]:
        """Process combination personality requests."""
        if analysis.input_type != InputType.COMBINATION:
            return None
        
        # Research the primary personality
        try:
            primary_result = await research_personality(analysis.primary_personality)
            if not primary_result.profiles:
                return None
            
            primary_profile = primary_result.profiles[0]
            
            # Apply modifications based on combination type
            modified_profile = await self._apply_personality_modifications(
                primary_profile,
                analysis.combination_type,
                analysis.modifiers[0] if analysis.modifiers else ""
            )
            
            return modified_profile
            
        except Exception as e:
            print(f"Error processing combination: {e}")
            return None
    
    async def _apply_personality_modifications(
        self,
        base_profile: PersonalityProfile,
        combo_type: CombinationType,
        modifier: str
    ) -> PersonalityProfile:
        """Apply modifications to a base personality profile."""
        # Create a copy of the base profile
        modified_profile = PersonalityProfile(
            id=f"{base_profile.id}_modified",
            name=f"{base_profile.name} (modified)",
            type=base_profile.type,
            traits=base_profile.traits.copy(),
            communication_style=base_profile.communication_style,
            mannerisms=base_profile.mannerisms.copy(),
            sources=base_profile.sources.copy()
        )
        
        if combo_type == CombinationType.BUT_MORE:
            # Add or enhance traits based on modifier
            await self._enhance_traits(modified_profile, modifier, increase=True)
        elif combo_type == CombinationType.BUT_LESS:
            # Reduce or remove traits based on modifier
            await self._enhance_traits(modified_profile, modifier, increase=False)
        elif combo_type == CombinationType.MIXED_WITH:
            # Blend with another personality
            await self._blend_personalities(modified_profile, modifier)
        elif combo_type == CombinationType.LIKE_BUT:
            # Similar to BUT_MORE but with different emphasis
            await self._enhance_traits(modified_profile, modifier, increase=True)
        
        return modified_profile
    
    async def _enhance_traits(self, profile: PersonalityProfile, modifier: str, increase: bool):
        """Enhance or reduce specific traits in a personality profile."""
        # Map common modifiers to trait categories
        trait_mappings = {
            "patient": "patience",
            "calm": "calmness",
            "aggressive": "aggressiveness",
            "confident": "confidence",
            "humble": "humility",
            "arrogant": "arrogance",
            "friendly": "friendliness",
            "serious": "seriousness",
            "funny": "humor",
            "strict": "strictness",
            "gentle": "gentleness"
        }
        
        modifier_lower = modifier.lower()
        
        # Find matching trait or create new one
        trait_name = trait_mappings.get(modifier_lower, modifier_lower)
        
        # Look for existing trait to modify
        existing_trait = None
        for trait in profile.traits:
            if trait.trait.lower() == trait_name or trait_name in trait.trait.lower():
                existing_trait = trait
                break
        
        if existing_trait:
            # Modify existing trait intensity
            if increase:
                existing_trait.intensity = min(10, existing_trait.intensity + 2)
            else:
                existing_trait.intensity = max(1, existing_trait.intensity - 2)
        else:
            # Add new trait
            from ..models.core import PersonalityTrait
            new_trait = PersonalityTrait(
                category="modified",
                trait=trait_name,
                intensity=8 if increase else 3,
                examples=[f"Enhanced {trait_name} characteristic"]
            )
            profile.traits.append(new_trait)
        
        # Update mannerisms
        if increase:
            profile.mannerisms.append(f"Shows enhanced {trait_name}")
        else:
            profile.mannerisms.append(f"Shows reduced {trait_name}")
    
    async def _blend_personalities(self, base_profile: PersonalityProfile, secondary_name: str):
        """Blend base personality with traits from secondary personality."""
        try:
            secondary_result = await research_personality(secondary_name)
            if secondary_result.profiles:
                secondary_profile = secondary_result.profiles[0]
                
                # Add some traits from secondary personality
                for trait in secondary_profile.traits[:2]:  # Take first 2 traits
                    # Reduce intensity when blending
                    blended_trait = PersonalityTrait(
                        category="blended",
                        trait=trait.trait,
                        intensity=max(1, trait.intensity - 2),
                        examples=[f"Blended from {secondary_profile.name}"]
                    )
                    base_profile.traits.append(blended_trait)
                
                # Add some mannerisms
                base_profile.mannerisms.extend(secondary_profile.mannerisms[:2])
                
                # Update name to reflect blend
                base_profile.name = f"{base_profile.name} + {secondary_profile.name}"
                
        except Exception as e:
            print(f"Error blending personalities: {e}")
    
    async def generate_clarification_questions(self, analysis: InputAnalysis) -> List[ClarificationQuestion]:
        """Generate structured clarification questions."""
        questions = []
        
        if analysis.input_type == InputType.AMBIGUOUS and analysis.suggestions:
            questions.append(ClarificationQuestion(
                question="Which personality did you mean?",
                options=analysis.suggestions[:4],
                context="Multiple similar personalities found"
            ))
        
        if analysis.input_type == InputType.UNCLEAR:
            questions.append(ClarificationQuestion(
                question="What type of personality are you looking for?",
                options=["Specific character (like Tony Stark)", "Personality type (like genius)", "Descriptive traits (like friendly mentor)"],
                context="Need more specific information"
            ))
        
        return questions


# Global instance
_input_processor = AdvancedInputProcessor()


async def analyze_personality_input(description: str) -> InputAnalysis:
    """Analyze personality input and return analysis."""
    return await _input_processor.analyze_input(description)


async def generate_personality_suggestions(description: str, max_suggestions: int = 5) -> List[PersonalitySuggestion]:
    """Generate personality suggestions for ambiguous input."""
    return await _input_processor.generate_suggestions(description, max_suggestions)


async def process_combination_personality(analysis: InputAnalysis) -> Optional[PersonalityProfile]:
    """Process combination personality requests."""
    return await _input_processor.process_combination(analysis)


async def generate_clarification_questions(analysis: InputAnalysis) -> List[ClarificationQuestion]:
    """Generate clarification questions for unclear input."""
    return await _input_processor.generate_clarification_questions(analysis)