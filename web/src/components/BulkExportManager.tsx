/**
 * Bulk export manager component
 */

import React, { useState, useEffect } from 'react';
import { 
  PersonalityConfig, 
  BulkExportRequest,
  SupportedIDEType,
  ExportFormatOptions 
} from '../types/personality';
import PersonalityApi from '../services/api';

interface BulkExportManagerProps {
  availableConfigs: PersonalityConfig[];
  onClose: () => void;
  onExportComplete?: (success: boolean, fileName?: string) => void;
  onError?: (error: string) => void;
}

const BulkExportManager: React.FC<BulkExportManagerProps> = ({
  availableConfigs,
  onClose,
  onExportComplete,
  onError,
}) => {
  const [selectedConfigs, setSelectedConfigs] = useState<Set<string>>(new Set());
  const [selectedIDETypes, setSelectedIDETypes] = useState<SupportedIDEType[]>(['cursor']);
  const [formatOptions, setFormatOptions] = useState<ExportFormatOptions>({
    include_metadata: true,
    include_instructions: true,
    preserve_comments: true,
  });
  const [includeReadme, setIncludeReadme] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState({ progress: 0, message: '' });

  const ideTypes: Array<{ type: SupportedIDEType; name: string; description: string }> = [
    { type: 'cursor', name: 'Cursor', description: 'AI-powered code editor' },
    { type: 'claude', name: 'Claude', description: 'Claude AI assistant' },
    { type: 'windsurf', name: 'Windsurf', description: 'Next-gen IDE' },
    { type: 'generic', name: 'Generic', description: 'Universal format' },
  ];

  const handleConfigToggle = (configId: string) => {
    const newSelected = new Set(selectedConfigs);
    if (newSelected.has(configId)) {
      newSelected.delete(configId);
    } else {
      newSelected.add(configId);
    }
    setSelectedConfigs(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedConfigs.size === availableConfigs.length) {
      setSelectedConfigs(new Set());
    } else {
      setSelectedConfigs(new Set(availableConfigs.map(c => c.id)));
    }
  };

  const handleIDETypeToggle = (ideType: SupportedIDEType) => {
    if (selectedIDETypes.includes(ideType)) {
      setSelectedIDETypes(selectedIDETypes.filter(t => t !== ideType));
    } else {
      setSelectedIDETypes([...selectedIDETypes, ideType]);
    }
  };

  const handleBulkExport = async () => {
    if (selectedConfigs.size === 0) {
      onError?.('Please select at least one configuration to export');
      return;
    }

    if (selectedIDETypes.length === 0) {
      onError?.('Please select at least one IDE type');
      return;
    }

    setIsExporting(true);
    setExportProgress({ progress: 10, message: 'Preparing bulk export...' });

    try {
      const bulkRequest: BulkExportRequest = {
        personality_ids: Array.from(selectedConfigs),
        ide_types: selectedIDETypes,
        format_options: formatOptions,
        include_readme: includeReadme,
      };

      setExportProgress({ progress: 50, message: 'Generating export files...' });

      const blob = await PersonalityApi.bulkExportPersonalities(bulkRequest);

      setExportProgress({ progress: 90, message: 'Creating download...' });

      // Create download
      const url = window.URL.createObjectURL(blob);
      const fileName = `covibe-personalities-export-${new Date().toISOString().split('T')[0]}.zip`;
      
      const link = document.createElement('a');
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setExportProgress({ progress: 100, message: 'Export completed!' });
      onExportComplete?.(true, fileName);

      setTimeout(() => {
        onClose();
      }, 1500);

    } catch (error: any) {
      console.error('Bulk export failed:', error);
      const errorMessage = error.message || 'Bulk export failed unexpectedly';
      onError?.(errorMessage);
      setIsExporting(false);
      setExportProgress({ progress: 0, message: '' });
    }
  };

  const filteredConfigs = availableConfigs.filter(config => 
    config.profile.name.toLowerCase().includes('')
  );

  return (
    <div className="bulk-export-manager">
      <div className="manager-header">
        <h3>Bulk Export Manager</h3>
        <p>Export multiple personality configurations at once</p>
      </div>

      <div className="manager-content">
        {/* Configuration Selection */}
        <div className="section">
          <div className="section-header">
            <h4>Select Configurations ({selectedConfigs.size}/{availableConfigs.length})</h4>
            <button
              onClick={handleSelectAll}
              className="btn btn-sm btn-secondary"
              disabled={isExporting}
            >
              {selectedConfigs.size === availableConfigs.length ? 'Deselect All' : 'Select All'}
            </button>
          </div>
          
          <div className="config-list">
            {filteredConfigs.map((config) => (
              <div key={config.id} className="config-item">
                <label className="config-checkbox">
                  <input
                    type="checkbox"
                    checked={selectedConfigs.has(config.id)}
                    onChange={() => handleConfigToggle(config.id)}
                    disabled={isExporting}
                  />
                  <div className="config-info">
                    <span className="config-name">{config.profile.name}</span>
                    <span className="config-meta">
                      {config.profile.type} • {config.ide_type} • {config.active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </label>
              </div>
            ))}
          </div>
        </div>

        {/* IDE Type Selection */}
        <div className="section">
          <h4>Target IDE Types ({selectedIDETypes.length}/4)</h4>
          <div className="ide-grid">
            {ideTypes.map((ide) => (
              <label key={ide.type} className="ide-option">
                <input
                  type="checkbox"
                  checked={selectedIDETypes.includes(ide.type)}
                  onChange={() => handleIDETypeToggle(ide.type)}
                  disabled={isExporting}
                />
                <div className="ide-info">
                  <strong>{ide.name}</strong>
                  <small>{ide.description}</small>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Export Options */}
        <div className="section">
          <h4>Export Options</h4>
          <div className="options-grid">
            <label className="option-item">
              <input
                type="checkbox"
                checked={formatOptions.include_metadata || false}
                onChange={(e) => setFormatOptions(prev => ({
                  ...prev,
                  include_metadata: e.target.checked
                }))}
                disabled={isExporting}
              />
              Include metadata
            </label>
            
            <label className="option-item">
              <input
                type="checkbox"
                checked={formatOptions.include_instructions || false}
                onChange={(e) => setFormatOptions(prev => ({
                  ...prev,
                  include_instructions: e.target.checked
                }))}
                disabled={isExporting}
              />
              Include setup instructions
            </label>
            
            <label className="option-item">
              <input
                type="checkbox"
                checked={formatOptions.preserve_comments || false}
                onChange={(e) => setFormatOptions(prev => ({
                  ...prev,
                  preserve_comments: e.target.checked
                }))}
                disabled={isExporting}
              />
              Preserve comments
            </label>
            
            <label className="option-item">
              <input
                type="checkbox"
                checked={includeReadme}
                onChange={(e) => setIncludeReadme(e.target.checked)}
                disabled={isExporting}
              />
              Include README
            </label>
          </div>
        </div>

        {/* Progress Display */}
        {isExporting && (
          <div className="progress-section">
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${exportProgress.progress}%` }}
              ></div>
            </div>
            <p className="progress-message">{exportProgress.message}</p>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="manager-footer">
        <div className="export-summary">
          {selectedConfigs.size > 0 && selectedIDETypes.length > 0 && (
            <p>
              Ready to export {selectedConfigs.size} configuration(s) 
              for {selectedIDETypes.length} IDE type(s)
            </p>
          )}
        </div>
        
        <div className="action-buttons">
          <button
            onClick={onClose}
            className="btn btn-secondary"
            disabled={isExporting}
          >
            Cancel
          </button>
          
          <button
            onClick={handleBulkExport}
            className="btn btn-primary"
            disabled={isExporting || selectedConfigs.size === 0 || selectedIDETypes.length === 0}
          >
            {isExporting ? 'Exporting...' : 'Export & Download'}
          </button>
        </div>
      </div>

      <style jsx>{`
        .bulk-export-manager {
          max-width: 800px;
          margin: 0 auto;
        }

        .manager-header {
          text-align: center;
          padding: 20px;
          border-bottom: 1px solid #eee;
        }

        .manager-header h3 {
          margin: 0 0 10px 0;
          color: #333;
        }

        .manager-header p {
          margin: 0;
          color: #666;
        }

        .manager-content {
          padding: 20px;
          max-height: 60vh;
          overflow-y: auto;
        }

        .section {
          margin-bottom: 30px;
        }

        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 15px;
        }

        .section h4 {
          margin: 0 0 15px 0;
          color: #333;
          font-size: 16px;
        }

        .config-list {
          max-height: 200px;
          overflow-y: auto;
          border: 1px solid #ddd;
          border-radius: 4px;
        }

        .config-item {
          border-bottom: 1px solid #f0f0f0;
        }

        .config-item:last-child {
          border-bottom: none;
        }

        .config-checkbox {
          display: flex;
          align-items: center;
          padding: 12px;
          cursor: pointer;
          transition: background-color 0.2s ease;
        }

        .config-checkbox:hover {
          background-color: #f8f9fa;
        }

        .config-checkbox input[type="checkbox"] {
          margin-right: 12px;
          width: 16px;
          height: 16px;
        }

        .config-info {
          flex: 1;
        }

        .config-name {
          display: block;
          font-weight: 500;
          color: #333;
        }

        .config-meta {
          display: block;
          font-size: 12px;
          color: #666;
          margin-top: 2px;
        }

        .ide-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 15px;
        }

        .ide-option {
          display: flex;
          align-items: center;
          padding: 15px;
          border: 1px solid #ddd;
          border-radius: 4px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .ide-option:hover {
          border-color: #007bff;
          background-color: #f8f9fa;
        }

        .ide-option input[type="checkbox"]:checked + .ide-info {
          color: #007bff;
        }

        .ide-option input[type="checkbox"] {
          margin-right: 12px;
          width: 16px;
          height: 16px;
        }

        .ide-info strong {
          display: block;
          color: #333;
        }

        .ide-info small {
          display: block;
          color: #666;
          margin-top: 2px;
        }

        .options-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
        }

        .option-item {
          display: flex;
          align-items: center;
          cursor: pointer;
        }

        .option-item input[type="checkbox"] {
          margin-right: 8px;
          width: 16px;
          height: 16px;
        }

        .progress-section {
          margin: 20px 0;
          padding: 15px;
          background-color: #f8f9fa;
          border-radius: 4px;
        }

        .progress-bar {
          width: 100%;
          height: 8px;
          background-color: #e9ecef;
          border-radius: 4px;
          overflow: hidden;
          margin-bottom: 10px;
        }

        .progress-fill {
          height: 100%;
          background-color: #007bff;
          transition: width 0.3s ease;
        }

        .progress-message {
          margin: 0;
          font-size: 14px;
          color: #333;
        }

        .manager-footer {
          padding: 20px;
          border-top: 1px solid #eee;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .export-summary {
          font-size: 14px;
          color: #666;
        }

        .export-summary p {
          margin: 0;
        }

        .action-buttons {
          display: flex;
          gap: 10px;
        }

        .btn {
          padding: 10px 20px;
          border: none;
          border-radius: 4px;
          font-size: 14px;
          cursor: pointer;
          transition: background-color 0.2s ease;
        }

        .btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .btn-sm {
          padding: 6px 12px;
          font-size: 12px;
        }

        .btn-secondary {
          background-color: #6c757d;
          color: white;
        }

        .btn-secondary:hover:not(:disabled) {
          background-color: #545b62;
        }

        .btn-primary {
          background-color: #007bff;
          color: white;
        }

        .btn-primary:hover:not(:disabled) {
          background-color: #0056b3;
        }
      `}</style>
    </div>
  );
};

export default BulkExportManager;