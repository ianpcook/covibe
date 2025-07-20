/**
 * Personality input form component
 */

import React, { useState } from 'react';
import { PersonalityRequest } from '../types/personality';

interface PersonalityFormProps {
  onSubmit: (request: PersonalityRequest) => void;
  loading?: boolean;
  initialValues?: Partial<PersonalityRequest>;
}

const PersonalityForm: React.FC<PersonalityFormProps> = ({
  onSubmit,
  loading = false,
  initialValues = {},
}) => {
  const [formData, setFormData] = useState<PersonalityRequest>({
    description: initialValues.description || '',
    user_id: initialValues.user_id || '',
    project_path: initialValues.project_path || '',
    source: 'web',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      onSubmit(formData);
    }
  };

  const handleInputChange = (field: keyof PersonalityRequest, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <form onSubmit={handleSubmit} className="personality-form">
      <div className="form-group">
        <label htmlFor="description" className="form-label">
          Personality Description *
        </label>
        <textarea
          id="description"
          value={formData.description}
          onChange={(e) => handleInputChange('description', e.target.value)}
          placeholder="Describe the personality you want (e.g., 'Tony Stark', 'friendly mentor', 'sarcastic genius')"
          className={`form-input ${errors.description ? 'error' : ''}`}
          rows={3}
          disabled={loading}
        />
        {errors.description && (
          <span className="error-message">{errors.description}</span>
        )}
        <small className="form-help">
          You can describe celebrities, fictional characters, archetypes, or personality traits.
        </small>
      </div>

      <div className="form-group">
        <label htmlFor="user_id" className="form-label">
          User ID (Optional)
        </label>
        <input
          type="text"
          id="user_id"
          value={formData.user_id}
          onChange={(e) => handleInputChange('user_id', e.target.value)}
          placeholder="Optional user identifier"
          className="form-input"
          disabled={loading}
        />
        <small className="form-help">
          Optional identifier for tracking your configurations.
        </small>
      </div>

      <div className="form-group">
        <label htmlFor="project_path" className="form-label">
          Project Path (Optional)
        </label>
        <input
          type="text"
          id="project_path"
          value={formData.project_path}
          onChange={(e) => handleInputChange('project_path', e.target.value)}
          placeholder="/path/to/your/project"
          className={`form-input ${errors.project_path ? 'error' : ''}`}
          disabled={loading}
        />
        {errors.project_path && (
          <span className="error-message">{errors.project_path}</span>
        )}
        <small className="form-help">
          Optional path to your project for IDE integration (e.g., /Users/username/myproject).
        </small>
      </div>

      <div className="form-actions">
        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading}
        >
          {loading ? 'Creating...' : 'Create Personality'}
        </button>
      </div>
    </form>
  );
};

export default PersonalityForm;