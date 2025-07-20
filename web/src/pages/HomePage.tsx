/**
 * Home page with personality creation form
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import PersonalityForm from '../components/PersonalityForm';
import { PersonalityRequest, PersonalityConfig } from '../types/personality';
import { PersonalityApi, PersonalityApiError } from '../services/api';

const HomePage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<PersonalityConfig | null>(null);
  const navigate = useNavigate();

  const handleSubmit = async (request: PersonalityRequest) => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const config = await PersonalityApi.createPersonalityConfig(request);
      setSuccess(config);
      
      // Redirect to configurations page after a short delay
      setTimeout(() => {
        navigate('/configurations');
      }, 2000);
    } catch (err) {
      if (err instanceof PersonalityApiError) {
        setError(err.apiError.error.message);
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="home-page">
      <div className="hero-section">
        <h1>Agent Personality System</h1>
        <p className="hero-description">
          Enhance your coding agents with configurable personality traits. 
          Create custom personalities that influence how your AI assistants respond and interact.
        </p>
      </div>

      <div className="main-content">
        <div className="form-section">
          <h2>Create New Personality</h2>
          <p>
            Describe the personality you want your coding agent to adopt. 
            You can reference celebrities, fictional characters, archetypes, or describe specific traits.
          </p>

          {error && (
            <div className="alert alert-error">
              <strong>Error:</strong> {error}
            </div>
          )}

          {success && (
            <div className="alert alert-success">
              <strong>Success!</strong> Created personality "{success.profile.name}". 
              Redirecting to configurations...
            </div>
          )}

          <PersonalityForm onSubmit={handleSubmit} loading={loading} />
        </div>

        <div className="info-section">
          <h3>How it works</h3>
          <div className="steps">
            <div className="step">
              <div className="step-number">1</div>
              <div className="step-content">
                <h4>Describe</h4>
                <p>Tell us about the personality you want - a celebrity, character, or traits.</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">2</div>
              <div className="step-content">
                <h4>Research</h4>
                <p>Our system researches the personality and extracts key traits and communication style.</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">3</div>
              <div className="step-content">
                <h4>Generate</h4>
                <p>We create contextual prompts that guide your coding agent's responses.</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">4</div>
              <div className="step-content">
                <h4>Integrate</h4>
                <p>The personality is automatically integrated into your IDE environment.</p>
              </div>
            </div>
          </div>

          <div className="examples">
            <h4>Example Personalities</h4>
            <div className="example-tags">
              <span className="example-tag">Tony Stark</span>
              <span className="example-tag">Sherlock Holmes</span>
              <span className="example-tag">Friendly mentor</span>
              <span className="example-tag">Sarcastic genius</span>
              <span className="example-tag">Patient teacher</span>
              <span className="example-tag">Drill sergeant</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;