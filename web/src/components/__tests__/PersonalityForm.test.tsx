/**
 * Tests for PersonalityForm component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import PersonalityForm from '../PersonalityForm';
import { PersonalityRequest } from '../../types/personality';

describe('PersonalityForm', () => {
  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  it('renders form fields correctly', () => {
    render(<PersonalityForm onSubmit={mockOnSubmit} />);

    expect(screen.getByLabelText(/personality description/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/user id/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/project path/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create personality/i })).toBeInTheDocument();
  });

  it('shows validation error for empty description', async () => {
    const user = userEvent.setup();
    render(<PersonalityForm onSubmit={mockOnSubmit} />);

    const submitButton = screen.getByRole('button', { name: /create personality/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/personality description is required/i)).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('shows validation error for short description', async () => {
    const user = userEvent.setup();
    render(<PersonalityForm onSubmit={mockOnSubmit} />);

    const descriptionInput = screen.getByLabelText(/personality description/i);
    await user.type(descriptionInput, 'a');

    const submitButton = screen.getByRole('button', { name: /create personality/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/description must be at least 2 characters/i)).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('shows validation error for invalid project path', async () => {
    const user = userEvent.setup();
    render(<PersonalityForm onSubmit={mockOnSubmit} />);

    const descriptionInput = screen.getByLabelText(/personality description/i);
    const projectPathInput = screen.getByLabelText(/project path/i);

    await user.type(descriptionInput, 'Tony Stark');
    await user.type(projectPathInput, 'relative/path');

    const submitButton = screen.getByRole('button', { name: /create personality/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/project path must be an absolute path/i)).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('submits form with valid data', async () => {
    const user = userEvent.setup();
    render(<PersonalityForm onSubmit={mockOnSubmit} />);

    const descriptionInput = screen.getByLabelText(/personality description/i);
    const userIdInput = screen.getByLabelText(/user id/i);
    const projectPathInput = screen.getByLabelText(/project path/i);

    await user.type(descriptionInput, 'Tony Stark');
    await user.type(userIdInput, 'test-user');
    await user.type(projectPathInput, '/test/project');

    const submitButton = screen.getByRole('button', { name: /create personality/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        description: 'Tony Stark',
        user_id: 'test-user',
        project_path: '/test/project',
        source: 'web',
      });
    });
  });

  it('disables form when loading', () => {
    render(<PersonalityForm onSubmit={mockOnSubmit} loading={true} />);

    const descriptionInput = screen.getByLabelText(/personality description/i);
    const userIdInput = screen.getByLabelText(/user id/i);
    const projectPathInput = screen.getByLabelText(/project path/i);
    const submitButton = screen.getByRole('button', { name: /creating/i });

    expect(descriptionInput).toBeDisabled();
    expect(userIdInput).toBeDisabled();
    expect(projectPathInput).toBeDisabled();
    expect(submitButton).toBeDisabled();
  });

  it('populates form with initial values', () => {
    const initialValues = {
      description: 'Sherlock Holmes',
      user_id: 'test-user',
      project_path: '/test/project',
    };

    render(<PersonalityForm onSubmit={mockOnSubmit} initialValues={initialValues} />);

    expect(screen.getByDisplayValue('Sherlock Holmes')).toBeInTheDocument();
    expect(screen.getByDisplayValue('test-user')).toBeInTheDocument();
    expect(screen.getByDisplayValue('/test/project')).toBeInTheDocument();
  });

  it('clears validation errors when user starts typing', async () => {
    const user = userEvent.setup();
    render(<PersonalityForm onSubmit={mockOnSubmit} />);

    // Trigger validation error
    const submitButton = screen.getByRole('button', { name: /create personality/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/personality description is required/i)).toBeInTheDocument();
    });

    // Start typing to clear error
    const descriptionInput = screen.getByLabelText(/personality description/i);
    await user.type(descriptionInput, 'T');

    await waitFor(() => {
      expect(screen.queryByText(/personality description is required/i)).not.toBeInTheDocument();
    });
  });
});