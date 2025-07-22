/**
 * TypeScript types for the personality system
 */

export interface PersonalityTrait {
  category: string;
  trait: string;
  intensity: number;
  examples: string[];
}

export interface CommunicationStyle {
  tone: string;
  formality: 'casual' | 'formal' | 'mixed';
  verbosity: 'concise' | 'moderate' | 'verbose';
  technical_level: 'beginner' | 'intermediate' | 'expert';
}

export interface ResearchSource {
  type: string;
  url?: string;
  confidence: number;
  last_updated: string;
}

export interface PersonalityProfile {
  id: string;
  name: string;
  type: 'celebrity' | 'fictional' | 'archetype' | 'custom';
  traits: PersonalityTrait[];
  communication_style: CommunicationStyle;
  mannerisms: string[];
  sources: ResearchSource[];
}

export interface PersonalityConfig {
  id: string;
  profile: PersonalityProfile;
  context: string;
  ide_type: string;
  file_path: string;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PersonalityRequest {
  description: string;
  user_id?: string;
  project_path?: string;
  source?: 'web' | 'api' | 'chat';
}

export interface ResearchResult {
  query: string;
  profiles_found: number;
  profiles: Array<{
    id: string;
    name: string;
    type: string;
    traits: Array<{ trait: string; intensity: number }>;
    communication_style: {
      tone: string;
      formality: string;
      verbosity: string;
      technical_level: string;
    };
    mannerisms: string[];
    confidence: number;
  }>;
  confidence: number;
  suggestions: string[];
  errors: string[];
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: any;
    suggestions: string[];
  };
  request_id: string;
  timestamp: string;
}

// Export-related types

export interface ExportFormatOptions {
  file_name?: string;
  include_metadata?: boolean;
  include_instructions?: boolean;
  custom_header?: string;
  preserve_comments?: boolean;
}

export interface ExportResult {
  success: boolean;
  content: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  placement_instructions: string[];
  metadata: Record<string, any>;
  error?: string;
}

export interface PreviewResult {
  success: boolean;
  content: string;
  file_name: string;
  file_size: number;
  syntax_language: string;
  placement_instructions: string[];
  metadata: Record<string, any>;
  error?: string;
}

export interface BulkExportRequest {
  personality_ids: string[];
  ide_types: string[];
  format_options?: ExportFormatOptions;
  include_readme?: boolean;
}

export interface BulkExportResult {
  success: boolean;
  zip_content: string; // Base64 encoded
  file_name: string;
  file_size: number;
  included_configs: string[];
  readme_content: string;
  error?: string;
}

export interface ExportMetadata {
  export_version: string;
  personality_id: string;
  personality_name: string;
  ide_type: string;
  exported_at: string; // ISO date string
  exported_by?: string;
  original_created_at: string; // ISO date string
  llm_generated: boolean;
  llm_provider?: string;
  confidence?: number;
  checksum: string;
}

export interface ConversionResult {
  success: boolean;
  converted_content: string;
  target_format: string;
  conversion_notes: string[];
  error?: string;
}

export interface IDEFormatDetectionResult {
  detected_format: string;
  confidence: number;
  format_indicators: string[];
  suggested_ide_type: string;
}

// UI-specific export types

export type SupportedIDEType = 'cursor' | 'claude' | 'windsurf' | 'generic';

export interface ExportProgressState {
  stage: 'idle' | 'preparing' | 'generating' | 'downloading' | 'complete' | 'error';
  progress: number; // 0-100
  message: string;
  error?: string;
}

export interface ExportUIConfig {
  showPreview: boolean;
  selectedIDEType: SupportedIDEType;
  formatOptions: ExportFormatOptions;
  isGenerating: boolean;
}