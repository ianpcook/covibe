import React, { useState, useEffect, useRef, useCallback } from 'react';
import './ChatInterface.css';

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system' | 'error' | 'typing' | 'success';
  message: string;
  timestamp: string;
  suggestions?: string[];
  requires_confirmation?: boolean;
  personality_config?: any;
}

interface ChatInterfaceProps {
  onPersonalityConfigured?: (config: any) => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onPersonalityConfigured }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  
  const websocketRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  const connectWebSocket = useCallback(() => {
    const wsUrl = `ws://localhost:8000/api/chat/ws/${sessionId}`;
    
    try {
      websocketRef.current = new WebSocket(wsUrl);
      
      websocketRef.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
      };
      
      websocketRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Handle typing indicator
          if (data.type === 'typing') {
            setIsTyping(true);
            return;
          }
          
          // Remove typing indicator when we get a real message
          setIsTyping(false);
          
          const newMessage: ChatMessage = {
            id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            type: data.type || 'assistant',
            message: data.message,
            timestamp: data.timestamp,
            suggestions: data.suggestions,
            requires_confirmation: data.requires_confirmation,
            personality_config: data.personality_config
          };
          
          setMessages(prev => [...prev, newMessage]);
          
          // If personality was successfully configured, notify parent
          if (data.type === 'success' && data.config_id && onPersonalityConfigured) {
            onPersonalityConfigured({
              id: data.config_id,
              profile: data.profile
            });
          }
          
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      websocketRef.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setIsTyping(false);
        
        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
          if (!websocketRef.current || websocketRef.current.readyState === WebSocket.CLOSED) {
            connectWebSocket();
          }
        }, 3000);
      };
      
      websocketRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
        setIsTyping(false);
      };
      
    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      setIsConnected(false);
    }
  }, [sessionId, onPersonalityConfigured]);

  useEffect(() => {
    connectWebSocket();
    
    return () => {
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, [connectWebSocket]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, scrollToBottom]);

  const sendMessage = useCallback((message: string) => {
    if (!message.trim() || !websocketRef.current || websocketRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    // Add user message to chat
    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type: 'user',
      message: message.trim(),
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);

    // Send message to WebSocket
    websocketRef.current.send(JSON.stringify({
      message: message.trim()
    }));

    setInputValue('');
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(inputValue);
  };

  const handleSuggestionClick = (suggestion: string) => {
    sendMessage(suggestion);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputValue);
    }
  };

  const clearChat = () => {
    setMessages([]);
    // Optionally clear session on backend
    fetch(`http://localhost:8000/api/chat/sessions/${sessionId}`, {
      method: 'DELETE'
    }).catch(console.error);
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <div className="chat-title">
          <h3>🤖 Personality Chat Assistant</h3>
          <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
          </div>
        </div>
        <button onClick={clearChat} className="btn btn-secondary btn-sm">
          Clear Chat
        </button>
      </div>

      <div className="chat-messages">
        {messages.map((message) => (
          <div key={message.id} className={`message message-${message.type}`}>
            <div className="message-content">
              <div className="message-text">{message.message}</div>
              <div className="message-timestamp">
                {new Date(message.timestamp).toLocaleTimeString()}
              </div>
            </div>
            
            {message.suggestions && message.suggestions.length > 0 && (
              <div className="message-suggestions">
                <div className="suggestions-label">Quick replies:</div>
                <div className="suggestions-buttons">
                  {message.suggestions.map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="suggestion-btn"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
        
        {isTyping && (
          <div className="message message-typing">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <div className="message-text">Assistant is typing...</div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="chat-input-form">
        <div className="chat-input-container">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={isConnected ? "Type your message..." : "Connecting..."}
            disabled={!isConnected}
            className="chat-input"
          />
          <button
            type="submit"
            disabled={!isConnected || !inputValue.trim()}
            className="chat-send-btn"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatInterface;