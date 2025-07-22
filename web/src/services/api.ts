/**
 * API client for personality system backend
 */

import axios, { AxiosResponse } from 'axios';
import { 
  PersonalityConfig, 
  PersonalityRequest, 
  ResearchResult, 
  ApiError,
  ExportResult,
  PreviewResult,
  BulkExportRequest,
  BulkExportResult,
  ExportFormatOptions,
  SupportedIDEType
} from '../types/personality';

// Configure axios defaults
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export class PersonalityApiError extends Error {
  public apiError: ApiError;
  public status: number;

  constructor(apiError: ApiError, status: number) {
    super(apiError.error.message);
    this.apiError = apiError;
    this.status = status;
    this.name = 'PersonalityApiError';
  }
}

/**
 * API service for personality operations
 */
export class PersonalityApi {
  /**
   * Create a new personality configuration
   */
  static async createPersonalityConfig(request: PersonalityRequest): Promise<PersonalityConfig> {
    try {
      const response: AxiosResponse<PersonalityConfig> = await apiClient.post(
        '/api/personality/',
        request
      );
      return response.data;
    } catch (error: any) {
      if (error.response?.data) {
        throw new PersonalityApiError(error.response.data, error.response.status);
      }
      throw error;
    }
  }

  /**
   * Get a personality configuration by ID
   */
  static async getPersonalityConfig(id: string): Promise<PersonalityConfig> {
    try {
      const response: AxiosResponse<PersonalityConfig> = await apiClient.get(
        `/api/personality/${id}`
      );
      return response.data;
    } catch (error: any) {
      if (error.response?.data) {
        throw new PersonalityApiError(error.response.data, error.response.status);
      }
      throw error;
    }
  }

  /**
   * Update a personality configuration
   */
  static async updatePersonalityConfig(
    id: string,
    updates: Partial<PersonalityRequest>
  ): Promise<PersonalityConfig> {
    try {
      const response: AxiosResponse<PersonalityConfig> = await apiClient.put(
        `/api/personality/${id}`,
        updates
      );
      return response.data;
    } catch (error: any) {
      if (error.response?.data) {
        throw new PersonalityApiError(error.response.data, error.response.status);
      }
      throw error;
    }
  }

  /**
   * Delete a personality configuration
   */
  static async deletePersonalityConfig(id: string): Promise<void> {
    try {
      await apiClient.delete(`/api/personality/${id}`);
    } catch (error: any) {
      if (error.response?.data) {
        throw new PersonalityApiError(error.response.data, error.response.status);
      }
      throw error;
    }
  }

  /**
   * Research a personality without creating a full configuration
   */
  static async researchPersonality(
    description: string,
    useCache: boolean = true
  ): Promise<ResearchResult> {
    try {
      const response: AxiosResponse<ResearchResult> = await apiClient.post(
        '/api/personality/research',
        {
          description,
          use_cache: useCache,
        }
      );
      return response.data;
    } catch (error: any) {
      if (error.response?.data) {
        throw new PersonalityApiError(error.response.data, error.response.status);
      }
      throw error;
    }
  }

  /**
   * List personality configurations with pagination
   */
  static async listPersonalityConfigs(
    limit: number = 10,
    offset: number = 0
  ): Promise<{
    configurations: PersonalityConfig[];
    pagination: {
      total: number;
      limit: number;
      offset: number;
      has_more: boolean;
    };
  }> {
    try {
      const response = await apiClient.get('/api/personality/configs', {
        params: { limit, offset },
      });
      return response.data;
    } catch (error: any) {
      if (error.response?.data) {
        throw new PersonalityApiError(error.response.data, error.response.status);
      }
      throw error;
    }
  }

  /**
   * Detect IDE environment
   */
  static async detectIdeEnvironment(projectPath: string): Promise<{
    project_path: string;
    detected_ides: Array<{
      name: string;
      type: string;
      config_path: string;
      confidence: number;
      markers: string[];
    }>;
    primary_ide: {
      name: string;
      type: string;
      config_path: string;
      confidence: number;
      markers: string[];
    } | null;
    total_detected: number;
  }> {
    try {
      const response = await apiClient.get('/api/personality/ide/detect', {
        params: { project_path: projectPath },
      });
      return response.data;
    } catch (error: any) {
      if (error.response?.data) {
        throw new PersonalityApiError(error.response.data, error.response.status);
      }
      throw error;
    }
  }

  /**
   * Get cache statistics
   */
  static async getCacheStats(): Promise<{
    cache_stats: {
      total_entries: number;
      expired_entries: number;
      active_entries: number;
    };
    timestamp: string;
  }> {
    try {
      const response = await apiClient.get('/api/personality/cache/stats');
      return response.data;
    } catch (error: any) {
      if (error.response?.data) {
        throw new PersonalityApiError(error.response.data, error.response.status);
      }
      throw error;
    }
  }

