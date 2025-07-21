"""Chat message processing and natural language understanding for personality requests."""

import re
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from pydantic import BaseModel

from ..models.core import PersonalityProfile, PersonalityType, FormalityLevel, VerbosityLevel, TechnicalLevel


class ChatState(str, Enum):
    """Chat conversation states."""
    INITIAL = "initial"
    GATHERING_INFO = "gathering_info"
    CONFIRMING_PERSONALITY = "confirming_personality"
    REFINING_TRAITS = "refining_traits"
    READY_TO_APPLY = "ready_to_apply"
    COMPLETED = "completed"


class ChatMessage(BaseModel):
    """Represents a chat message from the user."""
    content: str
    timestamp: datetime
    session_id: str


class PersonalityContext(BaseModel):
    """Tracks personality information gathered during chat."""
    description: str = ""
    personality_type: Optional[PersonalityType] = None
    formality: Optional[FormalityLevel] = None
    verbosity: Optional[VerbosityLevel] = None
    technical_level: Optional[TechnicalLevel] = None
    specific_traits: List[str] = []
    examples_given: List[str] = []
    confidence_score: float = 0.0


class ChatResponse(BaseModel):
    """Response from the chat processor."""
    message: str
    timestamp: datetime
    suggestions: List[str] = []
    requires_confirmation: bool = False
    personality_config: Optional[PersonalityContext] = None
    ready_to_apply: bool = False


@dataclass
class ChatSession:
    """Represents an active chat session."""
    session_id: str
    created_at: datetime
    current_state: ChatState = ChatState.INITIAL
    messages: List[ChatMessage] = field(default_factory=list)
    personality_context: Optional[PersonalityContext] = None
    last_activity: datetime = field(default_factory=datetime.now)


def create_chat_session(session_id: str) -> ChatSession:
    """Create a new chat session."""
    return ChatSession(
        session_id=session_id,
        created_at=datetime.now(),
        personality_context=PersonalityContext()
    )


def update_chat_context(session: ChatSession, message: ChatMessage, response: ChatResponse) -> ChatSession:
    """Update chat session with new message and response."""
    session.messages.append(message)
    session.last_activity = datetime.now()
    
    if response.personality_config:
        session.personality_context = response.personality_config
    
    if response.ready_to_apply:
        session.current_state = ChatState.READY_TO_APPLY
    
    return session


# Personality detection patterns
PERSONALITY_PATTERNS = {
    # Famous people
    'celebrities': [
        r'\b(einstein|albert einstein)\b',
        r'\b(steve jobs)\b',
        r'\b(elon musk)\b',
        r'\b(bill gates)\b',
        r'\b(linus torvalds)\b',
    ],
    'fictional': [
        r'\b(sherlock holmes|sherlock)\b',
        r'\b(tony stark|iron man)\b',
        r'\b(yoda)\b',
        r'\b(spock)\b',
        r'\b(batman|bruce wayne)\b',
        r'\b(gandalf)\b',
    ],
    'archetypes': [
        r'\b(cowboy|western)\b',
        r'\b(robot|robotic|mechanical)\b',
        r'\b(drill sergeant|military|sergeant)\b',
        r'\b(mentor|teacher|wise)\b',
        r'\b(pirate|buccaneer)\b',
        r'\b(ninja|stealthy)\b',
    ]
}

# Trait detection patterns
TRAIT_PATTERNS = {
    'formality': {
        FormalityLevel.CASUAL: [r'\b(casual|relaxed|informal|chill|laid.?back)\b'],
        FormalityLevel.FORMAL: [r'\b(formal|professional|proper|polite|respectful)\b'],
        FormalityLevel.MIXED: [r'\b(mixed|balanced|flexible|adaptable)\b'],
    },
    'verbosity': {
        VerbosityLevel.CONCISE: [r'\b(brief|short|concise|minimal|terse|to.?the.?point)\b'],
        VerbosityLevel.MODERATE: [r'\b(moderate|balanced|normal|regular)\b'],
        VerbosityLevel.VERBOSE: [r'\b(detailed|verbose|thorough|explanatory|comprehensive)\b'],
    },
    'technical_level': {
        TechnicalLevel.BEGINNER: [r'\b(beginner|simple|basic|easy|novice)\b'],
        TechnicalLevel.INTERMEDIATE: [r'\b(intermediate|moderate|standard)\b'],
        TechnicalLevel.EXPERT: [r'\b(expert|advanced|technical|detailed|professional)\b'],
    }
}

