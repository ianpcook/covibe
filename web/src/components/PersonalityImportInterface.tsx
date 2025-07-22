/**
 * Personality import interface component
 */

import React, { useState, useCallback } from 'react';
import { PersonalityConfig } from '../types/personality';
import PersonalityApi from '../services/api';

interface PersonalityImportInterfaceProps {
  onImportComplete?: (config: PersonalityConfig) => void;
  onError?: (error: string) => void;
  onClose?: () => void;
}

interface ValidationResult {
  valid: boolean;
  detected_format: string;
  ide_type: string;
  confidence: number;
  errors: string[];
  warnings: string[];
}

const PersonalityImportInterface: React.FC<PersonalityImportInterfaceProps> = ({
  onImportComplete,
  onError,
  onClose,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [importProgress, setImportProgress] = useState({ stage: 'idle', message: '' });

  const handleFiles = useCallback(async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    const file = files[0];
    
    // Validate file type
    if (!file.name.match(/\.(md|mdc|json|txt)$/i)) {
      onError?.('Please select a valid configuration file (.md, .mdc, .json, or .txt)');
      return;
    }

    // Validate file size (5MB limit)
    if (file.size > 5 * 1024 * 1024) {
      onError?.('File size must be less than 5MB');
      return;
    }

    setSelectedFile(file);
    
    // Automatically validate the file
    await validateFile(file);
  }, [onError]);

  const validateFile = async (file: File) => {
    setIsValidating(true);
    setValidationResult(null);
    
    try {
      const result = await PersonalityApi.validateImportFile(file);
      setValidationResult(result);
      
      if (!result.valid && result.errors.length > 0) {
        onError?.(`Validation failed: ${result.errors.join(', ')}`);
      }
    } catch (error: any) {
      console.error('File validation failed:', error);
      onError?.('Failed to validate file. Please try again.');
      setValidationResult(null);
    } finally {
      setIsValidating(false);
    }
  };

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    handleFiles(e.target.files);
  }, [handleFiles]);

  const handleImport = async () => {
    if (!selectedFile || !validationResult?.valid) return;

    setIsImporting(true);
    setImportProgress({ stage: 'uploading', message: 'Uploading file...' });

    try {
      setImportProgress({ stage: 'parsing', message: 'Parsing configuration...' });
      
      const importedConfig = await PersonalityApi.importPersonalityConfig(selectedFile);
      
      setImportProgress({ stage: 'complete', message: 'Import completed successfully!' });
      
      onImportComplete?.(importedConfig);
      
      // Close after a brief delay
      setTimeout(() => {
        onClose?.();
      }, 1500);
      
    } catch (error: any) {
      console.error('Import failed:', error);
      const errorMessage = error.message || 'Import failed unexpectedly';
      onError?.(errorMessage);
      setIsImporting(false);
      setImportProgress({ stage: 'idle', message: '' });
    }
  };

  const handleClearFile = () => {
    setSelectedFile(null);
    setValidationResult(null);
    setImportProgress({ stage: 'idle', message: '' });
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return '#28a745';
    if (confidence >= 0.6) return '#ffc107';
    return '#dc3545';
  };

  const getConfidenceText = (confidence: number) => {
    if (confidence >= 0.8) return 'High';
    if (confidence >= 0.6) return 'Medium';
    return 'Low';
  };

  return (
    <div className="personality-import-interface">
      <div className="import-header">
        <h3>Import Personality Configuration</h3>
        <p>Import personality configurations from other IDEs or previous exports</p>
      </div>

      <div className="import-content">
        {!selectedFile ? (
          <div
            className={`file-drop-zone ${dragActive ? 'drag-active' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <div className="drop-zone-content">
              <div className="upload-icon">📁</div>
              <p className="drop-text">
                Drag and drop a configuration file here, or{' '}
                <label className="file-select-link">
                  browse files
                  <input
                    type="file"
                    accept=".md,.mdc,.json,.txt"
                    onChange={handleFileSelect}
                    style={{ display: 'none' }}
                  />
                </label>
              </p>
              <p className="supported-formats">
                Supported formats: .md, .mdc, .json, .txt (max 5MB)
              </p>
            </div>
          </div>
        ) : (
          <div className="file-selected">
            <div className="file-info">
              <div className="file-details">
                <h4>{selectedFile.name}</h4>
                <p>
                  Size: {(selectedFile.size / 1024).toFixed(1)} KB • 
                  Type: {selectedFile.type || 'Unknown'}
                </p>
              </div>
              <button onClick={handleClearFile} className="clear-file-btn" title="Remove file">
                ×
              </button>
            </div>

            {isValidating && (
              <div className="validation-status">
                <div className="loading-spinner"></div>
                <p>Validating file...</p>
              </div>
            )}

            {validationResult && !isValidating && (
              <div className={`validation-result ${validationResult.valid ? 'valid' : 'invalid'}`}>
                <div className="validation-header">
                  <span className={`status-icon ${validationResult.valid ? 'success' : 'error'}`}>
                    {validationResult.valid ? '✅' : '❌'}
                  </span>
                  <span className="validation-title">
                    {validationResult.valid ? 'File is valid' : 'Validation failed'}
                  </span>
                </div>

                <div className="validation-details">
                  <div className="detail-row">
                    <strong>Detected format:</strong> {validationResult.detected_format}
                  </div>
                  <div className="detail-row">
                    <strong>IDE type:</strong> {validationResult.ide_type}
                  </div>
                  <div className="detail-row">
                    <strong>Confidence:</strong>
                    <span 
                      className="confidence-badge"
                      style={{ backgroundColor: getConfidenceColor(validationResult.confidence) }}
                    >
                      {getConfidenceText(validationResult.confidence)} ({Math.round(validationResult.confidence * 100)}%)
                    </span>
                  </div>
                </div>

                {validationResult.warnings.length > 0 && (
                  <div className="warnings">
                    <strong>⚠️ Warnings:</strong>
                    <ul>
                      {validationResult.warnings.map((warning, index) => (
                        <li key={index}>{warning}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {validationResult.errors.length > 0 && (
                  <div className="errors">
                    <strong>❌ Errors:</strong>
                    <ul>
                      {validationResult.errors.map((error, index) => (
                        <li key={index}>{error}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Progress Display */}
        {isImporting && (
          <div className="import-progress">
            <div className="progress-content">
              <div className="loading-spinner"></div>
              <p>{importProgress.message}</p>
            </div>
          </div>
        )}
      </div>

      <div className="import-footer">
        <div className="import-info">
          {validationResult?.valid && (
            <p className="ready-message">
              Ready to import {validationResult.detected_format} configuration
            </p>
          )}
        </div>

        <div className="action-buttons">
          <button
            onClick={onClose}
            className="btn btn-secondary"
            disabled={isImporting}
          >
            Cancel
          </button>
          
          <button
            onClick={handleImport}
            className="btn btn-primary"
            disabled={!selectedFile || !validationResult?.valid || isImporting}
          >
            {isImporting ? 'Importing...' : 'Import Configuration'}
          </button>
        </div>
      </div>

      <style jsx>{`
        .personality-import-interface {
          max-width: 600px;
          margin: 0 auto;
        }

        .import-header {
          text-align: center;
          padding: 20px;
          border-bottom: 1px solid #eee;
        }

        .import-header h3 {
          margin: 0 0 10px 0;
          color: #333;
        }

        .import-header p {
          margin: 0;
          color: #666;
        }

        .import-content {
          padding: 30px 20px;
          min-height: 300px;
        }

        .file-drop-zone {
          border: 2px dashed #ccc;
          border-radius: 8px;
          padding: 40px 20px;
          text-align: center;
          transition: all 0.2s ease;
          cursor: pointer;
        }

        .file-drop-zone:hover,
        .file-drop-zone.drag-active {
          border-color: #007bff;
          background-color: #f8f9fa;
        }

        .drop-zone-content {
          pointer-events: none;
        }

        .upload-icon {
          font-size: 48px;
          margin-bottom: 15px;
        }

        .drop-text {
          font-size: 16px;
          color: #333;
          margin-bottom: 10px;
        }

        .file-select-link {
          color: #007bff;
          cursor: pointer;
          text-decoration: underline;
          pointer-events: all;
        }

        .file-select-link:hover {
          color: #0056b3;
        }

        .supported-formats {
          font-size: 14px;
          color: #666;
          margin: 0;
        }

        .file-selected {
          border: 1px solid #ddd;
          border-radius: 8px;
          padding: 20px;
        }

        .file-info {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 20px;
        }

        .file-details h4 {
          margin: 0 0 5px 0;
          color: #333;
        }

        .file-details p {
          margin: 0;
          color: #666;
          font-size: 14px;
        }

        .clear-file-btn {
          background: none;
          border: none;
          font-size: 24px;
          cursor: pointer;
          color: #999;
          width: 30px;
          height: 30px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 50%;
          transition: all 0.2s ease;
        }

        .clear-file-btn:hover {
          background-color: #f0f0f0;
          color: #333;
        }

        .validation-status {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 15px;
          background-color: #f8f9fa;
          border-radius: 4px;
          margin-bottom: 15px;
        }

        .loading-spinner {
          width: 20px;
          height: 20px;
          border: 2px solid #f3f3f3;
          border-top: 2px solid #007bff;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .validation-result {
          padding: 15px;
          border-radius: 6px;
          margin-bottom: 15px;
        }

        .validation-result.valid {
          background-color: #d4edda;
          border: 1px solid #c3e6cb;
        }

        .validation-result.invalid {
          background-color: #f8d7da;
          border: 1px solid #f5c6cb;
        }

        .validation-header {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 10px;
        }

        .status-icon {
          font-size: 18px;
        }

        .validation-title {
          font-weight: 500;
          color: #333;
        }

        .validation-details {
          margin: 10px 0;
        }

        .detail-row {
          display: flex;
          gap: 10px;
          margin-bottom: 5px;
          font-size: 14px;
        }

        .confidence-badge {
          color: white;
          padding: 2px 8px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 500;
        }

        .warnings,
        .errors {
          margin-top: 10px;
          font-size: 14px;
        }

        .warnings strong {
          color: #856404;
        }

        .errors strong {
          color: #721c24;
        }

        .warnings ul,
        .errors ul {
          margin: 5px 0 0 0;
          padding-left: 20px;
        }

        .import-progress {
          display: flex;
          justify-content: center;
          align-items: center;
          padding: 30px;
          background-color: #f8f9fa;
          border-radius: 6px;
        }

        .progress-content {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 15px;
        }

        .progress-content .loading-spinner {
          width: 30px;
          height: 30px;
        }

        .import-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px;
          border-top: 1px solid #eee;
        }

        .import-info {
          flex: 1;
        }

        .ready-message {
          margin: 0;
          color: #28a745;
          font-weight: 500;
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

export default PersonalityImportInterface;