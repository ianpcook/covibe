/**
 * Integration tests for PersonalitySwitcher component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import PersonalitySwitcher from '../PersonalitySwitcher';
import { PersonalityApi } from '../../services/api';
import { PersonalityConfig } from '../../types/personality';

// Mock the API
vi.mock('../../services/api');

// Sample test data
const mockConfigurations: PersonalityConfig[] = [
  {
    id: '1',
    profile: {
      id: 'profile-1',
      name: 'Tony Stark',
      type: 'fictional',
      traits: [],
      communication_style: {
        tone: 'witty',
        formality: 'casual',
        verbosity: 'moderate',
        technical_level: 'expert'
      },
      mannerisms: [],
      sources: []
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
      traits: [],
      communication_style: {
        tone: 'analytical',
        formality: 'formal',
        verbosity: 'verbose',
        technical_level: 'expert'
      },
      mannerisms: [],
      sources: []
    },
    context: 'You are Sherlock Holmes...',
    ide_type: 'claude',
    file_path: '/project/CLAUDE.md',
    active: false,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  },
  {
    id: '3',
    profile: {
      id: 'profile-3',
      name: 'Einstein',
      type: 'celebrity',
      traits: [],
      communication_style: {
        tone: 'thoughtful',
        formality: 'formal',
        verbosity: 'verbose',
        technical_level: 'expert'
      },
      mannerisms: [],
      sources: []
    },
    context: 'You are Einstein...',
    ide_type: 'vscode',
    file_path: '/project/.vscode/settings.json',
    active: false,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  }
];

describe('PersonalitySwitcher Integration Tests', () => {
  const user = userEvent.setup();
  const mockOnSwitch = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock successful API response
    vi.mocked(PersonalityApi.listPersonalityConfigs).mockResolvedValue({
      configurations: mockConfigurations,
      pagination: {
        total: 3,
        limit: 50,
        offset: 0,
        has_more: false
      }
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Loading and Display', () => {
    it('should show loading state initially', () => {
      render(
        <PersonalitySwitcher
          currentActiveId="1"
          onSwitch={mockOnSwitch}
        />
      );

      expect(screen.getByText('Loading...')).toBeInTheDocument();
      expect(screen.getByRole('button')).toHaveClass('disabled');
    });

    it('should display current active personality', async () => {
      render(
        <PersonalitySwitcher
          currentActiveId="1"
          onSwitch={mockOnSwitch}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
        expect(screen.getByText('⚡ cursor')).toBeInTheDocument();
      });
    });

    it('should display "No Active Personality" when none is active', async () => {
      render(
        <PersonalitySwitcher
          currentActiveId={null}
          onSwitch={mockOnSwitch}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('No Active Personality')).toBeInTheDocument();
        expect(screen.getByText('Click to select')).toBeInTheDocument();
      });
    });

    it('should handle API errors gracefully', async () => {
      vi.mocked(PersonalityApi.listPersonalityConfigs).mockRejectedValue(
        new Error('Network error')
      );

      render(
        <PersonalitySwitcher
          currentActiveId="1"
          onSwitch={mockOnSwitch}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('⚠️ Error')).toBeInTheDocument();
        expect(screen.getByRole('button')).toHaveClass('disabled');
      });
    });
  });

  describe('Dropdown Functionality', () => {
    it('should open and close dropdown when clicking switcher button', async () => {
      render(
        <PersonalitySwitcher
          currentActiveId="1"
          onSwitch={mockOnSwitch}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
      });

      const switcherButton = screen.getByRole('button');
      
      // Open dropdown
      await user.click(switcherButton);

      await waitFor(() => {
        expect(screen.getByText('Switch Personality')).toBeInTheDocument();
        expect(screen.getByText('3 configurations')).toBeInTheDocument();
      });

      // Close dropdown by clicking button again
      await user.click(switcherButton);

      await waitFor(() => {
        expect(screen.queryByText('Switch Personality')).not.toBeInTheDocument();
      });
    });

    it('should close dropdown when clicking outside', async () => {
      render(
        <div>
          <PersonalitySwitcher
            currentActiveId="1"
            onSwitch={mockOnSwitch}
          />
          <div data-testid="outside">Outside element</div>
        </div>
      );

      await waitFor(() => {
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
      });

      // Open dropdown
      const switcherButton = screen.getByRole('button');
      await user.click(switcherButton);

      await waitFor(() => {
        expect(screen.getByText('Switch Personality')).toBeInTheDocument();
      });

      // Click outside
      const outsideElement = screen.getByTestId('outside');
      await user.click(outsideElement);

      await waitFor(() => {
        expect(screen.queryByText('Switch Personality')).not.toBeInTheDocument();
      });
    });

    it('should display current active personality in dropdown', async () => {
      render(
        <PersonalitySwitcher
          currentActiveId="1"
          onSwitch={mockOnSwitch}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
      });

      // Open dropdown
      const switcherButton = screen.getByRole('button');
      await user.click(switcherButton);

      await waitFor(() => {
        expect(screen.getByText('Current Active')).toBeInTheDocument();
        
        // Find the current active section
        const currentSection = screen.getByText('Current Active').closest('.dropdown-section');
        expect(within(currentSection!).getByText('Tony Stark')).toBeInTheDocument();
        expect(within(currentSection!).getByText('✅ Active')).toBeInTheDocument();
      });
    });

    it('should display available personalities for switching', async () => {
      render(
        <PersonalitySwitcher
          currentActiveId="1"
          onSwitch={mockOnSwitch}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
      });

      // Open dropdown
      const switcherButton = screen.getByRole('button');
      await user.click(switcherButton);

      await waitFor(() => {
        expect(screen.getByText('Available Personalities')).toBeInTheDocument();
        
        // Should show Sherlock Holmes and Einstein as available
        expect(screen.getByText('Sherlock Holmes')).toBeInTheDocument();
        expect(screen.getByText('Einstein')).toBeInTheDocument();
        
        // Should show personality types and IDE info
        expect(screen.getByText('fictional • 🤖 claude')).toBeInTheDocument();
        expect(screen.getByText('celebrity • 💻 vscode')).toBeInTheDocument();
      });
    });
  });

  describe('Personality Switching', () => {
    it('should call onSwitch when selecting a different personality', async () => {
      render(
        <PersonalitySwitcher
          currentActiveId="1"
          onSwitch={mockOnSwitch}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
      });

      // Open dropdown
      const switcherButton = screen.getByRole('button');
      await user.click(switcherButton);

      await waitFor(() => {
        expect(screen.getByText('Sherlock Holmes')).toBeInTheDocument();
      });

      // Click on Sherlock Holmes
      const sherlockButton = screen.getByText('Sherlock Holmes').closest('button');
      await user.click(sherlockButton!);

      // Should call onSwitch with Sherlock Holmes config
      expect(mockOnSwitch).toHaveBeenCalledWith(mockConfigurations[1]);
    });

    it('should show hover effects on available personalities', async () => {
      render(
        <PersonalitySwitcher
          currentActiveId="1"
          onSwitch={mockOnSwitch}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
      });

      // Open dropdown
      const switcherButton = screen.getByRole('button');
      await user.click(switcherButton);

      await waitFor(() => {
        expect(screen.getByText('Sherlock Holmes')).toBeInTheDocument();
      });

      // Hover over Sherlock Holmes
      const sherlockButton = screen.getByText('Sherlock Holmes').closest('button');
      await user.hover(sherlockButton!);

      // Should show switch icon on hover
      const switchIcon = within(sherlockButton!).getByText('🔄');
      expect(switchIcon).toBeInTheDocument();
    });

    it('should handle deactivation of current personality', async () => {
      render(
        <PersonalitySwitcher
          currentActiveId="1"
          onSwitch={mockOnSwitch}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
      });

      // Open dropdown
      const switcherButton = screen.getByRole('button');
      await user.click(switcherButton);

      await waitFor(() => {
        expect(screen.getByText('Deactivate Current')).toBeInTheDocument();
      });

      // Click deactivate button
      const deactivateButton = screen.getByText('Deactivate Current');
      await user.click(deactivateButton);

      // Should call onSwitch with deactivated config
      expect(mockOnSwitch).toHaveBeenCalledWith({
        ...mockConfigurations[0],
        active: false
      });
    });
  });

  describe('Empty State', () => {
    it('should show empty state when no configurations exist', async () => {
      vi.mocked(PersonalityApi.listPersonalityConfigs).mockResolvedValue({
        configurations: [],
        pagination: {
          total: 0,
          limit: 50,
          offset: 0,
          has_more: false
        }
      });

      render(
        <PersonalitySwitcher
          currentActiveId={null}
          onSwitch={mockOnSwitch}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('No Active Personality')).toBeInTheDocument();
      });

      // Open dropdown
      const switcherButton = screen.getByRole('button');
      await user.click(switcherButton);

      await waitFor(() => {
        expect(screen.getByText('📝')).toBeInTheDocument();
        expect(screen.getByText('No personality configurations found.')).toBeInTheDocument();
        expect(screen.getByText('Create one to get started!')).toBeInTheDocument();
      });
    });
  });

  describe('Personality Type Icons', () => {
    it('should display correct icons for different personality types', async () => {
      render(
        <PersonalitySwitcher
          currentActiveId="1"
          onSwitch={mockOnSwitch}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
      });

      // Open dropdown
      const switcherButton = screen.getByRole('button');
      await user.click(switcherButton);

      await waitFor(() => {
        // Check fictional character icon (Tony Stark and Sherlock Holmes)
        const tonySection = screen.getByText('Tony Stark').closest('.personality-item');
        expect(within(tonySection!).getByText('📚')).toBeInTheDocument();

        const sherlockSection = screen.getByText('Sherlock Holmes').closest('.personality-item');
        expect(within(sherlockSection!).getByText('📚')).toBeInTheDocument();

        // Check celebrity icon (Einstein)
        const einsteinSection = screen.getByText('Einstein').closest('.personality-item');
        expect(within(einsteinSection!).getByText('⭐')).toBeInTheDocument();
      });
    });
  });

  describe('IDE Type Icons', () => {
    it('should display correct icons for different IDE types', async () => {
      render(
        <PersonalitySwitcher
          currentActiveId="1"
          onSwitch={mockOnSwitch}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('⚡ cursor')).toBeInTheDocument();
      });

      // Open dropdown
      const switcherButton = screen.getByRole('button');
      await user.click(switcherButton);

      await waitFor(() => {
        // Check different IDE icons
        expect(screen.getByText('🤖 claude')).toBeInTheDocument(); // Sherlock Holmes
        expect(screen.getByText('💻 vscode')).toBeInTheDocument(); // Einstein
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes', async () => {
      render(
        <PersonalitySwitcher
          currentActiveId="1"
          onSwitch={mockOnSwitch}
        />
      );

      await waitFor(() => {
        const switcherButton = screen.getByRole('button');
        expect(switcherButton).toHaveAttribute('title', 'Switch Active Personality');
      });
    });

    it('should support keyboard navigation', async () => {
      render(
        <PersonalitySwitcher
          currentActiveId="1"
          onSwitch={mockOnSwitch}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Tony Stark')).toBeInTheDocument();
      });

      // Focus and activate with keyboard
      const switcherButton = screen.getByRole('button');
      switcherButton.focus();
      
      // Press Enter to open dropdown
      fireEvent.keyDown(switcherButton, { key: 'Enter', code: 'Enter' });

      await waitFor(() => {
        expect(screen.getByText('Switch Personality')).toBeInTheDocument();
      });
    });
  });

  describe('Custom CSS Classes', () => {
    it('should apply custom className prop', async () => {
      const { container } = render(
        <PersonalitySwitcher
          currentActiveId="1"
          onSwitch={mockOnSwitch}
          className="custom-switcher"
        />
      );

      await waitFor(() => {
        const switcher = container.querySelector('.personality-switcher');
        expect(switcher).toHaveClass('custom-switcher');
      });
    });
  });
});