/**
 * Detailed view component for personality configurations
 */

import React, { useState } from 'react';
import { PersonalityConfig } from '../types/personality';

interface PersonalityDetailViewProps {
  config: PersonalityConfig;
  onClose: () => void;
  onEdit: (config: PersonalityConfig) => void;
  onDelete: (config: PersonalityConfig) => void;
  onToggleActive: (config: PersonalityConfig) => void;
}

const PersonalityDetailView: React.FC<PersonalityDetailViewProps> = ({
  config,
  onClose,
  onEdit,
  onDelete,
  onToggleActive,
}) => {
  const [showFullContext, setShowFullContext] = useState(false);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const getPersonalityTypeColor = (type: string) => {
    switch (type) {
      case 'celebrity':
        return 'type-celebrity';
      case 'fictional':
        return 'type-fictional';
      case 'archetype':
        return 'type-archetype';
      case 'custom':
        return 'type-custom';
      default:
        return 'type-default';
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

  const handleDelete = () => {
    if (window.confirm(`Are you sure you want to delete "${config.profile.name}"?`)) {
      onDelete(config);
    }
  };

  return (
    <div className="personality-detail-overlay">
      <div className="personality-detail-modal">
        <div className="detail-header">
          <div className="detail-title">
            <h2>{config.profile.name}</h2>
            <span className={`personality-type ${getPersonalityTypeColor(config.profile.type)}`}>
              {config.profile.type}
            </span>
          </div>
          <div className="detail-actions">
            <button
              onClick={() => onToggleActive(config)}
              className={`btn btn-sm ${config.active ? 'btn-warning' : 'btn-success'}`}
              title={config.active ? 'Deactivate' : 'Activate'}
            >
              {config.active ? '⏸️ Deactivate' : '▶️ Activate'}
            </button>
            <button
              onClick={() => onEdit(config)}
              className="btn btn-sm btn-secondary"
              title="Edit Configuration"
            >
              ✏️ Edit
            </button>
            <button
              onClick={handleDelete}
              className="btn btn-sm btn-danger"
              title="Delete Configuration"
            >
              🗑️ Delete
            </button>
            <button
              onClick={onClose}
              className="btn btn-sm btn-secondary"
              title="Close"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="detail-content">
          <div className="detail-section">
            <h3>Communication Style</h3>
            <div className="communication-details">
              <div className="style-item">
                <strong>Tone:</strong> {config.profile.communication_style.tone}
              </div>
              <div className="style-item">
                <strong>Formality:</strong> {config.profile.communication_style.formality}
              </div>
              <div className="style-item">
                <strong>Verbosity:</strong> {config.profile.communication_style.verbosity}
              </div>
              <div className="style-item">
                <strong>Technical Level:</strong> {config.profile.communication_style.technical_level}
              </div>
            </div>
          </div>

          {config.profile.traits.length > 0 && (
            <div className="detail-section">
              <h3>Personality Traits</h3>
              <div className="traits-grid">
                {config.profile.traits.map((trait, index) => (
                  <div key={index} className="trait-detail">
                    <div className="trait-header">
                      <span className="trait-name">{trait.trait}</span>
                      <span className="trait-intensity">{trait.intensity}/10</span>
                    </div>
                    <div className="trait-category">{trait.category}</div>
                    {trait.examples.length > 0 && (
                      <div className="trait-examples">
                        {trait.examples.map((example, idx) => (
                          <span key={idx} className="example-tag">{example}</span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {config.profile.mannerisms.length > 0 && (
            <div className="detail-section">
              <h3>Behavioral Mannerisms</h3>
              <div className="mannerisms-list">
                {config.profile.mannerisms.map((mannerism, index) => (
                  <div key={index} className="mannerism-item">
                    • {mannerism}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="detail-section">
            <h3>IDE Integration</h3>
            <div className="ide-integration-details">
              <div className="ide-status">
                <div className="ide-info">
                  <span className="ide-icon">{getIdeTypeIcon(config.ide_type)}</span>
                  <span className="ide-name">{config.ide_type}</span>
                  <span className={`status-badge ${config.active ? 'active' : 'inactive'}`}>
                    {config.active ? '✅ Active' : '⏸️ Inactive'}
                  </span>
                </div>
                {config.file_path && (
                  <div className="file-path">
                    <strong>Config File:</strong> {config.file_path}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="detail-section">
            <h3>Generated Context</h3>
            <div className="context-section">
              <div className="context-preview">
                {showFullContext ? (
                  <pre className="context-full">{config.context}</pre>
                ) : (
                  <div className="context-summary">
                    {config.context.substring(0, 200)}...
                  </div>
                )}
              </div>
              <button
                onClick={() => setShowFullContext(!showFullContext)}
                className="btn btn-sm btn-secondary"
              >
                {showFullContext ? 'Show Less' : 'Show Full Context'}
              </button>
            </div>
          </div>

          <div className="detail-section">
            <h3>Configuration Details</h3>
            <div className="config-metadata">
              <div className="metadata-item">
                <strong>ID:</strong> {config.id}
              </div>
              <div className="metadata-item">
                <strong>Created:</strong> {formatDate(config.created_at)}
              </div>
              <div className="metadata-item">
                <strong>Last Updated:</strong> {formatDate(config.updated_at)}
              </div>
              {config.profile.sources.length > 0 && (
                <div className="metadata-item">
                  <strong>Research Sources:</strong>
                  <div className="sources-list">
                    {config.profile.sources.map((source, index) => (
                      <div key={index} className="source-item">
                        <span className="source-type">{source.type}</span>
                        <span className="source-confidence">
                          {Math.round(source.confidence * 100)}% confidence
                        </span>
                        {source.url && (
                          <a href={source.url} target="_blank" rel="noopener noreferrer" className="source-link">
                            🔗
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PersonalityDetailView;