/**
 * Tests for PersonalityExportInterface component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import PersonalityExportInterface from '../PersonalityExportInterface';
import PersonalityApi from '../../services/api';
import { PersonalityConfig } from '../../types/personality';

// Mock the API
vi.mock('../../services/api', () => ({
  default: {
    getSupportedIDETypes: vi.fn(),
    exportPersonalityConfig: vi.fn(),
  },
}));

const mockPersonalityConfig: PersonalityConfig = {
  id: 'test-123',
  profile: {
    id: 'profile-123',
    name: 'Tony Stark',
    type: 'fictional',
    traits: [
      { category: 'intelligence', trait: 'genius', intensity: 10, examples: ['Invents arc reactor'] }
    ],
    communication_style: {
      tone: 'witty',
      formality: 'casual',
      verbosity: 'concise',
      technical_level: 'expert'
    },
    mannerisms: ['Sarcastic quips', 'Technical jargon'],
    sources: []
  },
  context: 'Test context',
  ide_type: 'cursor',
  file_path: '/test/path',
  active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z'
};

const mockSupportedIDEs = {
  supported_ides: [
    { type: 'cursor', name: 'Cursor', description: 'AI code editor', file_extension: '.mdc', supports_metadata: true },
    { type: 'claude', name: 'Claude', description: 'Claude AI', file_extension: '.md', supports_metadata: true },
    { type: 'windsurf', name: 'Windsurf', description: 'Next-gen IDE', file_extension: '.json', supports_metadata: true },
    { type: 'generic', name: 'Generic', description: 'Universal format', file_extension: '.md', supports_metadata: false },
  ],
  total_count: 4
};

describe('PersonalityExportInterface', () => {
  const mockOnExportComplete = vi.fn();
  const mockOnError = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (PersonalityApi.getSupportedIDETypes as any).mockResolvedValue(mockSupportedIDEs);
  });

  it('renders export interface correctly', async () => {
    render(
      <PersonalityExportInterface
        personalityConfig={mockPersonalityConfig}
        onExportComplete={mockOnExportComplete}
        onError={mockOnError}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Export Configuration')).toBeInTheDocument();
      expect(screen.getByText(`Export "Tony Stark" for use in your IDE`)).toBeInTheDocument();
      expect(screen.getByLabelText('Target IDE:')).toBeInTheDocument();
      expect(screen.getByText('Export & Download')).toBeInTheDocument();
    });
  });

  it('loads supported IDE types on mount', async () => {
    render(
      <PersonalityExportInterface
        personalityConfig={mockPersonalityConfig}
        onExportComplete={mockOnExportComplete}
        onError={mockOnError}
      />
    );

    await waitFor(() => {
      expect(PersonalityApi.getSupportedIDETypes).toHaveBeenCalledTimes(1);
    });

    // Check if IDE options are rendered
    expect(screen.getByDisplayValue('cursor')).toBeInTheDocument();
  });

  it('handles IDE selection changes', async () => {
    const user = userEvent.setup();
    render(
      <PersonalityExportInterface
        personalityConfig={mockPersonalityConfig}
        onExportComplete={mockOnExportComplete}
        onError={mockOnError}
      />
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Target IDE:')).toBeInTheDocument();
    });

    const selectElement = screen.getByLabelText('Target IDE:');
    await user.selectOptions(selectElement, 'claude');

    expect(selectElement).toHaveValue('claude');
  });

  it('handles format option changes', async () => {
    const user = userEvent.setup();
    render(
      <PersonalityExportInterface
        personalityConfig={mockPersonalityConfig}
        onExportComplete={mockOnExportComplete}
        onError={mockOnError}
      />
    );

    await waitFor(() => {
      expect(screen.getByLabelText(/include metadata/i)).toBeInTheDocument();
    });

    const metadataCheckbox = screen.getByLabelText(/include metadata/i);
    expect(metadataCheckbox).toBeChecked();

    await user.click(metadataCheckbox);
    expect(metadataCheckbox).not.toBeChecked();
  });

  it('handles successful export', async () => {
    const mockBlob = new Blob(['test content'], { type: 'text/plain' });
    (PersonalityApi.exportPersonalityConfig as any).mockResolvedValue(mockBlob);

    // Mock URL.createObjectURL and document methods
    const mockCreateObjectURL = vi.fn(() => 'mock-url');
    const mockRevokeObjectURL = vi.fn();
    Object.defineProperty(window.URL, 'createObjectURL', { value: mockCreateObjectURL });
    Object.defineProperty(window.URL, 'revokeObjectURL', { value: mockRevokeObjectURL });

    const mockLink = {
      click: vi.fn(),
      setAttribute: vi.fn(),
      style: {}
    };
    const mockCreateElement = vi.fn(() => mockLink);
    const mockAppendChild = vi.fn();
    const mockRemoveChild = vi.fn();
    
    Object.defineProperty(document, 'createElement', { value: mockCreateElement });
    Object.defineProperty(document.body, 'appendChild', { value: mockAppendChild });
    Object.defineProperty(document.body, 'removeChild', { value: mockRemoveChild });

    const user = userEvent.setup();
    render(
      <PersonalityExportInterface
        personalityConfig={mockPersonalityConfig}
        onExportComplete={mockOnExportComplete}
        onError={mockOnError}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Export & Download')).toBeInTheDocument();
    });

    const exportButton = screen.getByText('Export & Download');
    await user.click(exportButton);

    await waitFor(() => {
      expect(PersonalityApi.exportPersonalityConfig).toHaveBeenCalledWith(
        'test-123',
        'cursor',
        expect.objectContaining({
          include_metadata: true,
          include_instructions: true,
          preserve_comments: true
        })
      );
    });

    await waitFor(() => {
      expect(mockOnExportComplete).toHaveBeenCalledWith(true, expect.any(String));
    });
  });

  it('handles export error', async () => {
    const mockError = new Error('Export failed');
    (PersonalityApi.exportPersonalityConfig as any).mockRejectedValue(mockError);

    const user = userEvent.setup();
    render(
      <PersonalityExportInterface
        personalityConfig={mockPersonalityConfig}
        onExportComplete={mockOnExportComplete}
        onError={mockOnError}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Export & Download')).toBeInTheDocument();
    });

    const exportButton = screen.getByText('Export & Download');
    await user.click(exportButton);

    await waitFor(() => {
      expect(mockOnError).toHaveBeenCalledWith('Export failed');
    });
  });

  it('shows progress during export', async () => {
    let resolveExport: (value: Blob) => void;
    const exportPromise = new Promise<Blob>((resolve) => {
      resolveExport = resolve;
    });
    (PersonalityApi.exportPersonalityConfig as any).mockReturnValue(exportPromise);

    const user = userEvent.setup();
    render(
      <PersonalityExportInterface
        personalityConfig={mockPersonalityConfig}
        onExportComplete={mockOnExportComplete}
        onError={mockOnError}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Export & Download')).toBeInTheDocument();
    });

    const exportButton = screen.getByText('Export & Download');
    await user.click(exportButton);

    // Should show progress
    expect(screen.getByText('Exporting...')).toBeInTheDocument();
    expect(screen.getByText(/Preparing export/i)).toBeInTheDocument();

    // Resolve the export
    resolveExport!(new Blob(['test'], { type: 'text/plain' }));

    await waitFor(() => {
      expect(screen.getByText('Export completed successfully!')).toBeInTheDocument();
    });
  });

  it('disables controls during export', async () => {
    let resolveExport: (value: Blob) => void;
    const exportPromise = new Promise<Blob>((resolve) => {
      resolveExport = resolve;
    });
    (PersonalityApi.exportPersonalityConfig as any).mockReturnValue(exportPromise);

    const user = userEvent.setup();
    render(
      <PersonalityExportInterface
        personalityConfig={mockPersonalityConfig}
        onExportComplete={mockOnExportComplete}
        onError={mockOnError}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Export & Download')).toBeInTheDocument();
    });

    const exportButton = screen.getByText('Export & Download');
    const ideSelect = screen.getByLabelText('Target IDE:');
    
    await user.click(exportButton);

    // Should disable controls during export
    expect(exportButton).toBeDisabled();
    expect(ideSelect).toBeDisabled();

    // Complete the export
    resolveExport!(new Blob(['test'], { type: 'text/plain' }));
  });

  it('handles custom filename input', async () => {
    const user = userEvent.setup();
    render(
      <PersonalityExportInterface
        personalityConfig={mockPersonalityConfig}
        onExportComplete={mockOnExportComplete}
        onError={mockOnError}
      />
    );

    await waitFor(() => {
      expect(screen.getByLabelText(/custom filename/i)).toBeInTheDocument();
    });

    const filenameInput = screen.getByLabelText(/custom filename/i);
    await user.type(filenameInput, 'my-custom-name.mdc');

    expect(filenameInput).toHaveValue('my-custom-name.mdc');
  });

  it('opens preview modal when preview button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <PersonalityExportInterface
        personalityConfig={mockPersonalityConfig}
        onExportComplete={mockOnExportComplete}
        onError={mockOnError}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Preview')).toBeInTheDocument();
    });

    const previewButton = screen.getByText('Preview');
    await user.click(previewButton);

    // Should render ExportPreview component (we check for the props being passed)
    expect(screen.getByText('Preview functionality will be implemented in ExportPreview component')).toBeInTheDocument();
  });
});