# Intent detection patterns
INTENT_PATTERNS = {
    'personality_request': [
        r'\b(like|sound like|be like|act like|behave like)\b',
        r'\b(personality|character|style|manner)\b',
        r'\b(want to|would like to|make me)\b',
    ],
    'modification': [
        r'\b(but|however|except|more|less)\b',
        r'\b(change|modify|adjust|tweak)\b',
    ],
    'confirmation': [
        r'\b(yes|yeah|yep|correct|right|exactly|perfect)\b',
        r'\b(that.?s right|sounds good|looks good)\b',
    ],
    'negation': [
        r'\b(no|nope|not|wrong|incorrect)\b',
        r'\b(that.?s not|don.?t want)\b',
    ]
}


def extract_personality_info(message: str) -> Dict[str, Any]:
    """Extract personality information from a chat message."""
    message_lower = message.lower()
    info = {
        'personalities': [],
        'traits': {},
        'modifiers': [],
        'intent': None
    }
    
    # Detect personality types
    for category, patterns in PERSONALITY_PATTERNS.items():
        for pattern in patterns:
            matches = re.findall(pattern, message_lower, re.IGNORECASE)
            if matches:
                info['personalities'].append({
                    'type': category,
                    'name': matches[0],
                    'category': PersonalityType.CELEBRITY if category == 'celebrities' 
                              else PersonalityType.FICTIONAL if category == 'fictional'
                              else PersonalityType.ARCHETYPE
                })
    
    # Detect traits
    for trait_type, trait_values in TRAIT_PATTERNS.items():
        for value, patterns in trait_values.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    info['traits'][trait_type] = value
                    break
    
    # Detect intent
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                info['intent'] = intent
                break
    
    # Extract modifiers (but, more, less, etc.)
    modifier_matches = re.findall(r'\b(but|however|except|more|less|very|quite|somewhat)\s+(\w+)', message_lower)
    info['modifiers'] = modifier_matches
    
    return info


def generate_clarification_questions(context: PersonalityContext) -> List[str]:
    """Generate clarification questions based on current context."""
    questions = []
    
    if not context.description:
        questions.append("What personality would you like your coding agent to have?")
    
    if context.personality_type is None and not context.specific_traits:
        questions.extend([
            "Are you thinking of a specific person, character, or general style?",
            "Would you like something professional, casual, or creative?"
        ])
    
    if context.formality is None:
        questions.append("Should the responses be formal and professional, or more casual and relaxed?")
    
    if context.verbosity is None:
        questions.append("Do you prefer brief, concise responses or more detailed explanations?")
    
    if context.technical_level is None:
        questions.append("What's your experience level? Should I explain things simply or assume technical knowledge?")
    
    return questions[:2]  # Limit to 2 questions to avoid overwhelming


def calculate_confidence_score(context: PersonalityContext) -> float:
    """Calculate confidence score for the personality configuration."""
    score = 0.0
    
    # Base score for having a description
    if context.description:
        score += 0.3
    
    # Score for personality type
    if context.personality_type:
        score += 0.2
    
    # Score for traits
    trait_count = sum([
        1 for trait in [context.formality, context.verbosity, context.technical_level]
        if trait is not None
    ])
    score += (trait_count / 3) * 0.3
    
    # Score for specific traits
    if context.specific_traits:
        score += min(len(context.specific_traits) * 0.05, 0.2)
    
    return min(score, 1.0)