  /**
   * Clear cache
   */
  static async clearCache(clearAll: boolean = false): Promise<{
    cleared_entries: number;
    clear_type: string;
    timestamp: string;
  }> {
    try {
      const response = await apiClient.delete('/api/personality/cache', {
        params: { clear_all: clearAll },
      });
      return response.data;
    } catch (error: any) {
      if (error.response?.data) {
        throw new PersonalityApiError(error.response.data, error.response.status);
      }
      throw error;
    }
  }

  // Export-related methods

  /**
   * Export personality configuration as downloadable file
   */
  static async exportPersonalityConfig(
    personalityId: string,
    ideType: SupportedIDEType,
    formatOptions?: ExportFormatOptions
  ): Promise<Blob> {
    try {
      const params = new URLSearchParams();
      if (formatOptions?.file_name) params.set('file_name', formatOptions.file_name);
      if (formatOptions?.include_metadata !== undefined) params.set('include_metadata', formatOptions.include_metadata.toString());
      if (formatOptions?.include_instructions !== undefined) params.set('include_instructions', formatOptions.include_instructions.toString());
      if (formatOptions?.custom_header) params.set('custom_header', formatOptions.custom_header);
      if (formatOptions?.preserve_comments !== undefined) params.set('preserve_comments', formatOptions.preserve_comments.toString());

      const response = await apiClient.get(
        `/api/personality/${personalityId}/export/${ideType}?${params.toString()}`,
        { responseType: 'blob' }
      );
      return response.data;
    } catch (error: any) {
      if (error.response?.data) {
        throw new PersonalityApiError(error.response.data, error.response.status);
      }
      throw error;
    }
  }

  /**
   * Preview personality configuration export content
   */
  static async previewPersonalityExport(
    personalityId: string,
    ideType: SupportedIDEType,
    formatOptions?: ExportFormatOptions
  ): Promise<PreviewResult> {
    try {
      const response: AxiosResponse<PreviewResult> = await apiClient.get(
        `/api/personality/${personalityId}/export/${ideType}/preview`,
        {
          params: {
            ...(formatOptions?.file_name && { file_name: formatOptions.file_name }),
            ...(formatOptions?.include_metadata !== undefined && { include_metadata: formatOptions.include_metadata }),
            ...(formatOptions?.include_instructions !== undefined && { include_instructions: formatOptions.include_instructions }),
            ...(formatOptions?.custom_header && { custom_header: formatOptions.custom_header }),
            ...(formatOptions?.preserve_comments !== undefined && { preserve_comments: formatOptions.preserve_comments }),
          }
        }
      );
      return response.data;
    } catch (error: any) {
      if (error.response?.data) {
        throw new PersonalityApiError(error.response.data, error.response.status);
      }
      throw error;
    }
  }

  /**
   * Get list of supported IDE types for export
   */
  static async getSupportedIDETypes(): Promise<{
    supported_ides: Array<{
      type: string;
      name: string;
      description: string;
      file_extension: string;
      supports_metadata: boolean;
    }>;
    total_count: number;
  }> {
    try {
      const response = await apiClient.get('/api/personality/export/supported-ides');
      return response.data;
    } catch (error: any) {
      if (error.response?.data) {
        throw new PersonalityApiError(error.response.data, error.response.status);
      }
      throw error;
    }
  }

  /**
   * Bulk export multiple personality configurations
   */
  static async bulkExportPersonalities(
    request: BulkExportRequest
  ): Promise<Blob> {
    try {
      const response = await apiClient.post(
        '/api/personality/export/bulk',
        request,
        { responseType: 'blob' }
      );
      return response.data;
    } catch (error: any) {
      if (error.response?.data) {
        throw new PersonalityApiError(error.response.data, error.response.status);
      }
      throw error;
    }
  }

  /**
   * Import personality configuration from file
   */
  static async importPersonalityConfig(
    file: File,
    userId?: string
  ): Promise<PersonalityConfig> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (userId) {
        formData.append('user_id', userId);
      }

      const response: AxiosResponse<PersonalityConfig> = await apiClient.post(
        '/api/personality/import',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      return response.data;
    } catch (error: any) {
      if (error.response?.data) {
        throw new PersonalityApiError(error.response.data, error.response.status);
      }
      throw error;
    }
  }

  /**
   * Validate import file format before import
   */
  static async validateImportFile(file: File): Promise<{
    valid: boolean;
    detected_format: string;
    ide_type: string;
    confidence: number;
    errors: string[];
    warnings: string[];
  }> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await apiClient.post(
        '/api/personality/import/validate',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      return response.data;
    } catch (error: any) {
      if (error.response?.data) {
        throw new PersonalityApiError(error.response.data, error.response.status);
      }
      throw error;
    }
  }
}

export default PersonalityApi;