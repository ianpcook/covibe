import * as vscode from 'vscode';
import { Personality, PersonalityTrait } from '../models/personality';
import { generateId } from '../utils/helpers';
import { IDEDetectionService } from './ideDetectionService';
import { IDEWriterService } from './ideWriterService';

export class PersonalityService {
  private readonly STORAGE_KEY = 'covibe.personalities';
  private personalities: Map<string, Personality> = new Map();
  private _onDidChangePersonalities = new vscode.EventEmitter<void>();
  public readonly onDidChangePersonalities = this._onDidChangePersonalities.event;
  
  private ideDetectionService: IDEDetectionService;
  private ideWriterService: IDEWriterService;

  constructor(
    private globalState: vscode.Memento,
    private workspaceState: vscode.Memento
  ) {
    this.ideDetectionService = new IDEDetectionService();
    this.ideWriterService = new IDEWriterService();
    this.loadPersonalities();
  }

  private async loadPersonalities(): Promise<void> {
    const stored = this.globalState.get<Record<string, Personality>>(this.STORAGE_KEY, {});
    this.personalities.clear();
    
    for (const [id, personality] of Object.entries(stored)) {
      // Convert dates from strings
      personality.created = new Date(personality.created);
      personality.modified = new Date(personality.modified);
      this.personalities.set(id, personality);
    }
  }

  private async savePersonalities(): Promise<void> {
    const toStore: Record<string, Personality> = {};
    for (const [id, personality] of this.personalities) {
      toStore[id] = personality;
    }
    await this.globalState.update(this.STORAGE_KEY, toStore);
    this._onDidChangePersonalities.fire();
  }

  async createPersonality(name: string, description: string, traits?: PersonalityTrait[]): Promise<Personality> {
    const id = generateId();
    const now = new Date();
    
    const personality: Personality = {
      id,
      name,
      description,
      traits: traits || this.generateDefaultTraits(description),
      context: this.generateContext(name, description),
      isActive: false,
      created: now,
      modified: now,
      version: '1.0.0'
    };

    this.personalities.set(id, personality);
    await this.savePersonalities();
    
    return personality;
  }

  async getPersonalities(): Promise<Personality[]> {
    return Array.from(this.personalities.values());
  }

  async getPersonality(id: string): Promise<Personality | undefined> {
    return this.personalities.get(id);
  }

  async getActivePersonality(): Promise<Personality | undefined> {
    for (const personality of this.personalities.values()) {
      if (personality.isActive) {
        return personality;
      }
    }
    return undefined;
  }

  async activatePersonality(id: string): Promise<void> {
    // Deactivate all personalities
    for (const personality of this.personalities.values()) {
      personality.isActive = false;
    }

    // Activate the selected one
    const personality = this.personalities.get(id);
    if (personality) {
      personality.isActive = true;
      personality.workspaceId = vscode.workspace.workspaceFolders?.[0]?.uri.toString();
      await this.savePersonalities();
      
      // Update workspace state
      await this.workspaceState.update('activePersonalityId', id);
      await this.workspaceState.update('defaultPersonalityId', id);
      
      // Apply to IDE files
      await this.applyPersonalityToWorkspace(personality);
    }
  }

  private async applyPersonalityToWorkspace(personality: Personality): Promise<void> {
    try {
      // Check workspace trust
      if (!vscode.workspace.isTrusted) {
        vscode.window.showWarningMessage(
          'Cannot update IDE files in untrusted workspace'
        );
        return;
      }

      // Detect existing IDE files
      const ideFiles = await this.ideDetectionService.detectIDEFiles();
      
      if (ideFiles.length === 0) {
        // No IDE files found, ask user which one to create
        const ideTypes = ['claude', 'cursor', 'windsurf'];
        const selection = await vscode.window.showQuickPick(ideTypes, {
          placeHolder: 'No AI IDE files found. Which one would you like to create?',
          canPickMany: false
        });
        
        if (selection) {
          const ideFile = await this.ideDetectionService.findOrCreateIDEFile(
            selection as 'claude' | 'cursor' | 'windsurf'
          );
          await this.ideWriterService.applyPersonalityToIDE(personality, ideFile);
        }
      } else {
        // Update all existing IDE files
        for (const ideFile of ideFiles) {
          await this.ideWriterService.applyPersonalityToIDE(personality, ideFile);
        }
      }
    } catch (error) {
      console.error('Failed to apply personality to workspace:', error);
      vscode.window.showErrorMessage(
        `Failed to update IDE files: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  async updatePersonality(id: string, updates: Partial<Personality>): Promise<void> {
    const personality = this.personalities.get(id);
    if (personality) {
      Object.assign(personality, updates);
      personality.modified = new Date();
      await this.savePersonalities();
    }
  }

  async deletePersonality(id: string): Promise<void> {
    this.personalities.delete(id);
    await this.savePersonalities();
  }

  async exportPersonality(id: string): Promise<string> {
    const personality = this.personalities.get(id);
    if (!personality) {
      throw new Error('Personality not found');
    }

    const exportData = {
      ...personality,
      exportVersion: '1.0',
      exportDate: new Date().toISOString()
    };

    return JSON.stringify(exportData, null, 2);
  }

  async importPersonality(data: string): Promise<Personality> {
    try {
      const parsed = JSON.parse(data);
      
      // Validate required fields
      if (!parsed.name || !parsed.description || !parsed.traits) {
        throw new Error('Invalid personality data: missing required fields');
      }

      // Create new personality with imported data
      return await this.createPersonality(
        parsed.name,
        parsed.description,
        parsed.traits
      );
    } catch (error) {
      throw new Error(`Failed to import personality: ${error instanceof Error ? error.message : 'Invalid JSON'}`);
    }
  }

  private generateDefaultTraits(description: string): PersonalityTrait[] {
    // Generate basic traits based on description keywords
    const traits: PersonalityTrait[] = [];
    const lowerDesc = description.toLowerCase();

    // Technical traits
    if (lowerDesc.includes('typescript') || lowerDesc.includes('javascript')) {
      traits.push({
        category: 'technical',
        name: 'Language expertise',
        value: 'Expert in TypeScript/JavaScript development',
        priority: 'high'
      });
    }

    if (lowerDesc.includes('clean') || lowerDesc.includes('quality')) {
      traits.push({
        category: 'technical',
        name: 'Code quality',
        value: 'Emphasizes clean, maintainable code',
        priority: 'high'
      });
    }

    // Communication traits
    if (lowerDesc.includes('patient') || lowerDesc.includes('helpful')) {
      traits.push({
        category: 'communication',
        name: 'Teaching style',
        value: 'Patient and thorough explanations',
        priority: 'medium'
      });
    }

    // Add default trait if none were generated
    if (traits.length === 0) {
      traits.push({
        category: 'communication',
        name: 'General approach',
        value: 'Professional and helpful',
        priority: 'medium'
      });
    }

    return traits;
  }

  private generateContext(name: string, description: string): string {
    return `You are ${name}. ${description}

Key traits:
- Focus on code quality and best practices
- Provide clear, actionable feedback
- Be constructive and supportive`;
  }

  dispose(): void {
    this._onDidChangePersonalities.dispose();
    this.ideDetectionService.dispose();
  }
}