async def process_chat_message(message: ChatMessage, session: ChatSession) -> ChatResponse:
    """Process a chat message and generate an appropriate response."""
    message_info = extract_personality_info(message.content)
    context = session.personality_context or PersonalityContext()
    
    # Update context with extracted information
    if message_info['personalities']:
        personality = message_info['personalities'][0]  # Take the first one for now
        context.description = f"{personality['name']} personality"
        context.personality_type = personality['category']
    
    # Update traits
    for trait_type, value in message_info['traits'].items():
        setattr(context, trait_type, value)
    
    # Handle different intents
    intent = message_info['intent']
    
    if intent == 'confirmation' and session.current_state == ChatState.CONFIRMING_PERSONALITY:
        # User confirmed the personality
        context.confidence_score = calculate_confidence_score(context)
        
        if context.confidence_score >= 0.7:
            return ChatResponse(
                message="Perfect! I'll configure your coding agent with these settings now.",
                timestamp=datetime.now(),
                personality_config=context,
                ready_to_apply=True
            )
        else:
            questions = generate_clarification_questions(context)
            return ChatResponse(
                message="Great! Let me ask a few more questions to make sure I get this right. " + questions[0],
                timestamp=datetime.now(),
                suggestions=questions[1:] if len(questions) > 1 else [],
                personality_config=context
            )
    
    elif intent == 'negation' and session.current_state == ChatState.CONFIRMING_PERSONALITY:
        # User rejected the personality, ask for clarification
        return ChatResponse(
            message="No problem! Can you tell me more about what you're looking for? What would you like to change?",
            timestamp=datetime.now(),
            suggestions=[
                "I want something more professional",
                "Make it more casual",
                "I prefer a different personality entirely"
            ]
        )
    
    elif intent == 'personality_request' or message_info['personalities']:
        # User is requesting a personality
        if message_info['personalities']:
            personality = message_info['personalities'][0]
            personality_name = personality['name'].title()
            
            # Generate confirmation message
            confirmation_msg = f"I found information about {personality_name}. "
            
            # Add trait information if detected
            trait_descriptions = []
            if context.formality:
                trait_descriptions.append(f"{context.formality.value} communication style")
            if context.verbosity:
                trait_descriptions.append(f"{context.verbosity.value} responses")
            if context.technical_level:
                trait_descriptions.append(f"{context.technical_level.value}-level explanations")
            
            if trait_descriptions:
                confirmation_msg += f"I'll configure it with {', '.join(trait_descriptions)}. "
            
            confirmation_msg += "Does this sound right?"
            
            return ChatResponse(
                message=confirmation_msg,
                timestamp=datetime.now(),
                suggestions=["Yes, that's perfect", "Make some adjustments", "Try a different personality"],
                requires_confirmation=True,
                personality_config=context
            )
        else:
            # General personality request without specific name
            questions = generate_clarification_questions(context)
            return ChatResponse(
                message="I'd be happy to help configure a personality for your coding agent! " + questions[0],
                timestamp=datetime.now(),
                suggestions=questions[1:] if len(questions) > 1 else [
                    "Like Sherlock Holmes - analytical and precise",
                    "Like a friendly mentor - patient and encouraging", 
                    "Like Tony Stark - confident and witty"
                ]
            )
    
    else:
        # General conversation or unclear intent
        if not context.description:
            return ChatResponse(
                message="Hi! I can help you configure a personality for your coding agent. What kind of personality would you like?",
                timestamp=datetime.now(),
                suggestions=[
                    "Make it like Sherlock Holmes",
                    "I want a friendly mentor style",
                    "Something professional but approachable"
                ]
            )
        else:
            # Continue gathering information
            questions = generate_clarification_questions(context)
            if questions:
                return ChatResponse(
                    message=questions[0],
                    timestamp=datetime.now(),
                    suggestions=questions[1:] if len(questions) > 1 else [],
                    personality_config=context
                )
            else:
                # We have enough information
                context.confidence_score = calculate_confidence_score(context)
                return ChatResponse(
                    message="I think I have enough information to configure your personality. Should I proceed?",
                    timestamp=datetime.now(),
                    suggestions=["Yes, apply it", "Let me make some changes first"],
                    requires_confirmation=True,
                    personality_config=context,
                    ready_to_apply=True
                )