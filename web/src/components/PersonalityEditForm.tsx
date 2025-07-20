/**
 * Edit form component for personality configurations
 */

import React, { useState } from 'react';
import { PersonalityConfig, PersonalityRequest } from '../types/personality';

interface PersonalityEditFormProps {
  config: PersonalityConfig;
  onSave: (updates: Partial<PersonalityRequest>) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
}

const PersonalityEditForm: React.FC<PersonalityEditFormProps> = ({
  config,
  onSave,
  onCancel,
  loading = false,
}) => {
  const [formData, setFormData] = useState({
    description: config.profile.name, // Use the profile name as initial description
    project_path: config.file_path ? config.file_path.replace(/\/[^/]*$/, '') : '', // Extract directory from file path
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.description.trim()) {
      newErrors.description = 'Personality description is required';
    } else if (formData.description.length < 2) {
      newErrors.description = 'Description must be at least 2 characters';
    } else if (formData.description.length > 500) {
      newErrors.description = 'Description must be less than 500 characters';
    }

    if (formData.project_path && formData.project_path.trim() && !formData.project_path.startsWith('/')) {
      newErrors.project_path = 'Project path must be an absolute path starting with /';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    try {
      await onSave({
        description: formData.description,
        project_path: formData.project_path || undefined,
      });
    } catch (error) {
      // Error handling is done by parent component
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (field: keyof typeof formData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <div className="personality-edit-overlay">
      <div className="personality-edit-modal">
        <div className="edit-header">
          <h2>Edit Personality Configuration</h2>
          <button
            onClick={onCancel}
            className="btn btn-sm btn-secondary"
            disabled={isSubmitting}
          >
            ✕
          </button>
        </div>

        <div className="edit-content">
          <div className="current-config-summary">
            <h3>Current Configuration</h3>
            <div className="config-summary">
              <div className="summary-item">
                <strong>Name:</strong> {config.profile.name}
              </div>
              <div className="summary-item">
                <strong>Type:</strong> {config.profile.type}
              </div>
              <div className="summary-item">
                <strong>IDE:</strong> {config.ide_type}
              </div>
              <div className="summary-item">
                <strong>Status:</strong> {config.active ? '✅ Active' : '⏸️ Inactive'}
              </div>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="personality-edit-form">
            <div className="form-group">
              <label htmlFor="edit-description" className="form-label">
                Personality Description *
              </label>
              <textarea
                id="edit-description"
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                placeholder="Describe the personality you want (e.g., 'Tony Stark', 'friendly mentor', 'sarcastic genius')"
                className={`form-input ${errors.description ? 'error' : ''}`}
                rows={3}
                disabled={isSubmitting || loading}
              />
              {errors.description && (
                <span className="error-message">{errors.description}</span>
              )}
              <small className="form-help">
                Changing this will trigger new personality research and regenerate the context.
              </small>
            </div>

            <div className="form-group">
              <label htmlFor="edit-project-path" className="form-label">
                Project Path (Optional)
              </label>
              <input
                type="text"
                id="edit-project-path"
                value={formData.project_path}
                onChange={(e) => handleInputChange('project_path', e.target.value)}
                placeholder="/path/to/your/project"
                className={`form-input ${errors.project_path ? 'error' : ''}`}
                disabled={isSubmitting || loading}
              />
              {errors.project_path && (
                <span className="error-message">{errors.project_path}</span>
              )}
              <small className="form-help">
                Changing this will re-detect the IDE and update integration settings.
              </small>
            </div>

            <div className="form-actions">
              <button
                type="button"
                onClick={onCancel}
                className="btn btn-secondary"
                disabled={isSubmitting || loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isSubmitting || loading}
              >
                {isSubmitting || loading ? 'Updating...' : 'Update Configuration'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default PersonalityEditForm;