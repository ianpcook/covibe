/**
 * Tests for BulkExportManager component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import BulkExportManager from '../BulkExportManager';
import PersonalityApi from '../../services/api';
import { PersonalityConfig } from '../../types/personality';

// Mock the API
vi.mock('../../services/api', () => ({
  default: {
    bulkExportPersonalities: vi.fn(),
  },
}));

const mockConfigs: PersonalityConfig[] = [
  {
    id: 'config-1',
    profile: {
      id: 'profile-1',
      name: 'Tony Stark',
      type: 'fictional',
      traits: [],
      communication_style: { tone: 'witty', formality: 'casual', verbosity: 'concise', technical_level: 'expert' },
      mannerisms: [],
      sources: []
    },
    context: 'Test context 1',
    ide_type: 'cursor',
    file_path: '/test/path1',
    active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  },
  {
    id: 'config-2', 
    profile: {
      id: 'profile-2',
      name: 'Yoda',
      type: 'fictional',
      traits: [],
      communication_style: { tone: 'wise', formality: 'mixed', verbosity: 'concise', technical_level: 'expert' },
      mannerisms: [],
      sources: []
    },
    context: 'Test context 2',
    ide_type: 'claude',
    file_path: '/test/path2',
    active: false,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  }
];

describe('BulkExportManager', () => {
  const mockOnClose = vi.fn();
  const mockOnExportComplete = vi.fn();
  const mockOnError = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders bulk export manager correctly', () => {
    render(
      <BulkExportManager
        availableConfigs={mockConfigs}
        onClose={mockOnClose}
        onExportComplete={mockOnExportComplete}
        onError={mockOnError}
      />
    );

    expect(screen.getByText('Bulk Export Manager')).toBeInTheDocument();
    expect(screen.getByText('Export multiple personality configurations at once')).toBeInTheDocument();
    expect(screen.getByText('Select Configurations (0/2)')).toBeInTheDocument();
    expect(screen.getByText('Target IDE Types (1/4)')).toBeInTheDocument();
  });

  it('displays available configurations', () => {
    render(
      <BulkExportManager
        availableConfigs={mockConfigs}
        onClose={mockOnClose}
        onExportComplete={mockOnExportComplete}
        onError={mockOnError}
      />
    );

    expect(screen.getByText('Tony Stark')).toBeInTheDocument();
    expect(screen.getByText('Yoda')).toBeInTheDocument();
    expect(screen.getByText('fictional • cursor • Active')).toBeInTheDocument();
    expect(screen.getByText('fictional • claude • Inactive')).toBeInTheDocument();
  });

  it('handles configuration selection', async () => {
    const user = userEvent.setup();
    render(
      <BulkExportManager
        availableConfigs={mockConfigs}
        onClose={mockOnClose}
        onExportComplete={mockOnExportComplete}
        onError={mockOnError}
      />
    );

    const tonyCheckbox = screen.getByLabelText(/Tony Stark/);
    await user.click(tonyCheckbox);

    expect(screen.getByText('Select Configurations (1/2)')).toBeInTheDocument();
    expect(tonyCheckbox).toBeChecked();
  });

  it('handles select all/deselect all functionality', async () => {
    const user = userEvent.setup();
    render(
      <BulkExportManager
        availableConfigs={mockConfigs}
        onClose={mockOnClose}
        onExportComplete={mockOnExportComplete}
        onError={mockOnError}
      />
    );

    const selectAllButton = screen.getByText('Select All');
    await user.click(selectAllButton);

    expect(screen.getByText('Select Configurations (2/2)')).toBeInTheDocument();
    expect(screen.getByText('Deselect All')).toBeInTheDocument();

    await user.click(screen.getByText('Deselect All'));
    expect(screen.getByText('Select Configurations (0/2)')).toBeInTheDocument();
  });

  it('handles IDE type selection', async () => {
    const user = userEvent.setup();
    render(
      <BulkExportManager
        availableConfigs={mockConfigs}
        onClose={mockOnClose}
        onExportComplete={mockOnExportComplete}
        onError={mockOnError}
      />
    );

    // Cursor should be selected by default
    expect(screen.getByText('Target IDE Types (1/4)')).toBeInTheDocument();

    const claudeCheckbox = screen.getByLabelText(/Claude/);
    await user.click(claudeCheckbox);

    expect(screen.getByText('Target IDE Types (2/4)')).toBeInTheDocument();
  });

  it('handles export options changes', async () => {
    const user = userEvent.setup();
    render(
      <BulkExportManager
        availableConfigs={mockConfigs}
        onClose={mockOnClose}
        onExportComplete={mockOnExportComplete}
        onError={mockOnError}
      />
    );

    const metadataCheckbox = screen.getByLabelText(/include metadata/i);
    expect(metadataCheckbox).toBeChecked();

    await user.click(metadataCheckbox);
    expect(metadataCheckbox).not.toBeChecked();

    const readmeCheckbox = screen.getByLabelText(/include readme/i);
    expect(readmeCheckbox).toBeChecked();

    await user.click(readmeCheckbox);
    expect(readmeCheckbox).not.toBeChecked();
  });

  it('shows export summary when selections are made', async () => {
    const user = userEvent.setup();
    render(
      <BulkExportManager
        availableConfigs={mockConfigs}
        onClose={mockOnClose}
        onExportComplete={mockOnExportComplete}
        onError={mockOnError}
      />
    );

    // Select a configuration and an additional IDE type
    const tonyCheckbox = screen.getByLabelText(/Tony Stark/);
    await user.click(tonyCheckbox);

    const claudeCheckbox = screen.getByLabelText(/Claude/);
    await user.click(claudeCheckbox);

    expect(screen.getByText('Ready to export 1 configuration(s) for 2 IDE type(s)')).toBeInTheDocument();
  });

  it('validates selections before export', async () => {
    const user = userEvent.setup();
    render(
      <BulkExportManager
        availableConfigs={mockConfigs}
        onClose={mockOnClose}
        onExportComplete={mockOnExportComplete}
        onError={mockOnError}
      />
    );

    // Try to export with no configurations selected
    const exportButton = screen.getByText('Export & Download');
    await user.click(exportButton);

    expect(mockOnError).toHaveBeenCalledWith('Please select at least one configuration to export');
  });

  it('handles successful bulk export', async () => {
    const mockBlob = new Blob(['test zip content'], { type: 'application/zip' });
    (PersonalityApi.bulkExportPersonalities as any).mockResolvedValue(mockBlob);

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
      <BulkExportManager
        availableConfigs={mockConfigs}
        onClose={mockOnClose}
        onExportComplete={mockOnExportComplete}
        onError={mockOnError}
      />
    );

    // Select a configuration
    const tonyCheckbox = screen.getByLabelText(/Tony Stark/);
    await user.click(tonyCheckbox);

    const exportButton = screen.getByText('Export & Download');
    await user.click(exportButton);

    await waitFor(() => {
      expect(PersonalityApi.bulkExportPersonalities).toHaveBeenCalledWith(
        expect.objectContaining({
          personality_ids: ['config-1'],
          ide_types: ['cursor'],
          format_options: expect.objectContaining({
            include_metadata: true,
            include_instructions: true,
            preserve_comments: true
          }),
          include_readme: true
        })
      );
    });

    await waitFor(() => {
      expect(mockOnExportComplete).toHaveBeenCalledWith(true, expect.stringContaining('.zip'));
    }, { timeout: 2000 });
  });

  it('handles bulk export error', async () => {
    const mockError = new Error('Bulk export failed');
    (PersonalityApi.bulkExportPersonalities as any).mockRejectedValue(mockError);

    const user = userEvent.setup();
    render(
      <BulkExportManager
        availableConfigs={mockConfigs}
        onClose={mockOnClose}
        onExportComplete={mockOnExportComplete}
        onError={mockOnError}
      />
    );

    // Select a configuration
    const tonyCheckbox = screen.getByLabelText(/Tony Stark/);
    await user.click(tonyCheckbox);

    const exportButton = screen.getByText('Export & Download');
    await user.click(exportButton);

    await waitFor(() => {
      expect(mockOnError).toHaveBeenCalledWith('Bulk export failed');
    });
  });

  it('shows progress during bulk export', async () => {
    let resolveBulkExport: (value: Blob) => void;
    const bulkExportPromise = new Promise<Blob>((resolve) => {
      resolveBulkExport = resolve;
    });
    (PersonalityApi.bulkExportPersonalities as any).mockReturnValue(bulkExportPromise);

    const user = userEvent.setup();
    render(
      <BulkExportManager
        availableConfigs={mockConfigs}
        onClose={mockOnClose}
        onExportComplete={mockOnExportComplete}
        onError={mockOnError}
      />
    );

    // Select a configuration
    const tonyCheckbox = screen.getByLabelText(/Tony Stark/);
    await user.click(tonyCheckbox);

    const exportButton = screen.getByText('Export & Download');
    await user.click(exportButton);

    // Should show progress
    expect(screen.getByText('Exporting...')).toBeInTheDocument();
    expect(screen.getByText(/Preparing bulk export/i)).toBeInTheDocument();

    // Resolve the export
    resolveBulkExport!(new Blob(['test'], { type: 'application/zip' }));

    await waitFor(() => {
      expect(screen.getByText('Export completed!')).toBeInTheDocument();
    });
  });

  it('disables controls during export', async () => {
    let resolveBulkExport: (value: Blob) => void;
    const bulkExportPromise = new Promise<Blob>((resolve) => {
      resolveBulkExport = resolve;
    });
    (PersonalityApi.bulkExportPersonalities as any).mockReturnValue(bulkExportPromise);

    const user = userEvent.setup();
    render(
      <BulkExportManager
        availableConfigs={mockConfigs}
        onClose={mockOnClose}
        onExportComplete={mockOnExportComplete}
        onError={mockOnError}
      />
    );

    // Select a configuration
    const tonyCheckbox = screen.getByLabelText(/Tony Stark/);
    await user.click(tonyCheckbox);

    const exportButton = screen.getByText('Export & Download');
    const cancelButton = screen.getByText('Cancel');
    
    await user.click(exportButton);

    // Should disable controls during export
    expect(exportButton).toBeDisabled();
    expect(cancelButton).toBeDisabled();
    expect(tonyCheckbox).toBeDisabled();

    // Complete the export
    resolveBulkExport!(new Blob(['test'], { type: 'application/zip' }));
  });

  it('closes modal when cancel is clicked', async () => {
    const user = userEvent.setup();
    render(
      <BulkExportManager
        availableConfigs={mockConfigs}
        onClose={mockOnClose}
        onExportComplete={mockOnExportComplete}
        onError={mockOnError}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    await user.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('handles empty configurations list', () => {
    render(
      <BulkExportManager
        availableConfigs={[]}
        onClose={mockOnClose}
        onExportComplete={mockOnExportComplete}
        onError={mockOnError}
      />
    );

    expect(screen.getByText('Select Configurations (0/0)')).toBeInTheDocument();
    expect(screen.getByText('Export & Download')).toBeDisabled();
  });
});