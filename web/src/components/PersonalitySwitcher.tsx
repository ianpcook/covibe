/**
 * Personality switcher component for quick profile switching
 */

import React, { useState, useEffect, useRef } from 'react';
import { PersonalityConfig } from '../types/personality';
import { PersonalityApi, PersonalityApiError } from '../services/api';

interface PersonalitySwitcherProps {
  currentActiveId: string | null;
  onSwitch: (config: PersonalityConfig) => void;
  className?: string;
}

const PersonalitySwitcher: React.FC<PersonalitySwitcherProps> = ({
  currentActiveId,
  onSwitch,
  className = '',
}) => {
  const [configurations, setConfigurations] = useState<PersonalityConfig[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Load configurations
  useEffect(() => {
    const fetchConfigurations = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await PersonalityApi.listPersonalityConfigs(50, 0);
        setConfigurations(result.configurations);
      } catch (err) {
        console.error('Failed to fetch configurations:', err);
        setError(
          err instanceof PersonalityApiError
            ? err.message
            : 'Failed to load personality configurations'
        );
      } finally {
        setLoading(false);
      }
    };

    fetchConfigurations();
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const currentConfig = configurations.find(c => c.id === currentActiveId);
  const availableConfigs = configurations.filter(c => c.id !== currentActiveId);

  const handleSwitch = (config: PersonalityConfig) => {
    onSwitch(config);
    setIsOpen(false);
  };

  const getPersonalityTypeIcon = (type: string) => {
    switch (type) {
      case 'celebrity':
        return '⭐';
      case 'fictional':
        return '📚';
      case 'archetype':
        return '🎭';
      case 'custom':
        return '✨';
      default:
        return '❓';
    }
  };

  const getIdeTypeIcon = (ideType: string) => {
    switch (ideType.toLowerCase()) {
      case 'cursor':
        return '⚡';
      case 'claude':
        return '🤖';
      case 'windsurf':
        return '🏄';
      case 'vscode':
        return '💻';
      default:
        return '❓';
    }
  };

  if (loading) {
    return (
      <div className={`personality-switcher loading ${className}`}>
        <div className="switcher-button disabled">
          <div className="switcher-spinner"></div>
          <span>Loading...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`personality-switcher error ${className}`}>
        <div className="switcher-button disabled">
          <span>⚠️ Error</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`personality-switcher ${className}`} ref={dropdownRef}>
      <button
        className={`switcher-button ${isOpen ? 'open' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        title="Switch Active Personality"
      >
        <div className="current-personality">
          {currentConfig ? (
            <>
              <span className="personality-icon">
                {getPersonalityTypeIcon(currentConfig.profile.type)}
              </span>
              <div className="personality-info">
                <span className="personality-name">{currentConfig.profile.name}</span>
                <span className="personality-meta">
                  {getIdeTypeIcon(currentConfig.ide_type)} {currentConfig.ide_type}
                </span>
              </div>
            </>
          ) : (
            <>
              <span className="personality-icon">⏸️</span>
              <div className="personality-info">
                <span className="personality-name">No Active Personality</span>
                <span className="personality-meta">Click to select</span>
              </div>
            </>
          )}
        </div>
        <span className={`dropdown-arrow ${isOpen ? 'up' : 'down'}`}>
          {isOpen ? '▲' : '▼'}
        </span>
      </button>

      {isOpen && (
        <div className="switcher-dropdown">
          <div className="dropdown-header">
            <h4>Switch Personality</h4>
            <span className="config-count">
              {configurations.length} configuration{configurations.length !== 1 ? 's' : ''}
            </span>
          </div>

          <div className="dropdown-content">
            {currentConfig && (
              <div className="dropdown-section">
                <h5>Current Active</h5>
                <div className="personality-item current">
                  <div className="item-icon">
                    {getPersonalityTypeIcon(currentConfig.profile.type)}
                  </div>
                  <div className="item-info">
                    <span className="item-name">{currentConfig.profile.name}</span>
                    <span className="item-meta">
                      {currentConfig.profile.type} • {getIdeTypeIcon(currentConfig.ide_type)} {currentConfig.ide_type}
                    </span>
                  </div>
                  <div className="item-status active">
                    ✅ Active
                  </div>
                </div>
              </div>
            )}

            {availableConfigs.length > 0 && (
              <div className="dropdown-section">
                <h5>Available Personalities</h5>
                <div className="personality-list">
                  {availableConfigs.map((config) => (
                    <button
                      key={config.id}
                      className="personality-item clickable"
                      onClick={() => handleSwitch(config)}
                      title={`Switch to ${config.profile.name}`}
                    >
                      <div className="item-icon">
                        {getPersonalityTypeIcon(config.profile.type)}
                      </div>
                      <div className="item-info">
                        <span className="item-name">{config.profile.name}</span>
                        <span className="item-meta">
                          {config.profile.type} • {getIdeTypeIcon(config.ide_type)} {config.ide_type}
                        </span>
                      </div>
                      <div className="item-action">
                        <span className="switch-icon">🔄</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {currentConfig && (
              <div className="dropdown-section">
                <button
                  className="deactivate-button"
                  onClick={() => handleSwitch({ ...currentConfig, active: false } as PersonalityConfig)}
                  title="Deactivate current personality"
                >
                  <span className="deactivate-icon">⏸️</span>
                  <span>Deactivate Current</span>
                </button>
              </div>
            )}

            {configurations.length === 0 && (
              <div className="empty-state">
                <span className="empty-icon">📝</span>
                <p>No personality configurations found.</p>
                <p>Create one to get started!</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default PersonalitySwitcher;