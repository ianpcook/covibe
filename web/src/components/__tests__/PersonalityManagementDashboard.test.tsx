/**
 * Integration tests for PersonalityManagementDashboard component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import PersonalityManagementDashboard from '../PersonalityManagementDashboard';
import { PersonalityApi } from '../../services/api';
import { PersonalityConfig } from '../../types/personality';

// Mock the API
vi.mock('../../services/api');

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

// Mock window.confirm
Object.defineProperty(window, 'confirm', {
  value: vi.fn(),
});

// Sample test data
const mockConfigurations: PersonalityConfig[] = [
  {
    id: '1',
    profile: {
      id: 'profile-1',
      name: 'Tony Stark',
      type: 'fictional',
      traits: [
        {
          category: 'personality',
          trait: 'confident',
          intensity: 9,
          examples: ['assertive', 'self-assured']
        }
      ],
      communication_style: {
        tone: 'witty',
        formality: 'casual',
        verbosity: 'moderate',
        technical_level: 'expert'
      },
      mannerisms: ['uses humor', 'tech references'],
      sources: [
        {
          type: 'fictional',
          confidence: 0.9,
          last_updated: '2024-01-01T00:00:00Z'
        }
      ]
    },
    context: 'You are Tony Stark...',
    ide_type: 'cursor',
    file_path: '/cursor/rules/tony-stark.mdc',
    active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  },
  {
    id: '2',
    profile: {
      id: 'profile-2',
      name: 'Sherlock Holmes',
      type: 'fictional',
      traits: [
        {
          category: 'personality',
          trait: 'analytical',
          intensity: 10,
          examples: ['logical', 'deductive']
        }
      ],
      communication_style: {
        tone: 'analytical',
        formality: 'formal',
        verbosity: 'verbose',
        technical_level: 'expert'
      },
      mannerisms: ['deductive reasoning', 'precise language'],
      sources: [
        {
          type: 'fictional',
          confidence: 0.95,
          last_updated: '2024-01-01T00:00:00Z'
        }
      ]
    },
    context: 'You are Sherlock Holmes...',
    ide_type: 'claude',
    file_path: '/project/CLAUDE.md',
    active: false,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  }
];

describe('PersonalityManagementDashboard Integration Tests', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue('1'); // Tony Stark is active
    
    // Mock successful API responses
    vi.mocked(PersonalityApi.listPersonalityConfigs).mockResolvedValue({
      configurations: mockConfigurations,
      pagination: {
        total: 2,
        limit: 100,
        offset: 0,
        has_more: false
      }
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Dashboard Loading and Display', () => {
    it('should load and display personality configurations', async () => {
      render(<PersonalityManagementDashboard />);

      // Check loading state
      expect(screen.getByText('Loading configurations...')).toBeInTheDocument();

      // Wait for configurations to load
      await waitFor(() => {
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
        expect(screen.getByText('Sherlock Holmes')).toBeInTheDocument();
      });

      // Check dashboard stats
      expect(screen.getByText('2')).toBeInTheDocument(); // Total personalities
      expect(screen.getByText('1')).toBeInTheDocument(); // Active personalities
    });

    it('should display quick switcher when configurations exist', async () => {
      render(<PersonalityManagementDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Quick Switch')).toBeInTheDocument();
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
      });
    });

    it('should handle API errors gracefully', async () => {
      vi.mocked(PersonalityApi.listPersonalityConfigs).mockRejectedValue(
        new Error('Network error')
      );

      render(<PersonalityManagementDashboard />);

      await waitFor(() => {
        expect(screen.getByText(/Failed to load personality configurations/)).toBeInTheDocument();
      });
    });
  });

  describe('Configuration Management', () => {
    it('should delete a configuration with confirmation', async () => {
      vi.mocked(window.confirm).mockReturnValue(true);
      vi.mocked(PersonalityApi.deletePersonalityConfig).mockResolvedValue();

      render(<PersonalityManagementDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
      });

      // Find and click delete button for Tony Stark
      const tonyCard = screen.getByText('Tony Stark').closest('.personality-card');
      const deleteButton = within(tonyCard!).getByTitle('Delete');
      
      await user.click(deleteButton);

      // Check confirmation dialog
      expect(window.confirm).toHaveBeenCalledWith(
        'Are you sure you want to delete "Tony Stark"? This action cannot be undone.'
      );

      // Wait for deletion to complete
      await waitFor(() => {
        expect(screen.getByText('Successfully deleted "Tony Stark"')).toBeInTheDocument();
      });

      // Verify API was called
      expect(PersonalityApi.deletePersonalityConfig).toHaveBeenCalledWith('1');
    });

    it('should not delete configuration if user cancels', async () => {
      vi.mocked(window.confirm).mockReturnValue(false);

      render(<PersonalityManagementDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
      });

      const tonyCard = screen.getByText('Tony Stark').closest('.personality-card');
      const deleteButton = within(tonyCard!).getByTitle('Delete');
      
      await user.click(deleteButton);

      expect(window.confirm).toHaveBeenCalled();
      expect(PersonalityApi.deletePersonalityConfig).not.toHaveBeenCalled();
    });

    it('should toggle personality active status', async () => {
      render(<PersonalityManagementDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Sherlock Holmes')).toBeInTheDocument();
      });

      // Find and click activate button for Sherlock Holmes
      const sherlockCard = screen.getByText('Sherlock Holmes').closest('.personality-card');
      const activateButton = within(sherlockCard!).getByTitle('Activate');
      
      await user.click(activateButton);

      // Wait for activation to complete
      await waitFor(() => {
        expect(screen.getByText('Activated "Sherlock Holmes"')).toBeInTheDocument();
      });

      // Check localStorage was updated
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('activePersonalityId', '2');
    });

    it('should handle delete operation errors', async () => {
      vi.mocked(window.confirm).mockReturnValue(true);
      vi.mocked(PersonalityApi.deletePersonalityConfig).mockRejectedValue(
        new Error('Delete failed')
      );

      render(<PersonalityManagementDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
      });

      const tonyCard = screen.getByText('Tony Stark').closest('.personality-card');
      const deleteButton = within(tonyCard!).getByTitle('Delete');
      
      await user.click(deleteButton);

      await waitFor(() => {
        expect(screen.getByText(/Failed to delete personality configuration/)).toBeInTheDocument();
      });
    });
  });

  describe('Search and Filtering', () => {
    it('should filter configurations by search query', async () => {
      render(<PersonalityManagementDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
        expect(screen.getByText('Sherlock Holmes')).toBeInTheDocument();
      });

      // Search for "Tony"
      const searchInput = screen.getByPlaceholderText('Search personalities...');
      await user.type(searchInput, 'Tony');

      // Only Tony Stark should be visible
      expect(screen.getByText('Tony Stark')).toBeInTheDocument();
      expect(screen.queryByText('Sherlock Holmes')).not.toBeInTheDocument();
    });

    it('should filter configurations by type', async () => {
      render(<PersonalityManagementDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
        expect(screen.getByText('Sherlock Holmes')).toBeInTheDocument();
      });

      // Filter by fictional type
      const typeFilter = screen.getByDisplayValue('All Types');
      await user.selectOptions(typeFilter, 'fictional');

      // Both should still be visible (both are fictional)
      expect(screen.getByText('Tony Stark')).toBeInTheDocument();
      expect(screen.getByText('Sherlock Holmes')).toBeInTheDocument();
    });

    it('should sort configurations by different criteria', async () => {
      render(<PersonalityManagementDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
      });

      // Change sort to name
      const sortSelect = screen.getByDisplayValue('Recently Updated');
      await user.selectOptions(sortSelect, 'Name A-Z');

      // Configurations should be re-ordered (Sherlock comes before Tony alphabetically)
      const cards = screen.getAllByText(/Tony Stark|Sherlock Holmes/);
      expect(cards[0]).toHaveTextContent('Sherlock Holmes');
      expect(cards[1]).toHaveTextContent('Tony Stark');
    });

    it('should show empty state when no configurations match filters', async () => {
      render(<PersonalityManagementDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
      });

      // Search for something that doesn't exist
      const searchInput = screen.getByPlaceholderText('Search personalities...');
      await user.type(searchInput, 'NonExistent');

      expect(screen.getByText('No Personalities Found')).toBeInTheDocument();
      expect(screen.getByText('No personalities match your current filters.')).toBeInTheDocument();
    });
  });

  describe('View Modes', () => {
    it('should switch between grid and list view modes', async () => {
      render(<PersonalityManagementDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
      });

      // Check initial grid view
      const container = document.querySelector('.configurations-container');
      expect(container).toHaveClass('grid');

      // Switch to list view
      const listViewButton = screen.getByTitle('List View');
      await user.click(listViewButton);

      expect(container).toHaveClass('list');

      // Switch back to grid view
      const gridViewButton = screen.getByTitle('Grid View');
      await user.click(gridViewButton);

      expect(container).toHaveClass('grid');
    });
  });

  describe('Detail View Integration', () => {
    it('should open detail view when clicking view button', async () => {
      render(<PersonalityManagementDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
      });

      // Click view details button
      const tonyCard = screen.getByText('Tony Stark').closest('.personality-card');
      const viewButton = within(tonyCard!).getByTitle('View Details');
      
      await user.click(viewButton);

      // Detail view should open
      await waitFor(() => {
        expect(screen.getByText('Communication Style')).toBeInTheDocument();
        expect(screen.getByText('Personality Traits')).toBeInTheDocument();
        expect(screen.getByText('IDE Integration Status')).toBeInTheDocument();
      });
    });

    it('should close detail view when clicking close button', async () => {
      render(<PersonalityManagementDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
      });

      // Open detail view
      const tonyCard = screen.getByText('Tony Stark').closest('.personality-card');
      const viewButton = within(tonyCard!).getByTitle('View Details');
      await user.click(viewButton);

      await waitFor(() => {
        expect(screen.getByText('Communication Style')).toBeInTheDocument();
      });

      // Close detail view
      const closeButton = screen.getByTitle('Close');
      await user.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByText('Communication Style')).not.toBeInTheDocument();
      });
    });
  });

  describe('Edit Form Integration', () => {
    it('should open edit form when clicking edit button', async () => {
      render(<PersonalityManagementDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
      });

      // Click edit button
      const tonyCard = screen.getByText('Tony Stark').closest('.personality-card');
      const editButton = within(tonyCard!).getByTitle('Edit');
      
      await user.click(editButton);

      // Edit form should open
      await waitFor(() => {
        expect(screen.getByText('Edit Personality Configuration')).toBeInTheDocument();
        expect(screen.getByText('Current Configuration')).toBeInTheDocument();
      });
    });

    it('should update configuration through edit form', async () => {
      const updatedConfig = { ...mockConfigurations[0], profile: { ...mockConfigurations[0].profile, name: 'Updated Tony Stark' } };
      vi.mocked(PersonalityApi.updatePersonalityConfig).mockResolvedValue(updatedConfig);

      render(<PersonalityManagementDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
      });

      // Open edit form
      const tonyCard = screen.getByText('Tony Stark').closest('.personality-card');
      const editButton = within(tonyCard!).getByTitle('Edit');
      await user.click(editButton);

      await waitFor(() => {
        expect(screen.getByText('Edit Personality Configuration')).toBeInTheDocument();
      });

      // Update description
      const descriptionInput = screen.getByLabelText(/Personality Description/);
      await user.clear(descriptionInput);
      await user.type(descriptionInput, 'Updated Tony Stark personality');

      // Submit form
      const updateButton = screen.getByText('Update Configuration');
      await user.click(updateButton);

      // Verify API was called
      expect(PersonalityApi.updatePersonalityConfig).toHaveBeenCalledWith('1', {
        description: 'Updated Tony Stark personality',
        project_path: '/cursor/rules'
      });
    });
  });

  describe('Real-time Feedback', () => {
    it('should show operation progress during delete', async () => {
      vi.mocked(window.confirm).mockReturnValue(true);
      
      // Mock a delayed response to see progress indicator
      vi.mocked(PersonalityApi.deletePersonalityConfig).mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      );

      render(<PersonalityManagementDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
      });

      const tonyCard = screen.getByText('Tony Stark').closest('.personality-card');
      const deleteButton = within(tonyCard!).getByTitle('Delete');
      
      await user.click(deleteButton);

      // Should show progress indicator
      await waitFor(() => {
        expect(screen.getByText('Deleting "Tony Stark"...')).toBeInTheDocument();
      });
    });

    it('should show success message after successful operation', async () => {
      render(<PersonalityManagementDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Sherlock Holmes')).toBeInTheDocument();
      });

      // Activate Sherlock Holmes
      const sherlockCard = screen.getByText('Sherlock Holmes').closest('.personality-card');
      const activateButton = within(sherlockCard!).getByTitle('Activate');
      
      await user.click(activateButton);

      await waitFor(() => {
        expect(screen.getByText('Activated "Sherlock Holmes"')).toBeInTheDocument();
      });

      // Success message should disappear after timeout
      await waitFor(() => {
        expect(screen.queryByText('Activated "Sherlock Holmes"')).not.toBeInTheDocument();
      }, { timeout: 4000 });
    });
  });

  describe('Personality Switcher Integration', () => {
    it('should show personality switcher with current active personality', async () => {
      render(<PersonalityManagementDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Quick Switch')).toBeInTheDocument();
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
      });

      // Check that Tony Stark is shown as current in switcher
      const switcherButton = screen.getByTitle('Switch Active Personality');
      expect(within(switcherButton).getByText('Tony Stark')).toBeInTheDocument();
    });

    it('should switch personality through switcher dropdown', async () => {
      render(<PersonalityManagementDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Quick Switch')).toBeInTheDocument();
      });

      // Open switcher dropdown
      const switcherButton = screen.getByTitle('Switch Active Personality');
      await user.click(switcherButton);

      await waitFor(() => {
        expect(screen.getByText('Switch Personality')).toBeInTheDocument();
        expect(screen.getByText('Available Personalities')).toBeInTheDocument();
      });

      // Click on Sherlock Holmes to switch
      const sherlockOption = screen.getByText('Sherlock Holmes').closest('button');
      await user.click(sherlockOption!);

      // Should activate Sherlock Holmes
      await waitFor(() => {
        expect(screen.getByText('Activated "Sherlock Holmes"')).toBeInTheDocument();
      });
    });
  });
});