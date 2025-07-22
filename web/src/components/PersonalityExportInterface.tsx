/**
 * Personality export interface component
 */

import React, { useState, useEffect } from 'react';
import { 
  PersonalityConfig, 
  ExportFormatOptions, 
  SupportedIDEType, 
  ExportProgressState 
} from '../types/personality';
import PersonalityApi from '../services/api';
import ExportPreview from './ExportPreview';

interface PersonalityExportInterfaceProps {
  personalityConfig: PersonalityConfig;
  onExportComplete?: (success: boolean, fileName?: string) => void;
  onError?: (error: string) => void;
}

interface SupportedIDE {
  type: SupportedIDEType;
  name: string;
  description: string;
  file_extension: string;
  supports_metadata: boolean;
}

const PersonalityExportInterface: React.FC<PersonalityExportInterfaceProps> = ({
  personalityConfig,
  onExportComplete,
  onError,
}) => {
  const [selectedIDEType, setSelectedIDEType] = useState<SupportedIDEType>('cursor');
  const [formatOptions, setFormatOptions] = useState<ExportFormatOptions>({
    include_metadata: true,
    include_instructions: true,
    preserve_comments: true,
  });
  const [supportedIDEs, setSupportedIDEs] = useState<SupportedIDE[]>([]);
  const [progressState, setProgressState] = useState<ExportProgressState>({
    stage: 'idle',
    progress: 0,
    message: '',
  });
  const [showPreview, setShowPreview] = useState(false);

  // Load supported IDEs on mount
  useEffect(() => {
    const loadSupportedIDEs = async () => {
      try {
        const response = await PersonalityApi.getSupportedIDETypes();
        setSupportedIDEs(response.supported_ides as SupportedIDE[]);
      } catch (error: any) {
        console.error('Failed to load supported IDEs:', error);
        // Fallback to default IDE types
        setSupportedIDEs([
          { type: 'cursor', name: 'Cursor', description: 'Cursor IDE rules format', file_extension: '.mdc', supports_metadata: true },
          { type: 'claude', name: 'Claude', description: 'Claude.md format', file_extension: '.md', supports_metadata: true },
          { type: 'windsurf', name: 'Windsurf', description: 'Windsurf JSON format', file_extension: '.json', supports_metadata: true },
          { type: 'generic', name: 'Generic', description: 'Generic markdown format', file_extension: '.md', supports_metadata: false },
        ]);
      }
    };
    
    loadSupportedIDEs();
  }, []);

  const handleExport = async () => {
    try {
      setProgressState({
        stage: 'preparing',
        progress: 10,
        message: 'Preparing export...',
      });

      setProgressState({
        stage: 'generating',
        progress: 50,
        message: 'Generating configuration file...',
      });

      const blob = await PersonalityApi.exportPersonalityConfig(
        personalityConfig.id,
        selectedIDEType,
        formatOptions
      );

      setProgressState({
        stage: 'downloading',
        progress: 90,
        message: 'Initiating download...',
      });

      // Create download
      const url = window.URL.createObjectURL(blob);
      const selectedIDE = supportedIDEs.find(ide => ide.type === selectedIDEType);
      const fileName = formatOptions.file_name || 
        `${personalityConfig.profile.name.toLowerCase().replace(/[^a-z0-9]/g, '_')}_${selectedIDEType}${selectedIDE?.file_extension || '.txt'}`;
      
      const link = document.createElement('a');
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setProgressState({
        stage: 'complete',
        progress: 100,
        message: 'Export completed successfully!',
      });

      onExportComplete?.(true, fileName);

      // Reset after 2 seconds
      setTimeout(() => {
        setProgressState({
          stage: 'idle',
          progress: 0,
          message: '',
        });
      }, 2000);

    } catch (error: any) {
      console.error('Export failed:', error);
      const errorMessage = error.message || 'Export failed unexpectedly';
      
      setProgressState({
        stage: 'error',
        progress: 0,
        message: errorMessage,
        error: errorMessage,
      });

      onError?.(errorMessage);

      // Reset after 3 seconds
      setTimeout(() => {
        setProgressState({
          stage: 'idle',
          progress: 0,
          message: '',
        });
      }, 3000);
    }
  };

  const handlePreview = () => {
    setShowPreview(true);
  };

  const isExporting = progressState.stage !== 'idle';
  const selectedIDE = supportedIDEs.find(ide => ide.type === selectedIDEType);

  return (
    <div className="personality-export-interface">
      <div className="export-header">
        <h3>Export Configuration</h3>
        <p>Export "{personalityConfig.profile.name}" for use in your IDE</p>
      </div>

      <form onSubmit={(e) => { e.preventDefault(); handleExport(); }}>
        {/* IDE Selection */}
        <div className="form-group">
          <label htmlFor="ide-type">Target IDE:</label>
          <select
            id="ide-type"
            value={selectedIDEType}
            onChange={(e) => setSelectedIDEType(e.target.value as SupportedIDEType)}
            disabled={isExporting}
          >
            {supportedIDEs.map((ide) => (
              <option key={ide.type} value={ide.type}>
                {ide.name} - {ide.description}
              </option>
            ))}
          </select>
          {selectedIDE && (
            <small className="ide-info">
              File type: {selectedIDE.file_extension} | 
              Metadata support: {selectedIDE.supports_metadata ? 'Yes' : 'No'}
            </small>
          )}
        </div>

        {/* Format Options */}
        <div className="form-group">
          <fieldset>
            <legend>Export Options:</legend>
            
            <div className="checkbox-group">
              <label>
                <input
                  type="checkbox"
                  checked={formatOptions.include_metadata || false}
                  onChange={(e) => setFormatOptions(prev => ({
                    ...prev,
                    include_metadata: e.target.checked
                  }))}
                  disabled={isExporting || !selectedIDE?.supports_metadata}
                />
                Include metadata and generation info
              </label>
            </div>

            <div className="checkbox-group">
              <label>
                <input
                  type="checkbox"
                  checked={formatOptions.include_instructions || false}
                  onChange={(e) => setFormatOptions(prev => ({
                    ...prev,
                    include_instructions: e.target.checked
                  }))}
                  disabled={isExporting}
                />
                Include placement instructions
              </label>
            </div>

            <div className="checkbox-group">
              <label>
                <input
                  type="checkbox"
                  checked={formatOptions.preserve_comments || false}
                  onChange={(e) => setFormatOptions(prev => ({
                    ...prev,
                    preserve_comments: e.target.checked
                  }))}
                  disabled={isExporting}
                />
                Preserve code comments
              </label>
            </div>
          </fieldset>
        </div>

        {/* Custom Options */}
        <div className="form-group">
          <label htmlFor="custom-filename">Custom filename (optional):</label>
          <input
            type="text"
            id="custom-filename"
            value={formatOptions.file_name || ''}
            onChange={(e) => setFormatOptions(prev => ({
              ...prev,
              file_name: e.target.value || undefined
            }))}
            placeholder={`${personalityConfig.profile.name.toLowerCase().replace(/[^a-z0-9]/g, '_')}_${selectedIDEType}${selectedIDE?.file_extension || '.txt'}`}
            disabled={isExporting}
          />
        </div>

        <div className="form-group">
          <label htmlFor="custom-header">Custom header (optional):</label>
          <textarea
            id="custom-header"
            value={formatOptions.custom_header || ''}
            onChange={(e) => setFormatOptions(prev => ({
              ...prev,
              custom_header: e.target.value || undefined
            }))}
            placeholder="Add custom header text to the exported file..."
            rows={3}
            disabled={isExporting}
          />
        </div>

        {/* Progress Display */}
        {progressState.stage !== 'idle' && (
          <div className={`progress-display ${progressState.stage}`}>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${progressState.progress}%` }}
              ></div>
            </div>
            <p className="progress-message">{progressState.message}</p>
            {progressState.error && (
              <p className="error-message">{progressState.error}</p>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="button-group">
          <button
            type="button"
            onClick={handlePreview}
            disabled={isExporting}
            className="btn btn-secondary"
          >
            Preview
          </button>
          
          <button
            type="submit"
            disabled={isExporting}
            className="btn btn-primary"
          >
            {isExporting ? 'Exporting...' : 'Export & Download'}
          </button>
        </div>
      </form>

      {/* Export Preview Modal */}
      <ExportPreview
        personalityId={personalityConfig.id}
        ideType={selectedIDEType}
        formatOptions={formatOptions}
        isOpen={showPreview}
        onClose={() => setShowPreview(false)}
        onDownload={() => {
          setShowPreview(false);
          handleExport();
        }}
      />

      <style jsx>{`
        .personality-export-interface {
          max-width: 600px;
          margin: 0 auto;
          padding: 20px;
        }

        .export-header {
          text-align: center;
          margin-bottom: 30px;
        }

        .export-header h3 {
          margin: 0 0 10px 0;
          color: #333;
        }

        .export-header p {
          color: #666;
          margin: 0;
        }

        .form-group {
          margin-bottom: 20px;
        }

        .form-group label {
          display: block;
          margin-bottom: 8px;
          font-weight: 500;
          color: #333;
        }

        .form-group select,
        .form-group input,
        .form-group textarea {
          width: 100%;
          padding: 10px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 14px;
        }

        .form-group select:focus,
        .form-group input:focus,
        .form-group textarea:focus {
          outline: none;
          border-color: #007bff;
          box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
        }

        .ide-info {
          display: block;
          margin-top: 5px;
          color: #666;
          font-size: 12px;
        }

        fieldset {
          border: 1px solid #ddd;
          border-radius: 4px;
          padding: 15px;
        }

        legend {
          padding: 0 10px;
          font-weight: 500;
          color: #333;
        }

        .checkbox-group {
          margin: 10px 0;
        }

        .checkbox-group label {
          display: flex;
          align-items: center;
          margin-bottom: 0;
          font-weight: normal;
        }

        .checkbox-group input[type="checkbox"] {
          width: auto;
          margin-right: 8px;
        }

        .progress-display {
          margin: 20px 0;
          padding: 15px;
          border: 1px solid #ddd;
          border-radius: 4px;
          background-color: #f8f9fa;
        }

        .progress-display.error {
          border-color: #dc3545;
          background-color: #f8d7da;
        }

        .progress-display.complete {
          border-color: #28a745;
          background-color: #d4edda;
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

        .progress-display.complete .progress-fill {
          background-color: #28a745;
        }

        .progress-display.error .progress-fill {
          background-color: #dc3545;
        }

        .progress-message {
          margin: 0;
          font-size: 14px;
          color: #333;
        }

        .error-message {
          margin: 5px 0 0 0;
          color: #dc3545;
          font-size: 14px;
        }

        .button-group {
          display: flex;
          gap: 10px;
          justify-content: flex-end;
          margin-top: 30px;
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

        .modal-backdrop {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background-color: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .modal {
          background: white;
          border-radius: 8px;
          max-width: 90vw;
          max-height: 90vh;
          overflow-y: auto;
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px;
          border-bottom: 1px solid #ddd;
        }

        .modal-header h4 {
          margin: 0;
        }

        .close-button {
          background: none;
          border: none;
          font-size: 24px;
          cursor: pointer;
          color: #999;
        }

        .close-button:hover {
          color: #333;
        }

        .modal-body {
          padding: 20px;
        }
      `}</style>
    </div>
  );
};

export default PersonalityExportInterface;