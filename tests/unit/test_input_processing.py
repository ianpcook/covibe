"""Tests for advanced personality input processing."""

import pytest
from unittest.mock import AsyncMock, patch

from src.covibe.services.input_processing import (
    AdvancedInputProcessor,
    FuzzyMatcher,
    CombinationParser,
    PersonalityKnowledgeBase,
    InputType,
    CombinationType,
    analyze_personality_input,
    generate_personality_suggestions,
    process_combination_personality,
    generate_clarification_questions
)
from src.covibe.models.core import PersonalityProfile, PersonalityType


class TestFuzzyMatcher:
    """Test fuzzy matching functionality."""
    
    def test_levenshtein_distance(self):
        """Test Levenshtein distance calculation."""
        matcher = FuzzyMatcher()
        
        # Identical strings
        assert matcher.levenshtein_distance("hello", "hello") == 0
        
        # Single character difference
        assert matcher.levenshtein_distance("hello", "hallo") == 1
        
        # Multiple differences
        assert matcher.levenshtein_distance("kitten", "sitting") == 3
        
        # Empty strings
        assert matcher.levenshtein_distance("", "") == 0
        assert matcher.levenshtein_distance("hello", "") == 5
    
    def test_similarity_score(self):
        """Test similarity score calculation."""
        matcher = FuzzyMatcher()
        
        # Identical strings
        assert matcher.similarity_score("hello", "hello") == 1.0
        
        # Similar strings
        score = matcher.similarity_score("tony stark", "tony start")
        assert 0.8 < score < 1.0
        
        # Different strings
        score = matcher.similarity_score("tony stark", "yoda")
        assert score < 0.5
        
        # Empty strings
        assert matcher.similarity_score("", "") == 0.0
        assert matcher.similarity_score("hello", "") == 0.0
    
    def test_find_best_matches(self):
        """Test finding best matches from candidates."""
        matcher = FuzzyMatcher()
        candidates = ["tony stark", "sherlock holmes", "yoda", "einstein"]
        
        # Exact match
        matches = matcher.find_best_matches("tony stark", candidates)
        assert len(matches) > 0
        assert matches[0][0] == "tony stark"
        assert matches[0][1] == 1.0
        
        # Fuzzy match
        matches = matcher.find_best_matches("tony start", candidates, threshold=0.7)
        assert len(matches) > 0
        assert matches[0][0] == "tony stark"
        assert matches[0][1] > 0.8
        
        # No good matches
        matches = matcher.find_best_matches("completely different", candidates, threshold=0.8)
        assert len(matches) == 0


class TestPersonalityKnowledgeBase:
    """Test personality knowledge base functionality."""
    
    def test_get_all_names(self):
        """Test getting all personality names."""
        kb = PersonalityKnowledgeBase()
        names = kb.get_all_names()
        
        assert "tony stark" in names
        assert "iron man" in names  # alias
        assert "sherlock holmes" in names
        assert "mentor" in names
        assert "genius" in names
        assert len(names) > 10
    
    def test_find_personality_type(self):
        """Test finding personality types."""
        kb = PersonalityKnowledgeBase()
        
        # Character names
        assert kb.find_personality_type("tony stark") == PersonalityType.FICTIONAL
        assert kb.find_personality_type("iron man") == PersonalityType.FICTIONAL  # alias
        assert kb.find_personality_type("einstein") == PersonalityType.CELEBRITY
        
        # Archetype names
        assert kb.find_personality_type("mentor") == PersonalityType.ARCHETYPE
        assert kb.find_personality_type("robot") == PersonalityType.ARCHETYPE
        
        # Unknown names
        assert kb.find_personality_type("unknown character") is None


