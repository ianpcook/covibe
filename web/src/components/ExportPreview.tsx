/**
 * Export preview component with syntax highlighting
 */

import React, { useState, useEffect } from 'react';
import { 
  PreviewResult, 
  ExportFormatOptions, 
  SupportedIDEType 
} from '../types/personality';
import PersonalityApi from '../services/api';

interface ExportPreviewProps {
  personalityId: string;
  ideType: SupportedIDEType;
  formatOptions?: ExportFormatOptions;
  onDownload?: () => void;
  onClose?: () => void;
  isOpen: boolean;
}

const ExportPreview: React.FC<ExportPreviewProps> = ({
  personalityId,
  ideType,
  formatOptions,
  onDownload,
  onClose,
  isOpen,
}) => {
  const [previewData, setPreviewData] = useState<PreviewResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Load preview when component opens
  useEffect(() => {
    if (isOpen && personalityId && ideType) {
      loadPreview();
    }
  }, [isOpen, personalityId, ideType, formatOptions]);

  const loadPreview = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await PersonalityApi.previewPersonalityExport(
        personalityId,
        ideType,
        formatOptions
      );
      
      if (result.success) {
        setPreviewData(result);
      } else {
        setError(result.error || 'Failed to generate preview');
      }
    } catch (err: any) {
      console.error('Preview failed:', err);
      setError(err.message || 'Preview generation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyContent = async () => {
    if (previewData?.content) {
      try {
        await navigator.clipboard.writeText(previewData.content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch (err) {
        console.error('Failed to copy content:', err);
      }
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getSyntaxHighlighting = (content: string, language: string): string => {
    // Basic syntax highlighting - in a real implementation, you'd use a library like Prism.js
    // For now, we'll just apply basic formatting
    switch (language.toLowerCase()) {
      case 'markdown':
      case 'md':
        return content
          .replace(/^(#{1,6})\s+(.+)$/gm, '<span class="md-header">$1 $2</span>')
          .replace(/\*\*(.+?)\*\*/g, '<span class="md-bold">**$1**</span>')
          .replace(/\*(.+?)\*/g, '<span class="md-italic">*$1*</span>')
          .replace(/`(.+?)`/g, '<span class="md-code">`$1`</span>');
      
      case 'json':
        return content
          .replace(/"([^"]+)":/g, '<span class="json-key">"$1":</span>')
          .replace(/:\s*"([^"]*)"/g, ': <span class="json-string">"$1"</span>')
          .replace(/:\s*(true|false|null)/g, ': <span class="json-literal">$1</span>')
          .replace(/:\s*(\d+)/g, ': <span class="json-number">$1</span>');
      
      default:
        return content;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop">
      <div className="export-preview-modal">
        <div className="modal-header">
          <div className="header-info">
            <h3>Export Preview</h3>
            {previewData && (
              <div className="file-info">
                <span className="file-name">{previewData.file_name}</span>
                <span className="file-size">({formatFileSize(previewData.file_size)})</span>
                <span className="file-type">{previewData.syntax_language}</span>
              </div>
            )}
          </div>
          <button onClick={onClose} className="close-button" aria-label="Close preview">
            ×
          </button>
        </div>

        <div className="modal-body">
          {loading && (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <p>Generating preview...</p>
            </div>
          )}

          {error && (
            <div className="error-state">
              <p className="error-message">⚠️ {error}</p>
              <button onClick={loadPreview} className="btn btn-secondary">
                Retry
              </button>
            </div>
          )}

          {previewData && !loading && !error && (
            <>
              <div className="preview-toolbar">
                <div className="toolbar-section">
                  <span className="syntax-label">
                    Language: {previewData.syntax_language}
                  </span>
                </div>
                <div className="toolbar-actions">
                  <button
                    onClick={handleCopyContent}
                    className="btn btn-sm btn-outline"
                    title="Copy content to clipboard"
                  >
                    {copied ? '✓ Copied' : '📋 Copy'}
                  </button>
                </div>
              </div>

              <div className="content-preview">
                <pre className={`code-block ${previewData.syntax_language}`}>
                  <code
                    dangerouslySetInnerHTML={{
                      __html: getSyntaxHighlighting(previewData.content, previewData.syntax_language)
                    }}
                  />
                </pre>
              </div>

              {previewData.placement_instructions && previewData.placement_instructions.length > 0 && (
                <div className="placement-instructions">
                  <h4>📍 Placement Instructions</h4>
                  <ol>
                    {previewData.placement_instructions.map((instruction, index) => (
                      <li key={index}>{instruction}</li>
                    ))}
                  </ol>
                </div>
              )}

              {previewData.metadata && Object.keys(previewData.metadata).length > 0 && (
                <div className="metadata-section">
                  <h4>📋 Metadata</h4>
                  <div className="metadata-grid">
                    {Object.entries(previewData.metadata).map(([key, value]) => (
                      <div key={key} className="metadata-item">
                        <strong>{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</strong>
                        <span>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        <div className="modal-footer">
          <div className="footer-actions">
            <button onClick={onClose} className="btn btn-secondary">
              Close
            </button>
            {previewData && (
              <button
                onClick={onDownload}
                className="btn btn-primary"
              >
                Download File
              </button>
            )}
          </div>
        </div>
      </div>

      <style jsx>{`
        .modal-backdrop {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background-color: rgba(0, 0, 0, 0.7);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1050;
          padding: 20px;
        }

        .export-preview-modal {
          background: white;
          border-radius: 8px;
          max-width: 90vw;
          max-height: 90vh;
          width: 1000px;
          display: flex;
          flex-direction: column;
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px;
          border-bottom: 1px solid #eee;
          background-color: #f8f9fa;
          border-radius: 8px 8px 0 0;
        }

        .header-info h3 {
          margin: 0 0 8px 0;
          color: #333;
        }

        .file-info {
          display: flex;
          gap: 10px;
          align-items: center;
          font-size: 14px;
          color: #666;
        }

        .file-name {
          font-weight: 500;
          color: #333;
        }

        .file-size {
          color: #888;
        }

        .file-type {
          background-color: #e9ecef;
          padding: 2px 8px;
          border-radius: 12px;
          font-size: 12px;
          text-transform: uppercase;
        }

        .close-button {
          background: none;
          border: none;
          font-size: 28px;
          cursor: pointer;
          color: #999;
          line-height: 1;
          padding: 0;
          width: 30px;
          height: 30px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .close-button:hover {
          color: #333;
        }

        .modal-body {
          flex: 1;
          overflow-y: auto;
          padding: 0;
        }

        .loading-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 60px 20px;
          color: #666;
        }

        .loading-spinner {
          width: 40px;
          height: 40px;
          border: 3px solid #f3f3f3;
          border-top: 3px solid #007bff;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin-bottom: 20px;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .error-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 60px 20px;
        }

        .error-message {
          color: #dc3545;
          margin-bottom: 20px;
          text-align: center;
        }

        .preview-toolbar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 15px 20px;
          background-color: #f8f9fa;
          border-bottom: 1px solid #eee;
        }

        .syntax-label {
          font-size: 13px;
          color: #666;
          font-weight: 500;
        }

        .toolbar-actions {
          display: flex;
          gap: 10px;
        }

        .content-preview {
          max-height: 500px;
          overflow: auto;
          background-color: #f8f9fa;
        }

        .code-block {
          margin: 0;
          padding: 20px;
          background-color: #f8f9fa;
          border: none;
          font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
          font-size: 13px;
          line-height: 1.5;
          white-space: pre-wrap;
          word-wrap: break-word;
        }

        .code-block code {
          background: none;
          padding: 0;
          font-family: inherit;
        }

        /* Basic syntax highlighting styles */
        :global(.md-header) { color: #0366d6; font-weight: bold; }
        :global(.md-bold) { color: #24292e; font-weight: bold; }
        :global(.md-italic) { color: #24292e; font-style: italic; }
        :global(.md-code) { background-color: #f6f8fa; color: #e36209; }
        :global(.json-key) { color: #032f62; }
        :global(.json-string) { color: #032f62; }
        :global(.json-literal) { color: #005cc5; }
        :global(.json-number) { color: #005cc5; }

        .placement-instructions {
          padding: 20px;
          background-color: #fff3cd;
          border-top: 1px solid #ffeaa7;
        }

        .placement-instructions h4 {
          margin: 0 0 15px 0;
          color: #856404;
        }

        .placement-instructions ol {
          margin: 0;
          padding-left: 20px;
        }

        .placement-instructions li {
          margin-bottom: 8px;
          color: #856404;
        }

        .metadata-section {
          padding: 20px;
          background-color: #f8f9fa;
          border-top: 1px solid #eee;
        }

        .metadata-section h4 {
          margin: 0 0 15px 0;
          color: #495057;
        }

        .metadata-grid {
          display: grid;
          gap: 10px;
        }

        .metadata-item {
          display: flex;
          gap: 10px;
        }

        .metadata-item strong {
          min-width: 120px;
          color: #495057;
        }

        .metadata-item span {
          color: #6c757d;
          word-break: break-word;
        }

        .modal-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px;
          border-top: 1px solid #eee;
          background-color: #f8f9fa;
          border-radius: 0 0 8px 8px;
        }

        .footer-actions {
          display: flex;
          gap: 10px;
          margin-left: auto;
        }

        .btn {
          padding: 8px 16px;
          border: none;
          border-radius: 4px;
          font-size: 14px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .btn-sm {
          padding: 6px 12px;
          font-size: 12px;
        }

        .btn-outline {
          background-color: transparent;
          border: 1px solid #6c757d;
          color: #6c757d;
        }

        .btn-outline:hover {
          background-color: #6c757d;
          color: white;
        }

        .btn-secondary {
          background-color: #6c757d;
          color: white;
        }

        .btn-secondary:hover {
          background-color: #545b62;
        }

        .btn-primary {
          background-color: #007bff;
          color: white;
        }

        .btn-primary:hover {
          background-color: #0056b3;
        }
      `}</style>
    </div>
  );
};

export default ExportPreview;