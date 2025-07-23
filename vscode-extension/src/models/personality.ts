export interface Personality {
  id: string;
  name: string;
  description: string;
  traits: PersonalityTrait[];
  context: string;
  isActive: boolean;
  workspaceId?: string;
  created: Date;
  modified: Date;
  version: string;
}

export interface PersonalityTrait {
  category: 'technical' | 'communication' | 'workflow' | 'values';
  name: string;
  value: string;
  priority: 'high' | 'medium' | 'low';
}

export interface IDEFile {
  path: string;
  type: 'claude' | 'cursor' | 'windsurf' | 'continue';
  content: string;
  lastModified: Date;
  workspaceFolderUri: string;
}

export interface ResearchResult {
  success: boolean;
  personality?: Partial<Personality>;
  error?: string;
  source: 'ai' | 'template' | 'manual';
}

export interface PersonalityTemplate {
  id: string;
  name: string;
  description: string;
  keywords: string[];
  traits: PersonalityTrait[];
  context: string;
}