class TestCombinationParser:
    """Test combination parsing functionality."""
    
    def test_but_more_patterns(self):
        """Test 'but more' combination patterns."""
        parser = CombinationParser()
        
        # Standard pattern
        result = parser.parse_combination("tony stark but more patient")
        assert result is not None
        combo_type, primary, modifier = result
        assert combo_type == CombinationType.BUT_MORE
        assert primary == "tony stark"
        assert modifier == "patient"
        
        # Alternative patterns
        result = parser.parse_combination("sherlock but with more humor")
        assert result is not None
        assert result[0] == CombinationType.BUT_MORE
        
        result = parser.parse_combination("yoda but extra wise")
        assert result is not None
        assert result[0] == CombinationType.BUT_MORE
    
    def test_but_less_patterns(self):
        """Test 'but less' combination patterns."""
        parser = CombinationParser()
        
        result = parser.parse_combination("tony stark but less arrogant")
        assert result is not None
        combo_type, primary, modifier = result
        assert combo_type == CombinationType.BUT_LESS
        assert primary == "tony stark"
        assert modifier == "arrogant"
        
        result = parser.parse_combination("sherlock but without condescension")
        assert result is not None
        assert result[0] == CombinationType.BUT_LESS
    
    def test_mixed_with_patterns(self):
        """Test 'mixed with' combination patterns."""
        parser = CombinationParser()
        
        result = parser.parse_combination("tony stark mixed with einstein")
        assert result is not None
        combo_type, primary, modifier = result
        assert combo_type == CombinationType.MIXED_WITH
        assert primary == "tony stark"
        assert modifier == "einstein"
        
        result = parser.parse_combination("sherlock combined with yoda")
        assert result is not None
        assert result[0] == CombinationType.MIXED_WITH
    
    def test_like_but_patterns(self):
        """Test 'like but' combination patterns."""
        parser = CombinationParser()
        
        result = parser.parse_combination("like tony stark but calmer")
        assert result is not None
        combo_type, primary, modifier = result
        assert combo_type == CombinationType.LIKE_BUT
        assert primary == "tony stark"
        assert modifier == "calmer"
    
    def test_no_combination(self):
        """Test input without combination patterns."""
        parser = CombinationParser()
        
        result = parser.parse_combination("tony stark")
        assert result is None
        
        result = parser.parse_combination("genius mentor")
        assert result is None


class TestAdvancedInputProcessor:
    """Test advanced input processor functionality."""
    
    @pytest.fixture
    def processor(self):
        """Create input processor instance."""
        return AdvancedInputProcessor()
    
    @pytest.mark.asyncio
    async def test_analyze_specific_name(self, processor):
        """Test analysis of specific character names."""
        # Exact match
        analysis = await processor.analyze_input("tony stark")
        assert analysis.input_type == InputType.SPECIFIC_NAME
        assert analysis.confidence > 0.85
        assert analysis.primary_personality == "tony stark"
        
        # Fuzzy match
        analysis = await processor.analyze_input("tony start")  # typo
        assert analysis.input_type == InputType.AMBIGUOUS
        assert analysis.confidence > 0.6
        assert analysis.suggestions and "tony stark" in analysis.suggestions
    
    @pytest.mark.asyncio
    async def test_analyze_combination(self, processor):
        """Test analysis of combination requests."""
        analysis = await processor.analyze_input("tony stark but more patient")
        assert analysis.input_type == InputType.COMBINATION
        assert analysis.confidence == 0.9
        assert analysis.primary_personality == "tony stark"
        assert analysis.modifiers == ["patient"]
        assert analysis.combination_type == CombinationType.BUT_MORE
    
    @pytest.mark.asyncio
    async def test_analyze_descriptive_phrase(self, processor):
        """Test analysis of descriptive phrases."""
        analysis = await processor.analyze_input("friendly mentor")
        assert analysis.input_type == InputType.DESCRIPTIVE_PHRASE
        assert analysis.confidence == 0.7
        assert analysis.primary_personality == "friendly mentor"
    
    @pytest.mark.asyncio
    async def test_analyze_unclear_input(self, processor):
        """Test analysis of unclear input."""
        analysis = await processor.analyze_input("something weird")
        assert analysis.input_type == InputType.UNCLEAR
        assert analysis.confidence == 0.3
        assert len(analysis.clarification_questions) > 0
    
    @pytest.mark.asyncio
    async def test_generate_suggestions(self, processor):
        """Test suggestion generation."""
        suggestions = await processor.generate_suggestions("tony start", max_suggestions=3)
        assert len(suggestions) <= 3
        assert any("tony stark" in s.name.lower() for s in suggestions)
        # Check that suggestions have reasonable confidence (allowing for some low confidence matches)
        assert all(s.confidence >= 0.4 for s in suggestions) or len(suggestions) == 0
    
    @pytest.mark.asyncio
    async def test_process_combination_success(self, processor):
        """Test successful combination processing."""
        # Mock the research_personality function
        with patch('src.covibe.services.input_processing.research_personality') as mock_research:
            # Create a mock research result
            from src.covibe.models.core import CommunicationStyle, FormalityLevel, VerbosityLevel, TechnicalLevel
            
            mock_comm_style = CommunicationStyle(
                tone="confident",
                formality=FormalityLevel.CASUAL,
                verbosity=VerbosityLevel.MODERATE,
                technical_level=TechnicalLevel.EXPERT
            )
            
            mock_profile = PersonalityProfile(
                id="test_profile",
                name="Tony Stark",
                type=PersonalityType.FICTIONAL,
                traits=[],
                communication_style=mock_comm_style,
                mannerisms=[],
                sources=[]
            )
            
            mock_research_result = type('MockResult', (), {
                'profiles': [mock_profile]
            })()
            mock_research.return_value = mock_research_result
            
            # Create analysis for combination
            analysis = await processor.analyze_input("tony stark but more patient")
            
            # Process combination
            result = await processor.process_combination(analysis)
            
            assert result is not None
            assert "modified" in result.name.lower()
            mock_research.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_combination_failure(self, processor):
        """Test combination processing with failed research."""
        with patch('src.covibe.services.input_processing.research_personality') as mock_research:
            # Mock failed research
            mock_research_result = type('MockResult', (), {
                'profiles': []
            })()
            mock_research.return_value = mock_research_result
            
            analysis = await processor.analyze_input("unknown character but more patient")
            result = await processor.process_combination(analysis)
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_clarification_questions(self, processor):
        """Test clarification question generation."""
        # Ambiguous input
        analysis = await processor.analyze_input("tony start")  # typo
        questions = await processor.generate_clarification_questions(analysis)
        
        # Should have clarification questions for ambiguous input
        if analysis.input_type == InputType.AMBIGUOUS:
            assert len(questions) > 0
            assert any("which personality" in q.question.lower() for q in questions)
        
        # Unclear input
        analysis = await processor.analyze_input("something unclear")
        questions = await processor.generate_clarification_questions(analysis)
        
        assert len(questions) > 0
        assert any("what type" in q.question.lower() for q in questions)


class TestInputProcessingFunctions:
    """Test module-level functions."""
    
    @pytest.mark.asyncio
    async def test_analyze_personality_input(self):
        """Test analyze_personality_input function."""
        analysis = await analyze_personality_input("tony stark")
        assert analysis.input_type == InputType.SPECIFIC_NAME
        assert analysis.primary_personality == "tony stark"
    
    @pytest.mark.asyncio
    async def test_generate_personality_suggestions(self):
        """Test generate_personality_suggestions function."""
        suggestions = await generate_personality_suggestions("tony start", max_suggestions=3)
        assert len(suggestions) <= 3
        assert all(hasattr(s, 'name') and hasattr(s, 'confidence') for s in suggestions)
    
    @pytest.mark.asyncio
    async def test_process_combination_personality(self):
        """Test process_combination_personality function."""
        with patch('src.covibe.services.input_processing.research_personality') as mock_research:
            from src.covibe.models.core import CommunicationStyle, FormalityLevel, VerbosityLevel, TechnicalLevel
            
            mock_comm_style = CommunicationStyle(
                tone="confident",
                formality=FormalityLevel.CASUAL,
                verbosity=VerbosityLevel.MODERATE,
                technical_level=TechnicalLevel.EXPERT
            )
            
            mock_profile = PersonalityProfile(
                id="test_profile",
                name="Tony Stark",
                type=PersonalityType.FICTIONAL,
                traits=[],
                communication_style=mock_comm_style,
                mannerisms=[],
                sources=[]
            )
            
            mock_research_result = type('MockResult', (), {
                'profiles': [mock_profile]
            })()
            mock_research.return_value = mock_research_result
            
            analysis = await analyze_personality_input("tony stark but more patient")
            result = await process_combination_personality(analysis)
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_generate_clarification_questions(self):
        """Test generate_clarification_questions function."""
        analysis = await analyze_personality_input("unclear input")
        questions = await generate_clarification_questions(analysis)
        
        assert isinstance(questions, list)
        assert all(hasattr(q, 'question') and hasattr(q, 'options') for q in questions)


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.mark.asyncio
    async def test_empty_input(self):
        """Test handling of empty input."""
        analysis = await analyze_personality_input("")
        assert analysis.input_type == InputType.UNCLEAR
        assert len(analysis.clarification_questions) > 0
    
    @pytest.mark.asyncio
    async def test_very_long_input(self):
        """Test handling of very long input."""
        long_input = "a" * 1000
        analysis = await analyze_personality_input(long_input)
        # Should handle gracefully without crashing
        assert analysis is not None
    
    @pytest.mark.asyncio
    async def test_special_characters(self):
        """Test handling of special characters."""
        analysis = await analyze_personality_input("tony stark!@#$%")
        # Should still recognize the character name
        assert analysis.input_type in [InputType.SPECIFIC_NAME, InputType.AMBIGUOUS]
    
    @pytest.mark.asyncio
    async def test_case_insensitive_matching(self):
        """Test case insensitive matching."""
        analysis1 = await analyze_personality_input("TONY STARK")
        analysis2 = await analyze_personality_input("tony stark")
        analysis3 = await analyze_personality_input("Tony Stark")
        
        # All should be recognized as the same character
        assert analysis1.input_type == analysis2.input_type == analysis3.input_type
        assert analysis1.primary_personality.lower() == analysis2.primary_personality.lower() == analysis3.primary_personality.lower()