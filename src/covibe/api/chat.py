"""WebSocket chat interface for personality configuration."""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel, ValidationError

from ..models.core import PersonalityRequest, SourceType
from ..services.orchestration import orchestrate_personality_request
from ..services.chat_processor import (
    process_chat_message,
    ChatMessage,
    ChatResponse,
    ChatSession,
    create_chat_session,
    update_chat_context,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ConnectionManager:
    """Manages WebSocket connections and chat sessions."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.chat_sessions: Dict[str, ChatSession] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.chat_sessions[session_id] = create_chat_session(session_id)
        logger.info(f"WebSocket connection established for session {session_id}")
    
    def disconnect(self, session_id: str):
        """Remove a WebSocket connection."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.chat_sessions:
            del self.chat_sessions[session_id]
        logger.info(f"WebSocket connection closed for session {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        """Send a message to a specific session."""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_text(json.dumps(message))
    
    async def send_error(self, session_id: str, error_message: str, error_code: str = "CHAT_ERROR"):
        """Send an error message to a specific session."""
        error_response = {
            "type": "error",
            "error": {
                "code": error_code,
                "message": error_message,
                "timestamp": datetime.now().isoformat()
            }
        }
        await self.send_message(session_id, error_response)
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a chat session by ID."""
        return self.chat_sessions.get(session_id)
    
    def update_session(self, session_id: str, session: ChatSession):
        """Update a chat session."""
        self.chat_sessions[session_id] = session


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for chat interface."""
    await manager.connect(websocket, session_id)
    
    try:
        # Send welcome message
        welcome_message = {
            "type": "system",
            "message": "Welcome! I can help you configure personality traits for your coding agent. Try saying something like 'I want to code like Sherlock Holmes' or 'Make me sound more like a friendly mentor'.",
            "timestamp": datetime.now().isoformat()
        }
        await manager.send_message(session_id, welcome_message)
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                # Parse incoming message
                message_data = json.loads(data)
                
                # Validate message format
                if "message" not in message_data:
                    await manager.send_error(session_id, "Message field is required")
                    continue
                
                user_message = message_data["message"].strip()
                if not user_message:
                    await manager.send_error(session_id, "Message cannot be empty")
                    continue
                
                # Get current session
                session = manager.get_session(session_id)
                if not session:
                    await manager.send_error(session_id, "Session not found")
                    continue
                
                # Create chat message
                chat_message = ChatMessage(
                    content=user_message,
                    timestamp=datetime.now(),
                    session_id=session_id
                )
                
                # Send typing indicator
                typing_message = {
                    "type": "typing",
                    "message": "Processing your request...",
                    "timestamp": datetime.now().isoformat()
                }
                await manager.send_message(session_id, typing_message)
                
                # Process the chat message
                chat_response = await process_chat_message(chat_message, session)
                
                # Update session context
                updated_session = update_chat_context(session, chat_message, chat_response)
                manager.update_session(session_id, updated_session)
                
                # Send response back to client
                response_message = {
                    "type": "assistant",
                    "message": chat_response.message,
                    "timestamp": chat_response.timestamp.isoformat(),
                    "suggestions": chat_response.suggestions,
                    "requires_confirmation": chat_response.requires_confirmation,
                    "personality_config": chat_response.personality_config.dict() if chat_response.personality_config else None
                }
                await manager.send_message(session_id, response_message)
                
                # If we have a complete personality configuration, trigger the orchestration
                if chat_response.personality_config and chat_response.ready_to_apply:
                    try:
                        # Create personality request
                        personality_request = PersonalityRequest(
                            id=str(uuid4()),
                            description=chat_response.personality_config.description,
                            user_id=session_id,
                            timestamp=datetime.now(),
                            source=SourceType.CHAT
                        )
                        
                        # Process the personality request
                        result = await orchestrate_personality_request(personality_request)
                        
                        if result.success and result.config:
                            # Send success message
                            success_message = {
                                "type": "success",
                                "message": f"Great! I've configured your agent with the {result.config.profile.name} personality. The configuration has been applied to your IDE.",
                                "timestamp": datetime.now().isoformat(),
                                "config_id": result.config.id,
                                "profile": result.config.profile.dict()
                            }
                        else:
                            # Send error message if orchestration failed
                            error_msg = result.error.message if result.error else "Unknown error occurred"
                            success_message = {
                                "type": "error",
                                "message": f"I encountered an issue while configuring your personality: {error_msg}",
                                "timestamp": datetime.now().isoformat()
                            }
                        await manager.send_message(session_id, success_message)
                        
                    except Exception as e:
                        logger.error(f"Error processing personality request: {e}")
                        await manager.send_error(
                            session_id, 
                            f"I encountered an error while configuring your personality: {str(e)}",
                            "PROCESSING_ERROR"
                        )
                
            except json.JSONDecodeError:
                await manager.send_error(session_id, "Invalid JSON format")
            except ValidationError as e:
                await manager.send_error(session_id, f"Validation error: {str(e)}")
            except Exception as e:
                logger.error(f"Error processing chat message: {e}")
                await manager.send_error(session_id, "An unexpected error occurred while processing your message")
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        manager.disconnect(session_id)


@router.get("/sessions/{session_id}")
async def get_chat_session(session_id: str):
    """Get chat session information."""
    session = manager.get_session(session_id)
    if not session:
        return {"error": "Session not found"}
    
    return {
        "session_id": session.session_id,
        "created_at": session.created_at.isoformat(),
        "message_count": len(session.messages),
        "current_state": session.current_state,
        "personality_context": session.personality_context.dict() if session.personality_context else None
    }


@router.delete("/sessions/{session_id}")
async def clear_chat_session(session_id: str):
    """Clear a chat session."""
    if session_id in manager.chat_sessions:
        # Reset the session but keep it active
        manager.chat_sessions[session_id] = create_chat_session(session_id)
        return {"message": "Session cleared successfully"}
    
    return {"error": "Session not found"}