/**
 * Personality configuration card component
 */

import React from 'react';
import { PersonalityConfig } from '../types/personality';

interface PersonalityCardProps {
  config: PersonalityConfig;
  onEdit?: (config: PersonalityConfig) => void;
  onDelete?: (config: PersonalityConfig) => void;
  onView?: (config: PersonalityConfig) => void;
  onToggleActive?: (config: PersonalityConfig) => void;
  onExport?: (config: PersonalityConfig) => void;
  showDetailedStatus?: boolean;
  operationInProgress?: {
    type: 'delete' | 'toggle' | 'update' | 'export' | null;
    configId: string | null;
    message: string;
  };
}

const PersonalityCard: React.FC<PersonalityCardProps> = ({
  config,
  onEdit,
  onDelete,
  onView,
  onToggleActive,
  onExport,
  showDetailedStatus = false,
  operationInProgress,
}) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
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

  const isOperationInProgress = operationInProgress?.configId === config.id;
  const isDisabled = isOperationInProgress || (operationInProgress?.type === 'toggle' && operationInProgress?.configId !== config.id);

  return (
    <div className={`personality-card ${config.active ? 'active' : 'inactive'} ${isOperationInProgress ? 'operation-in-progress' : ''}`}>
      {isOperationInProgress && (
        <div className="card-operation-overlay">
          <div className="operation-indicator">
            <div className="operation-spinner"></div>
            <span className="operation-message">{operationInProgress?.message}</span>
          </div>
        </div>
      )}
      
      <div className="card-header">
        <div className="personality-info">
          <h3 className="personality-name">{config.profile.name}</h3>
          <span className={`personality-type ${getPersonalityTypeColor(config.profile.type)}`}>
            {config.profile.type}
          </span>
        </div>
        <div className="card-actions">
          {onToggleActive && (
            <button
              onClick={() => onToggleActive(config)}
              className={`btn btn-sm ${config.active ? 'btn-warning' : 'btn-success'}`}
              title={config.active ? 'Deactivate' : 'Activate'}
              disabled={isDisabled}
            >
              {isOperationInProgress && operationInProgress?.type === 'toggle' ? (
                <div className="btn-spinner"></div>
              ) : (
                config.active ? '⏸️' : '▶️'
              )}
            </button>
          )}
          {onView && (
            <button
              onClick={() => onView(config)}
              className="btn btn-sm btn-secondary"
              title="View Details"
              disabled={isDisabled}
            >
              👁️
            </button>
          )}
          {onEdit && (
            <button
              onClick={() => onEdit(config)}
              className="btn btn-sm btn-secondary"
              title="Edit"
              disabled={isDisabled}
            >
              ✏️
            </button>
          )}
          {onExport && (
            <button
              onClick={() => onExport(config)}
              className="btn btn-sm btn-info"
              title="Export Configuration"
              disabled={isDisabled}
            >
              {isOperationInProgress && operationInProgress?.type === 'export' ? (
                <div className="btn-spinner"></div>
              ) : (
                '📤'
              )}
            </button>
          )}
          {onDelete && (
            <button
              onClick={() => onDelete(config)}
              className={`btn btn-sm btn-danger ${isOperationInProgress && operationInProgress?.type === 'delete' ? 'deleting' : ''}`}
              title="Delete"
              disabled={isDisabled}
            >
              {isOperationInProgress && operationInProgress?.type === 'delete' ? (
                <div className="btn-spinner"></div>
              ) : (
                '🗑️'
              )}
            </button>
          )}
        </div>
      </div>

      <div className="card-body">
        <div className="personality-details">
          <div className="communication-style">
            <strong>Style:</strong> {config.profile.communication_style.tone} • {' '}
            {config.profile.communication_style.formality} • {' '}
            {config.profile.communication_style.verbosity}
          </div>
          
          {config.profile.traits.length > 0 && (
            <div className="traits">
              <strong>Key Traits:</strong>
              <div className="trait-list">
                {config.profile.traits.slice(0, 3).map((trait, index) => (
                  <span key={index} className="trait-tag">
                    {trait.trait} ({trait.intensity}/10)
                  </span>
                ))}
                {config.profile.traits.length > 3 && (
                  <span className="trait-more">
                    +{config.profile.traits.length - 3} more
                  </span>
                )}
              </div>
            </div>
          )}

          {config.profile.mannerisms.length > 0 && (
            <div className="mannerisms">
              <strong>Mannerisms:</strong>
              <div className="mannerism-list">
                {config.profile.mannerisms.slice(0, 2).map((mannerism, index) => (
                  <span key={index} className="mannerism-tag">
                    {mannerism}
                  </span>
                ))}
                {config.profile.mannerisms.length > 2 && (
                  <span className="mannerism-more">
                    +{config.profile.mannerisms.length - 2} more
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="card-footer">
        <div className="ide-info">
          <span className="ide-indicator">
            {getIdeTypeIcon(config.ide_type)} {config.ide_type}
          </span>
          <span className={`status ${config.active ? 'active' : 'inactive'}`}>
            {config.active ? '✅ Active' : '⏸️ Inactive'}
          </span>
        </div>
        <div className="timestamps">
          <small>
            Created: {formatDate(config.created_at)}
            {config.updated_at !== config.created_at && (
              <> • Updated: {formatDate(config.updated_at)}</>
            )}
          </small>
        </div>
      </div>
    </div>
  );
};

export default PersonalityCard;