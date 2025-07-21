import React, { useState } from 'react';
import ChatInterface from '../components/ChatInterface';
import './ChatPage.css';

const ChatPage: React.FC = () => {
  const [configuredPersonality, setConfiguredPersonality] = useState<any>(null);

  const handlePersonalityConfigured = (config: any) => {
    setConfiguredPersonality(config);
  };

  return (
    <div className="chat-page">
      <div className="chat-page-header">
        <h1>💬 Chat Configuration</h1>
        <p>
          Have a conversation with our AI assistant to configure your agent's personality. 
          Just describe what you want in natural language!
        </p>
      </div>

      <div className="chat-page-content">
        <div className="chat-section">
          <div className="chat-instructions">
            <h3>How to use:</h3>
            <ul>
              <li>💭 Describe the personality you want (e.g., "Make me sound like Sherlock Holmes")</li>
              <li>🎯 Specify traits (e.g., "I want something casual and brief")</li>
              <li>🔄 Refine your request through conversation</li>
              <li>✅ Confirm when you're happy with the configuration</li>
            </ul>
            
            <div className="example-prompts">
              <h4>Try these examples:</h4>
              <div className="example-buttons">
                <button className="example-btn">"I want to code like Tony Stark"</button>
                <button className="example-btn">"Make me sound like a friendly mentor"</button>
                <button className="example-btn">"Something professional but approachable"</button>
                <button className="example-btn">"Like Yoda, but for programming"</button>
              </div>
            </div>
          </div>

          <div className="chat-container">
            <ChatInterface onPersonalityConfigured={handlePersonalityConfigured} />
          </div>
        </div>

        {configuredPersonality && (
          <div className="success-panel">
            <div className="success-header">
              <h3>🎉 Personality Configured!</h3>
            </div>
            <div className="success-content">
              <p>
                Your agent has been configured with the <strong>{configuredPersonality.profile?.name}</strong> personality.
              </p>
              <div className="success-details">
                <h4>Configuration Details:</h4>
                <ul>
                  <li><strong>ID:</strong> {configuredPersonality.id}</li>
                  <li><strong>Type:</strong> {configuredPersonality.profile?.type}</li>
                  <li><strong>Applied:</strong> {new Date().toLocaleString()}</li>
                </ul>
              </div>
              <div className="success-actions">
                <button 
                  className="btn btn-primary"
                  onClick={() => window.location.href = '/configurations'}
                >
                  View All Configurations
                </button>
                <button 
                  className="btn btn-secondary"
                  onClick={() => setConfiguredPersonality(null)}
                >
                  Configure Another
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatPage;