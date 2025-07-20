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