/**
 * Configurations page for managing personality configurations
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import PersonalityCard from '../components/PersonalityCard';
import PersonalityDetailView from '../components/PersonalityDetailView';
import PersonalityEditForm from '../components/PersonalityEditForm';
import { PersonalityConfig, PersonalityRequest } from '../types/personality';
import { PersonalityApi, PersonalityApiError } from '../services/api';

const ConfigurationsPage: React.FC = () => {
  const [configurations, setConfigurations] = useState<PersonalityConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    total: 0,
    limit: 10,
    offset: 0,
    has_more: false,
  });
  
  // Modal states
  const [selectedConfig, setSelectedConfig] = useState<PersonalityConfig | null>(null);
  const [showDetailView, setShowDetailView] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  
  const navigate = useNavigate();

  const loadConfigurations = async (offset: number = 0) => {
    setLoading(true);
    setError(null);

    try {
      const response = await PersonalityApi.listPersonalityConfigs(10, offset);
      setConfigurations(response.configurations);
      setPagination(response.pagination);
    } catch (err) {
      if (err instanceof PersonalityApiError) {
        setError(err.apiError.error.message);
      } else {
        setError('Failed to load configurations. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfigurations();
  }, []);

  const handleDelete = async (config: PersonalityConfig) => {
    if (!window.confirm(`Are you sure you want to delete "${config.profile.name}"?`)) {
      return;
    }

    setActionLoading(`delete-${config.id}`);
    try {
      await PersonalityApi.deletePersonalityConfig(config.id);
      // Close modals if the deleted config was selected
      if (selectedConfig?.id === config.id) {
        setSelectedConfig(null);
        setShowDetailView(false);
        setShowEditForm(false);
      }
      // Reload configurations
      await loadConfigurations(pagination.offset);
    } catch (err) {
      if (err instanceof PersonalityApiError) {
        setError(err.apiError.error.message);
      } else {
        setError('Failed to delete configuration. Please try again.');
      }
    } finally {
      setActionLoading(null);
    }
  };

  const handleEdit = (config: PersonalityConfig) => {
    setSelectedConfig(config);
    setShowEditForm(true);
    setShowDetailView(false);
  };

  const handleView = (config: PersonalityConfig) => {
    setSelectedConfig(config);
    setShowDetailView(true);
    setShowEditForm(false);
  };

  const handleToggleActive = async (config: PersonalityConfig) => {
    setActionLoading(`toggle-${config.id}`);
    try {
      // For now, we'll just update the local state since we don't have a toggle endpoint
      // In a real implementation, this would call an API endpoint
      const updatedConfigs = configurations.map(c => 
        c.id === config.id ? { ...c, active: !c.active } : c
      );
      setConfigurations(updatedConfigs);
      
      // Update selected config if it's the one being toggled
      if (selectedConfig?.id === config.id) {
        setSelectedConfig({ ...selectedConfig, active: !selectedConfig.active });
      }
    } catch (err) {
      if (err instanceof PersonalityApiError) {
        setError(err.apiError.error.message);
      } else {
        setError('Failed to toggle configuration status. Please try again.');
      }
    } finally {
      setActionLoading(null);
    }
  };

  const handleSaveEdit = async (updates: Partial<PersonalityRequest>) => {
    if (!selectedConfig) return;

    setActionLoading(`edit-${selectedConfig.id}`);
    try {
      const updatedConfig = await PersonalityApi.updatePersonalityConfig(selectedConfig.id, updates);
      
      // Update the configurations list
      const updatedConfigs = configurations.map(c => 
        c.id === selectedConfig.id ? updatedConfig : c
      );
      setConfigurations(updatedConfigs);
      
      // Update selected config
      setSelectedConfig(updatedConfig);
      
      // Close edit form and show detail view
      setShowEditForm(false);
      setShowDetailView(true);
    } catch (err) {
      if (err instanceof PersonalityApiError) {
        setError(err.apiError.error.message);
      } else {
        setError('Failed to update configuration. Please try again.');
      }
      throw err; // Re-throw to let the form handle it
    } finally {
      setActionLoading(null);
    }
  };

  const handleCloseModals = () => {
    setSelectedConfig(null);
    setShowDetailView(false);
    setShowEditForm(false);
  };

  const handlePrevPage = () => {
    if (pagination.offset > 0) {
      const newOffset = Math.max(0, pagination.offset - pagination.limit);
      loadConfigurations(newOffset);
    }
  };

  const handleNextPage = () => {
    if (pagination.has_more) {
      const newOffset = pagination.offset + pagination.limit;
      loadConfigurations(newOffset);
    }
  };

  if (loading && configurations.length === 0) {
    return (
      <div className="configurations-page">
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>Loading configurations...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="configurations-page">
      <div className="page-header">
        <h1>Personality Configurations</h1>
        <button
          onClick={() => navigate('/')}
          className="btn btn-primary"
        >
          Create New
        </button>
      </div>

      {error && (
        <div className="alert alert-error">
          <strong>Error:</strong> {error}
          <button
            onClick={() => loadConfigurations(pagination.offset)}
            className="btn btn-sm btn-secondary"
            style={{ marginLeft: '1rem' }}
          >
            Retry
          </button>
        </div>
      )}

      {configurations.length === 0 && !loading ? (
        <div className="empty-state">
          <div className="empty-icon">🎭</div>
          <h3>No Personalities Yet</h3>
          <p>Create your first personality configuration to get started.</p>
          <button
            onClick={() => navigate('/')}
            className="btn btn-primary"
          >
            Create Personality
          </button>
        </div>
      ) : (
        <>
          <div className="configurations-grid">
            {configurations.map((config) => (
              <PersonalityCard
                key={config.id}
                config={config}
                onEdit={handleEdit}
                onDelete={handleDelete}
                onView={handleView}
                onToggleActive={handleToggleActive}
                showDetailedStatus={true}
              />
            ))}
          </div>

          {pagination.total > pagination.limit && (
            <div className="pagination">
              <button
                onClick={handlePrevPage}
                disabled={pagination.offset === 0}
                className="btn btn-secondary"
              >
                Previous
              </button>
              <span className="pagination-info">
                Showing {pagination.offset + 1} - {Math.min(pagination.offset + pagination.limit, pagination.total)} of {pagination.total}
              </span>
              <button
                onClick={handleNextPage}
                disabled={!pagination.has_more}
                className="btn btn-secondary"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}

      {/* Detail View Modal */}
      {showDetailView && selectedConfig && (
        <PersonalityDetailView
          config={selectedConfig}
          onClose={handleCloseModals}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onToggleActive={handleToggleActive}
        />
      )}

      {/* Edit Form Modal */}
      {showEditForm && selectedConfig && (
        <PersonalityEditForm
          config={selectedConfig}
          onSave={handleSaveEdit}
          onCancel={handleCloseModals}
          loading={actionLoading === `edit-${selectedConfig.id}`}
        />
      )}
    </div>
  );
};

export default ConfigurationsPage;