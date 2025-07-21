"""Unit tests for chat message processing functionality."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from src.covibe.services.chat_processor import (
    ChatMessage,
    ChatSession,
    ChatState,
    PersonalityContext,
    create_chat_session,
    update_chat_context,
    extract_personality_info,
    generate_clarification_questions,
    calculate_confidence_score,
    process_chat_message,
)
from src.covibe.models.core import PersonalityType, FormalityLevel, VerbosityLevel, TechnicalLevel


class TestChatSession:
    """Test chat session management."""
    
    def test_create_chat_session(self):
        """Test creating a new chat session."""
        session_id = "test_session_123"
        session = create_chat_session(session_id)
        
        assert session.session_id == session_id
        assert session.current_state == ChatState.INITIAL
        assert len(session.messages) == 0
        assert session.personality_context is not None
        assert isinstance(session.created_at, datetime)
    
    def test_update_chat_context(self):
        """Test updating chat session context."""
        session = create_chat_session("test_session")
        message = ChatMessage(
            content="I want to code like Sherlock Holmes",
            timestamp=datetime.now(),
            session_id="test_session"
        )
        
        from src.covibe.services.chat_processor import ChatResponse
        response = ChatResponse(
            message="Great choice!",
            timestamp=datetime.now(),
            personality_config=PersonalityContext(description="Sherlock Holmes personality")
        )
        
        updated_session = update_chat_context(session, message, response)
        
        assert len(updated_session.messages) == 1
        assert updated_session.messages[0] == message
        assert updated_session.personality_context.description == "Sherlock Holmes personality"


class TestPersonalityExtraction:
    """Test personality information extraction from messages."""
    
    def test_extract_celebrity_personality(self):
        """Test extracting celebrity personalities."""
        message = "I want to code like Einstein"
        info = extract_personality_info(message)
        
        assert len(info['personalities']) == 1
        personality = info['personalities'][0]
        assert personality['type'] == 'celebrities'
        assert 'einstein' in personality['name'].lower()
        assert personality['category'] == PersonalityType.CELEBRITY
    
    def test_extract_fictional_personality(self):
        """Test extracting fictional character personalities."""
        message = "Make me sound like Sherlock Holmes"
        info = extract_personality_info(message)
        
        assert len(info['personalities']) == 1
        personality = info['personalities'][0]
        assert personality['type'] == 'fictional'
        assert 'sherlock holmes' in personality['name'].lower()
        assert personality['category'] == PersonalityType.FICTIONAL
    
    def test_extract_archetype_personality(self):
        """Test extracting archetype personalities."""
        message = "I want a cowboy personality"
        info = extract_personality_info(message)
        
        assert len(info['personalities']) == 1
        personality = info['personalities'][0]
        assert personality['type'] == 'archetypes'
        assert 'cowboy' in personality['name'].lower()
        assert personality['category'] == PersonalityType.ARCHETYPE
    
    def test_extract_formality_traits(self):
        """Test extracting formality level traits."""
        test_cases = [
            ("I want something casual and relaxed", FormalityLevel.CASUAL),
            ("Make it formal and professional", FormalityLevel.FORMAL),
            ("Something balanced and flexible", FormalityLevel.MIXED),
        ]
        
        for message, expected_formality in test_cases:
            info = extract_personality_info(message)
            assert info['traits'].get('formality') == expected_formality
    
    def test_extract_verbosity_traits(self):
        """Test extracting verbosity level traits."""
        test_cases = [
            ("Keep it brief and concise", VerbosityLevel.CONCISE),
            ("I want detailed explanations", VerbosityLevel.VERBOSE),
            ("Something moderate and balanced", VerbosityLevel.MODERATE),
        ]
        
        for message, expected_verbosity in test_cases:
            info = extract_personality_info(message)
            assert info['traits'].get('verbosity') == expected_verbosity
    
    def test_extract_technical_level_traits(self):
        """Test extracting technical level traits."""
        test_cases = [
            ("Keep it simple for beginners", TechnicalLevel.BEGINNER),
            ("I'm an expert developer", TechnicalLevel.EXPERT),
            ("Something intermediate level", TechnicalLevel.INTERMEDIATE),
        ]
        
        for message, expected_level in test_cases:
            info = extract_personality_info(message)
            assert info['traits'].get('technical_level') == expected_level
    
    def test_extract_intent_patterns(self):
        """Test extracting user intent from messages."""
        test_cases = [
            ("I want to be like Tony Stark", "personality_request"),
            ("Yes, that sounds perfect", "confirmation"),
            ("No, that's not right", "negation"),
            ("But make it more professional", "modification"),
        ]
        
        for message, expected_intent in test_cases:
            info = extract_personality_info(message)
            assert info['intent'] == expected_intent


class TestClarificationQuestions:
    """Test clarification question generation."""
    
    def test_generate_questions_empty_context(self):
        """Test generating questions for empty context."""
        context = PersonalityContext()
        questions = generate_clarification_questions(context)
        
        assert len(questions) > 0
        assert any("personality" in q.lower() for q in questions)
    
    def test_generate_questions_partial_context(self):
        """Test generating questions for partial context."""
        context = PersonalityContext(
            description="Sherlock Holmes personality",
            personality_type=PersonalityType.FICTIONAL
        )
        questions = generate_clarification_questions(context)
        
        # Should ask about missing traits
        assert len(questions) <= 2  # Limited to 2 questions
        assert any("formal" in q.lower() or "casual" in q.lower() for q in questions)
    
    def test_generate_questions_complete_context(self):
        """Test generating questions for complete context."""
        context = PersonalityContext(
            description="Complete personality",
            personality_type=PersonalityType.FICTIONAL,
            formality=FormalityLevel.FORMAL,
            verbosity=VerbosityLevel.MODERATE,
            technical_level=TechnicalLevel.EXPERT
        )
        questions = generate_clarification_questions(context)
        
        # Should have fewer or no questions
        assert len(questions) <= 1


class TestConfidenceScore:
    """Test confidence score calculation."""
    
    def test_confidence_score_empty_context(self):
        """Test confidence score for empty context."""
        context = PersonalityContext()
        score = calculate_confidence_score(context)
        
        assert score == 0.0
    
    def test_confidence_score_partial_context(self):
        """Test confidence score for partial context."""
        context = PersonalityContext(
            description="Test personality",
            personality_type=PersonalityType.FICTIONAL
        )
        score = calculate_confidence_score(context)
        
        assert 0.0 < score < 1.0
        assert score == 0.5  # 0.3 for description + 0.2 for personality type
    
    def test_confidence_score_complete_context(self):
        """Test confidence score for complete context."""
        context = PersonalityContext(
            description="Complete personality",
            personality_type=PersonalityType.FICTIONAL,
            formality=FormalityLevel.FORMAL,
            verbosity=VerbosityLevel.MODERATE,
            technical_level=TechnicalLevel.EXPERT,
            specific_traits=["analytical", "precise", "logical"]
        )
        score = calculate_confidence_score(context)
        
        assert score >= 0.8  # Should be high confidence
        assert score <= 1.0


class TestChatMessageProcessing:
    """Test chat message processing logic."""
    
    @pytest.mark.asyncio
    async def test_process_initial_personality_request(self):
        """Test processing initial personality request."""
        session = create_chat_session("test_session")
        message = ChatMessage(
            content="I want to code like Sherlock Holmes",
            timestamp=datetime.now(),
            session_id="test_session"
        )
        
        response = await process_chat_message(message, session)
        
        assert "Sherlock Holmes" in response.message
        assert response.requires_confirmation
        assert response.personality_config is not None
        assert response.personality_config.description == "sherlock holmes personality"
    
    @pytest.mark.asyncio
    async def test_process_confirmation_message(self):
        """Test processing confirmation message."""
        session = create_chat_session("test_session")
        session.current_state = ChatState.CONFIRMING_PERSONALITY
        session.personality_context = PersonalityContext(
            description="Sherlock Holmes personality",
            personality_type=PersonalityType.FICTIONAL,
            formality=FormalityLevel.FORMAL,
            verbosity=VerbosityLevel.MODERATE,
            technical_level=TechnicalLevel.EXPERT
        )
        
        message = ChatMessage(
            content="Yes, that's perfect",
            timestamp=datetime.now(),
            session_id="test_session"
        )
        
        response = await process_chat_message(message, session)
        
        assert response.ready_to_apply
        assert "configure" in response.message.lower()
    
    @pytest.mark.asyncio
    async def test_process_negation_message(self):
        """Test processing negation message."""
        session = create_chat_session("test_session")
        session.current_state = ChatState.CONFIRMING_PERSONALITY
        
        message = ChatMessage(
            content="No, that's not right",
            timestamp=datetime.now(),
            session_id="test_session"
        )
        
        response = await process_chat_message(message, session)
        
        assert not response.ready_to_apply
        assert "what would you like to change" in response.message.lower()
        assert len(response.suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_process_general_conversation(self):
        """Test processing general conversation."""
        session = create_chat_session("test_session")
        message = ChatMessage(
            content="Hello, can you help me?",
            timestamp=datetime.now(),
            session_id="test_session"
        )
        
        response = await process_chat_message(message, session)
        
        assert "personality" in response.message.lower()
        assert len(response.suggestions) > 0
        assert not response.ready_to_apply
    
    @pytest.mark.asyncio
    async def test_process_trait_specification(self):
        """Test processing message with specific traits."""
        session = create_chat_session("test_session")
        message = ChatMessage(
            content="I want something casual and brief like Tony Stark",
            timestamp=datetime.now(),
            session_id="test_session"
        )
        
        response = await process_chat_message(message, session)
        
        assert response.personality_config is not None
        assert "tony stark" in response.personality_config.description.lower()
        assert "casual" in response.message.lower() or response.personality_config.formality == FormalityLevel.CASUAL


if __name__ == "__main__":
    pytest.main([__file__])