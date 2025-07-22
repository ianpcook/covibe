import React, { useState, useEffect } from 'react';
import { PersonalityConfig, PersonalityRequest } from '../types/personality';
import { PersonalityApi, PersonalityApiError } from '../services/api';
import PersonalityCard from './PersonalityCard';
import PersonalityDetailView from './PersonalityDetailView';
import PersonalityEditForm from './PersonalityEditForm';
import PersonalitySwitcher from './PersonalitySwitcher';
import PersonalityExportInterface from './PersonalityExportInterface';
import BulkExportManager from './BulkExportManager';
import PersonalityImportInterface from './PersonalityImportInterface';
import './PersonalityManagementDashboard.css';
import './PersonalitySwitcher.css';

interface DashboardStats {
  total: number;
  active: number;
  byType: Record<string, number>;
  byIde: Record<string, number>;
}

const PersonalityManagementDashboard: React.FC = () => {
  const [configurations, setConfigurations] = useState<PersonalityConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedConfig, setSelectedConfig] = useState<PersonalityConfig | null>(null);
  const [editingConfig, setEditingConfig] = useState<PersonalityConfig | null>(null);
  const [exportingConfig, setExportingConfig] = useState<PersonalityConfig | null>(null);
  const [showBulkExport, setShowBulkExport] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [activeConfigId, setActiveConfigId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [sortBy, setSortBy] = useState<'name' | 'created' | 'updated' | 'type'>('updated');
  const [filterType, setFilterType] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [stats, setStats] = useState<DashboardStats>({
    total: 0,
    active: 0,
    byType: {},
    byIde: {}
  });
  
  // Real-time feedback states
  const [operationInProgress, setOperationInProgress] = useState<{
    type: 'delete' | 'toggle' | 'update' | 'export' | null;
    configId: string | null;
    message: string;
  }>({ type: null, configId: null, message: '' });
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Load configurations and calculate stats
  useEffect(() => {
    const fetchConfigurations = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await PersonalityApi.listPersonalityConfigs(100, 0); // Get all for dashboard
        setConfigurations(result.configurations);

        // Calculate stats
        const newStats: DashboardStats = {
          total: result.configurations.length,
          active: result.configurations.filter(c => c.active).length,
          byType: {},
          byIde: {}
        };

        result.configurations.forEach(config => {
          // Count by type
          newStats.byType[config.profile.type] = (newStats.byType[config.profile.type] || 0) + 1;
          // Count by IDE
          newStats.byIde[config.ide_type] = (newStats.byIde[config.ide_type] || 0) + 1;
        });

        setStats(newStats);

        // Set active configuration from localStorage
        const savedActiveId = localStorage.getItem('activePersonalityId');
        if (savedActiveId && result.configurations.find(c => c.id === savedActiveId)) {
          setActiveConfigId(savedActiveId);
        }
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

  // Filter and sort configurations
  const filteredAndSortedConfigs = React.useMemo(() => {
    let filtered = configurations;

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(config =>
        config.profile.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        config.profile.type.toLowerCase().includes(searchQuery.toLowerCase()) ||
        config.ide_type.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Apply type filter
    if (filterType !== 'all') {
      filtered = filtered.filter(config => config.profile.type === filterType);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.profile.name.localeCompare(b.profile.name);
        case 'created':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case 'updated':
          return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
        case 'type':
          return a.profile.type.localeCompare(b.profile.type);
        default:
          return 0;
      }
    });

    return filtered;
  }, [configurations, searchQuery, filterType, sortBy]);

  const handleViewDetails = (config: PersonalityConfig) => {
    setSelectedConfig(config);
  };

  const handleEdit = (config: PersonalityConfig) => {
    setEditingConfig(config);
    setSelectedConfig(null);
  };

  const handleDelete = async (config: PersonalityConfig) => {
    if (!window.confirm(`Are you sure you want to delete "${config.profile.name}"? This action cannot be undone.`)) {
      return;
    }

    try {
      setError(null);
      setSuccessMessage(null);
      setOperationInProgress({
        type: 'delete',
        configId: config.id,
        message: `Deleting "${config.profile.name}"...`
      });

      await PersonalityApi.deletePersonalityConfig(config.id);
      
      // Remove from local state
      setConfigurations(prev => prev.filter(c => c.id !== config.id));
      
      // Clear active if this was the active config
      if (activeConfigId === config.id) {
        setActiveConfigId(null);
        localStorage.removeItem('activePersonalityId');
      }
      
      // Close detail view if this config was selected
      if (selectedConfig?.id === config.id) {
        setSelectedConfig(null);
      }

      setSuccessMessage(`Successfully deleted "${config.profile.name}"`);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      console.error('Failed to delete configuration:', err);
      setError(
        err instanceof PersonalityApiError
          ? err.message
          : 'Failed to delete personality configuration'
      );
    } finally {
      setOperationInProgress({ type: null, configId: null, message: '' });
    }
  };

  const handleToggleActive = async (config: PersonalityConfig) => {
    try {
      setError(null);
      setSuccessMessage(null);
      
      const isActivating = !config.active && activeConfigId !== config.id;
      setOperationInProgress({
        type: 'toggle',
        configId: config.id,
        message: isActivating 
          ? `Activating "${config.profile.name}"...` 
          : `Deactivating "${config.profile.name}"...`
      });

      // Simulate API delay for better UX feedback
      await new Promise(resolve => setTimeout(resolve, 500));
      
      if (config.active || activeConfigId === config.id) {
        // Deactivate
        setActiveConfigId(null);
        localStorage.removeItem('activePersonalityId');
        setSuccessMessage(`Deactivated "${config.profile.name}"`);
      } else {
        // Activate (deactivate others first)
        setActiveConfigId(config.id);
        localStorage.setItem('activePersonalityId', config.id);
        setSuccessMessage(`Activated "${config.profile.name}"`);
      }
      
      // Update local state
      setConfigurations(prev => 
        prev.map(c => ({
          ...c,
          active: c.id === config.id ? !c.active : (c.id === activeConfigId ? false : c.active)
        }))
      );

      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      console.error('Failed to toggle configuration:', err);
      setError('Failed to update configuration status');
    } finally {
      setOperationInProgress({ type: null, configId: null, message: '' });
    }
  };

  const handleUpdateConfig = async (updatedData: Partial<PersonalityRequest>) => {
    if (!editingConfig) return;

    try {
      setError(null);
      const updatedConfig = await PersonalityApi.updatePersonalityConfig(editingConfig.id, updatedData);
      
      // Update local state
      setConfigurations(prev => 
        prev.map(c => c.id === editingConfig.id ? updatedConfig : c)
      );
      
      setEditingConfig(null);
    } catch (err) {
      console.error('Failed to update configuration:', err);
      setError(
        err instanceof PersonalityApiError
          ? err.message
          : 'Failed to update personality configuration'
      );
    }
  };

  const handleExport = (config: PersonalityConfig) => {
    setExportingConfig(config);
  };

  const handleExportComplete = (success: boolean, fileName?: string) => {
    if (success) {
      setSuccessMessage(fileName ? `Successfully exported "${fileName}"` : 'Configuration exported successfully');
      setTimeout(() => setSuccessMessage(null), 3000);
    }
    setExportingConfig(null);
  };

  const handleExportError = (error: string) => {
    setError(`Export failed: ${error}`);
    setExportingConfig(null);
  };

  const handleCancelExport = () => {
    setExportingConfig(null);
  };

  const handleBulkExport = () => {
    setShowBulkExport(true);
  };

  const handleBulkExportComplete = (success: boolean, fileName?: string) => {
    if (success) {
      setSuccessMessage(fileName ? `Successfully exported "${fileName}"` : 'Bulk export completed successfully');
      setTimeout(() => setSuccessMessage(null), 3000);
    }
    setShowBulkExport(false);
  };

  const handleBulkExportError = (error: string) => {
    setError(`Bulk export failed: ${error}`);
    setShowBulkExport(false);
  };

  const handleCloseBulkExport = () => {
    setShowBulkExport(false);
  };

  const handleImport = () => {
    setShowImport(true);
  };

  const handleImportComplete = (importedConfig: PersonalityConfig) => {
    setSuccessMessage(`Successfully imported "${importedConfig.profile.name}"`);
    setTimeout(() => setSuccessMessage(null), 3000);
    
    // Refresh the configurations list
    const fetchConfigurations = async () => {
      try {
        const result = await PersonalityApi.listPersonalityConfigs(100, 0);
        setConfigurations(result.configurations);
        calculateStats(result.configurations);
      } catch (error) {
        console.error('Failed to refresh configurations:', error);
      }
    };
    fetchConfigurations();
    
    setShowImport(false);
  };

  const handleImportError = (error: string) => {
    setError(`Import failed: ${error}`);
  };

  const handleCloseImport = () => {
    setShowImport(false);
  };

  const handleCancelEdit = () => {
    setEditingConfig(null);
  };

  const handleCloseDetail = () => {
    setSelectedConfig(null);
  };

  if (editingConfig) {
    return (
      <div className="personality-management-dashboard">
        <PersonalityEditForm
          config={editingConfig}
          onSave={handleUpdateConfig}
          onCancel={handleCancelEdit}
        />
      </div>
    );
  }

  return (
    <div className="personality-management-dashboard">
      <div className="dashboard-header">
        <div className="header-title">
          <h1>Personality Management Dashboard</h1>
          <p>Manage and configure your AI agent personalities</p>
        </div>
        
        <div className="dashboard-stats">
          <div className="stat-card">
            <div className="stat-number">{stats.total}</div>
            <div className="stat-label">Total Personalities</div>
          </div>
          <div className="stat-card active">
            <div className="stat-number">{stats.active}</div>
            <div className="stat-label">Active</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{Object.keys(stats.byType).length}</div>
            <div className="stat-label">Types</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{Object.keys(stats.byIde).length}</div>
            <div className="stat-label">IDEs</div>
          </div>
        </div>
      </div>

      {/* Quick Personality Switcher */}
      {configurations.length > 0 && (
        <div className="quick-switcher-section">
          <div className="switcher-header">
            <h3>Quick Switch</h3>
            <p>Instantly activate a different personality</p>
          </div>
          <PersonalitySwitcher
            currentActiveId={activeConfigId}
            onSwitch={handleToggleActive}
            className="dashboard-switcher"
          />
        </div>
      )}

      <div className="dashboard-controls">
        <div className="search-and-filter">
          <div className="search-box">
            <input
              type="text"
              placeholder="Search personalities..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
            <span className="search-icon">🔍</span>
          </div>
          
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Types</option>
            {Object.keys(stats.byType).map(type => (
              <option key={type} value={type}>
                {type} ({stats.byType[type]})
              </option>
            ))}
          </select>
          
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="sort-select"
          >
            <option value="updated">Recently Updated</option>
            <option value="created">Recently Created</option>
            <option value="name">Name A-Z</option>
            <option value="type">Type</option>
          </select>
        </div>
        
        <div className="view-controls">
          <button
            onClick={handleImport}
            className="import-button"
            title="Import Configuration"
          >
            📥 Import
          </button>
          <button
            onClick={handleBulkExport}
            className="bulk-export-button"
            title="Bulk Export"
            disabled={configurations.length === 0}
          >
            📦 Bulk Export
          </button>
          <button
            onClick={() => setViewMode('grid')}
            className={`view-button ${viewMode === 'grid' ? 'active' : ''}`}
            title="Grid View"
          >
            ⊞
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`view-button ${viewMode === 'list' ? 'active' : ''}`}
            title="List View"
          >
            ☰
          </button>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}
      {successMessage && <div className="success-message">{successMessage}</div>}
      {operationInProgress.type && (
        <div className="operation-progress">
          <div className="progress-indicator">
            <div className="progress-spinner"></div>
            <span>{operationInProgress.message}</span>
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading-indicator">Loading configurations...</div>
      ) : filteredAndSortedConfigs.length === 0 ? (
        <div className="empty-state">
          <h2>No Personalities Found</h2>
          <p>
            {searchQuery || filterType !== 'all' 
              ? 'No personalities match your current filters.' 
              : 'You haven\'t created any personality configurations yet.'
            }
          </p>
          {(searchQuery || filterType !== 'all') && (
            <button
              onClick={() => {
                setSearchQuery('');
                setFilterType('all');
              }}
              className="clear-filters-button"
            >
              Clear Filters
            </button>
          )}
        </div>
      ) : (
        <div className={`configurations-container ${viewMode}`}>
          {filteredAndSortedConfigs.map((config) => (
            <PersonalityCard
              key={config.id}
              config={config}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onView={handleViewDetails}
              onToggleActive={handleToggleActive}
              onExport={handleExport}
              showDetailedStatus={true}
              operationInProgress={operationInProgress}
            />
          ))}
        </div>
      )}

      {selectedConfig && (
        <PersonalityDetailView
          config={selectedConfig}
          onClose={handleCloseDetail}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onToggleActive={handleToggleActive}
          onExport={handleExport}
          operationInProgress={operationInProgress}
        />
      )}

      {exportingConfig && (
        <div className="modal-backdrop">
          <div className="export-modal">
            <div className="modal-header">
              <h3>Export Configuration</h3>
              <button onClick={handleCancelExport} className="close-button">
                ×
              </button>
            </div>
            <div className="modal-body">
              <PersonalityExportInterface
                personalityConfig={exportingConfig}
                onExportComplete={handleExportComplete}
                onError={handleExportError}
              />
            </div>
          </div>
        </div>
      )}

      {showBulkExport && (
        <div className="modal-backdrop">
          <div className="bulk-export-modal">
            <div className="modal-header">
              <h3>Bulk Export</h3>
              <button onClick={handleCloseBulkExport} className="close-button">
                ×
              </button>
            </div>
            <div className="modal-body">
              <BulkExportManager
                availableConfigs={configurations}
                onClose={handleCloseBulkExport}
                onExportComplete={handleBulkExportComplete}
                onError={handleBulkExportError}
              />
            </div>
          </div>
        </div>
      )}

      {showImport && (
        <div className="modal-backdrop">
          <div className="import-modal">
            <div className="modal-header">
              <h3>Import Configuration</h3>
              <button onClick={handleCloseImport} className="close-button">
                ×
              </button>
            </div>
            <div className="modal-body">
              <PersonalityImportInterface
                onImportComplete={handleImportComplete}
                onError={handleImportError}
                onClose={handleCloseImport}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PersonalityManagementDashboard;