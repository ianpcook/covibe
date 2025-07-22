/**
 * Tests for export-related API methods
 */

import { vi } from 'vitest';
import PersonalityApi from '../api';
import { BulkExportRequest, ExportFormatOptions } from '../../types/personality';

// Mock axios
vi.mock('axios', () => ({
  create: () => ({
    get: vi.fn(),
    post: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() }
    }
  }),
  default: {
    create: () => ({
      get: vi.fn(),
      post: vi.fn(),
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() }
      }
    })
  }
}));

describe('PersonalityApi Export Methods', () => {
  let mockApiClient: any;

  beforeEach(() => {
    vi.clearAllMocks();
    // Get the mocked axios instance
    const axios = require('axios');
    mockApiClient = axios.create();
  });

  describe('exportPersonalityConfig', () => {
    it('exports personality config with basic parameters', async () => {
      const mockBlob = new Blob(['test content'], { type: 'text/plain' });
      mockApiClient.get.mockResolvedValue({ data: mockBlob });

      const result = await PersonalityApi.exportPersonalityConfig('test-id', 'cursor');

      expect(mockApiClient.get).toHaveBeenCalledWith(
        '/api/personality/test-id/export/cursor?',
        { responseType: 'blob' }
      );
      expect(result).toBe(mockBlob);
    });

    it('exports personality config with format options', async () => {
      const mockBlob = new Blob(['test content'], { type: 'text/plain' });
      mockApiClient.get.mockResolvedValue({ data: mockBlob });

      const formatOptions: ExportFormatOptions = {
        file_name: 'custom-file.mdc',
        include_metadata: false,
        include_instructions: true,
        custom_header: 'My custom header',
        preserve_comments: false
      };

      await PersonalityApi.exportPersonalityConfig('test-id', 'cursor', formatOptions);

      expect(mockApiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('file_name=custom-file.mdc'),
        { responseType: 'blob' }
      );
      expect(mockApiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('include_metadata=false'),
        { responseType: 'blob' }
      );
      expect(mockApiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('include_instructions=true'),
        { responseType: 'blob' }
      );
      expect(mockApiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('custom_header=My%20custom%20header'),
        { responseType: 'blob' }
      );
      expect(mockApiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('preserve_comments=false'),
        { responseType: 'blob' }
      );
    });

    it('handles export errors', async () => {
      const mockError = {
        response: {
          data: {
            error: {
              code: 'EXPORT_FAILED',
              message: 'Export failed',
              suggestions: ['Try again']
            },
            request_id: 'test-123',
            timestamp: '2024-01-01T00:00:00Z'
          },
          status: 500
        }
      };
      mockApiClient.get.mockRejectedValue(mockError);

      await expect(
        PersonalityApi.exportPersonalityConfig('test-id', 'cursor')
      ).rejects.toThrow();
    });
  });

  describe('previewPersonalityExport', () => {
    it('previews personality export', async () => {
      const mockPreviewResult = {
        success: true,
        content: 'Preview content',
        file_name: 'test.mdc',
        file_size: 100,
        syntax_language: 'markdown',
        placement_instructions: ['Step 1', 'Step 2'],
        metadata: { version: '1.0' }
      };
      mockApiClient.get.mockResolvedValue({ data: mockPreviewResult });

      const result = await PersonalityApi.previewPersonalityExport('test-id', 'cursor');

      expect(mockApiClient.get).toHaveBeenCalledWith(
        '/api/personality/test-id/export/cursor/preview',
        expect.objectContaining({
          params: expect.any(Object)
        })
      );
      expect(result).toEqual(mockPreviewResult);
    });

    it('previews with format options', async () => {
      const mockPreviewResult = {
        success: true,
        content: 'Preview content',
        file_name: 'test.mdc',
        file_size: 100,
        syntax_language: 'markdown',
        placement_instructions: [],
        metadata: {}
      };
      mockApiClient.get.mockResolvedValue({ data: mockPreviewResult });

      const formatOptions: ExportFormatOptions = {
        file_name: 'preview-test.mdc',
        include_metadata: true
      };

      await PersonalityApi.previewPersonalityExport('test-id', 'cursor', formatOptions);

      expect(mockApiClient.get).toHaveBeenCalledWith(
        '/api/personality/test-id/export/cursor/preview',
        expect.objectContaining({
          params: expect.objectContaining({
            file_name: 'preview-test.mdc',
            include_metadata: true
          })
        })
      );
    });
  });

  describe('getSupportedIDETypes', () => {
    it('gets supported IDE types', async () => {
      const mockResponse = {
        supported_ides: [
          {
            type: 'cursor',
            name: 'Cursor IDE',
            description: 'AI-powered code editor',
            file_extension: '.mdc',
            supports_metadata: true
          },
          {
            type: 'claude',
            name: 'Claude',
            description: 'Claude AI assistant',
            file_extension: '.md',
            supports_metadata: true
          }
        ],
        total_count: 2
      };
      mockApiClient.get.mockResolvedValue({ data: mockResponse });

      const result = await PersonalityApi.getSupportedIDETypes();

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/personality/export/supported-ides');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('bulkExportPersonalities', () => {
    it('performs bulk export', async () => {
      const mockBlob = new Blob(['zip content'], { type: 'application/zip' });
      mockApiClient.post.mockResolvedValue({ data: mockBlob });

      const bulkRequest: BulkExportRequest = {
        personality_ids: ['id1', 'id2'],
        ide_types: ['cursor', 'claude'],
        format_options: {
          include_metadata: true,
          include_instructions: true
        },
        include_readme: true
      };

      const result = await PersonalityApi.bulkExportPersonalities(bulkRequest);

      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/api/personality/export/bulk',
        bulkRequest,
        { responseType: 'blob' }
      );
      expect(result).toBe(mockBlob);
    });

    it('handles bulk export errors', async () => {
      const mockError = {
        response: {
          data: {
            error: {
              code: 'BULK_EXPORT_FAILED',
              message: 'Bulk export failed',
              suggestions: ['Try with fewer configurations']
            },
            request_id: 'test-123',
            timestamp: '2024-01-01T00:00:00Z'
          },
          status: 500
        }
      };
      mockApiClient.post.mockRejectedValue(mockError);

      const bulkRequest: BulkExportRequest = {
        personality_ids: ['id1'],
        ide_types: ['cursor'],
        include_readme: true
      };

      await expect(
        PersonalityApi.bulkExportPersonalities(bulkRequest)
      ).rejects.toThrow();
    });
  });

  describe('importPersonalityConfig', () => {
    it('imports personality config from file', async () => {
      const mockConfig = {
        id: 'imported-123',
        profile: { name: 'Imported Personality' },
        context: 'Imported context',
        ide_type: 'cursor',
        file_path: '/imported/path',
        active: false,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      };
      mockApiClient.post.mockResolvedValue({ data: mockConfig });

      const mockFile = new File(['test content'], 'test.mdc', { type: 'text/plain' });
      
      const result = await PersonalityApi.importPersonalityConfig(mockFile, 'user-123');

      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/api/personality/import',
        expect.any(FormData),
        expect.objectContaining({
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
      );
      expect(result).toEqual(mockConfig);
    });

    it('imports without user ID', async () => {
      const mockConfig = {
        id: 'imported-123',
        profile: { name: 'Imported Personality' },
        context: 'Imported context',
        ide_type: 'cursor',
        file_path: '/imported/path',
        active: false,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      };
      mockApiClient.post.mockResolvedValue({ data: mockConfig });

      const mockFile = new File(['test content'], 'test.mdc', { type: 'text/plain' });
      
      await PersonalityApi.importPersonalityConfig(mockFile);

      const [, formData] = mockApiClient.post.mock.calls[0];
      expect(formData.has('user_id')).toBe(false);
    });
  });

  describe('validateImportFile', () => {
    it('validates import file', async () => {
      const mockValidationResult = {
        valid: true,
        detected_format: 'cursor',
        ide_type: 'cursor',
        confidence: 0.95,
        errors: [],
        warnings: ['Minor formatting issue']
      };
      mockApiClient.post.mockResolvedValue({ data: mockValidationResult });

      const mockFile = new File(['test content'], 'test.mdc', { type: 'text/plain' });
      
      const result = await PersonalityApi.validateImportFile(mockFile);

      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/api/personality/import/validate',
        expect.any(FormData),
        expect.objectContaining({
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
      );
      expect(result).toEqual(mockValidationResult);
    });

    it('handles validation errors', async () => {
      const mockValidationResult = {
        valid: false,
        detected_format: 'unknown',
        ide_type: 'unknown',
        confidence: 0.1,
        errors: ['Invalid file format', 'Missing required fields'],
        warnings: []
      };
      mockApiClient.post.mockResolvedValue({ data: mockValidationResult });

      const mockFile = new File(['invalid content'], 'test.txt', { type: 'text/plain' });
      
      const result = await PersonalityApi.validateImportFile(mockFile);

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Invalid file format');
    });
  });
});