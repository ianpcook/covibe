import * as vscode from 'vscode';
import { PersonalityService } from '../services/personalityService';
import { showPersonalityInput, showPersonalityQuickPick } from '../ui/quickPick';
import { withProgress } from '../ui/progress';

export class CommandManager {
  private disposables: vscode.Disposable[] = [];

  constructor(
    private context: vscode.ExtensionContext,
    private personalityService: PersonalityService
  ) {}

  async registerCommands(): Promise<void> {
    // Register all commands
    this.registerCommand('covibe.createPersonality', () => this.createPersonality());
    this.registerCommand('covibe.listPersonalities', () => this.listPersonalities());
    this.registerCommand('covibe.activatePersonality', () => this.activatePersonality());
    this.registerCommand('covibe.deletePersonality', (personalityId?: string) => this.deletePersonality(personalityId));
    this.registerCommand('covibe.editPersonality', (personalityId?: string) => this.editPersonality(personalityId));
    this.registerCommand('covibe.exportPersonality', (personalityId?: string) => this.exportPersonality(personalityId));
    this.registerCommand('covibe.importPersonality', () => this.importPersonality());
    this.registerCommand('covibe.refreshPersonalities', () => this.refreshPersonalities());
  }

  private registerCommand(command: string, callback: (...args: any[]) => any): void {
    const disposable = vscode.commands.registerCommand(command, async (...args) => {
      try {
        await callback(...args);
      } catch (error) {
        console.error(`Command ${command} failed:`, error);
        vscode.window.showErrorMessage(
          `Command failed: ${error instanceof Error ? error.message : 'Unknown error'}`
        );
      }
    });
    
    this.disposables.push(disposable);
    this.context.subscriptions.push(disposable);
  }

  private async createPersonality(): Promise<void> {
    // Get personality name
    const name = await vscode.window.showInputBox({
      prompt: 'Enter a name for the personality',
      placeHolder: 'e.g., Expert TypeScript Developer',
      validateInput: (value) => {
        if (!value || value.trim().length === 0) {
          return 'Name is required';
        }
        if (value.length > 50) {
          return 'Name is too long (max 50 characters)';
        }
        return null;
      }
    });

    if (!name) {
      return;
    }

    // Get personality description
    const description = await showPersonalityInput();
    if (!description) {
      return;
    }

    // Create personality with progress
    await withProgress('Creating personality...', async (progress) => {
      progress.report({ message: 'Analyzing description...' });
      
      const personality = await this.personalityService.createPersonality(
        name.trim(),
        description.trim()
      );

      progress.report({ message: 'Personality created!', increment: 100 });

      // Show success message with action
      const activate = 'Activate Now';
      const selection = await vscode.window.showInformationMessage(
        `Personality "${personality.name}" created successfully!`,
        activate
      );

      if (selection === activate) {
        await this.personalityService.activatePersonality(personality.id);
        vscode.window.showInformationMessage(`Personality "${personality.name}" is now active`);
      }
    });
  }

  private async listPersonalities(): Promise<void> {
    const personalities = await this.personalityService.getPersonalities();
    
    if (personalities.length === 0) {
      const create = 'Create Personality';
      const selection = await vscode.window.showInformationMessage(
        'No personalities found. Would you like to create one?',
        create
      );
      
      if (selection === create) {
        await this.createPersonality();
      }
      return;
    }

    const personality = await showPersonalityQuickPick(personalities);
    if (personality) {
      await this.personalityService.activatePersonality(personality.id);
      vscode.window.showInformationMessage(`Activated personality: ${personality.name}`);
    }
  }

  private async activatePersonality(): Promise<void> {
    const personalities = await this.personalityService.getPersonalities();
    
    if (personalities.length === 0) {
      vscode.window.showWarningMessage('No personalities available to activate');
      return;
    }

    const personality = await showPersonalityQuickPick(personalities);
    if (personality) {
      await this.personalityService.activatePersonality(personality.id);
      vscode.window.showInformationMessage(`Activated personality: ${personality.name}`);
    }
  }

  private async deletePersonality(personalityId?: string): Promise<void> {
    let personality;
    
    if (personalityId) {
      personality = await this.personalityService.getPersonality(personalityId);
    } else {
      const personalities = await this.personalityService.getPersonalities();
      personality = await showPersonalityQuickPick(personalities, 'Select personality to delete');
    }

    if (!personality) {
      return;
    }

    const confirm = await vscode.window.showWarningMessage(
      `Are you sure you want to delete "${personality.name}"?`,
      { modal: true },
      'Delete'
    );

    if (confirm === 'Delete') {
      await this.personalityService.deletePersonality(personality.id);
      vscode.window.showInformationMessage(`Deleted personality: ${personality.name}`);
    }
  }

  private async editPersonality(personalityId?: string): Promise<void> {
    let personality;
    
    if (personalityId) {
      personality = await this.personalityService.getPersonality(personalityId);
    } else {
      const personalities = await this.personalityService.getPersonalities();
      personality = await showPersonalityQuickPick(personalities, 'Select personality to edit');
    }

    if (!personality) {
      return;
    }

    // For MVP, we'll open a simple input to edit the description
    const newDescription = await vscode.window.showInputBox({
      prompt: 'Edit personality description',
      value: personality.description,
      validateInput: (value) => {
        if (!value || value.length < 10) {
          return 'Please provide a more detailed description';
        }
        if (value.length > 500) {
          return 'Description is too long (max 500 characters)';
        }
        return null;
      }
    });

    if (newDescription && newDescription !== personality.description) {
      await this.personalityService.updatePersonality(personality.id, {
        description: newDescription
      });
      vscode.window.showInformationMessage(`Updated personality: ${personality.name}`);
    }
  }

  private async exportPersonality(personalityId?: string): Promise<void> {
    let personality;
    
    if (personalityId) {
      personality = await this.personalityService.getPersonality(personalityId);
    } else {
      const personalities = await this.personalityService.getPersonalities();
      personality = await showPersonalityQuickPick(personalities, 'Select personality to export');
    }

    if (!personality) {
      return;
    }

    const exportData = await this.personalityService.exportPersonality(personality.id);
    
    const uri = await vscode.window.showSaveDialog({
      defaultUri: vscode.Uri.file(`${personality.name.replace(/\s+/g, '-').toLowerCase()}.json`),
      filters: {
        'JSON files': ['json']
      }
    });

    if (uri) {
      await vscode.workspace.fs.writeFile(uri, Buffer.from(exportData, 'utf8'));
      vscode.window.showInformationMessage(`Exported personality to ${uri.fsPath}`);
    }
  }

  private async importPersonality(): Promise<void> {
    const uri = await vscode.window.showOpenDialog({
      canSelectFiles: true,
      canSelectFolders: false,
      canSelectMany: false,
      filters: {
        'JSON files': ['json']
      }
    });

    if (!uri || uri.length === 0) {
      return;
    }

    try {
      const data = await vscode.workspace.fs.readFile(uri[0]!);
      const jsonStr = Buffer.from(data).toString('utf8');
      
      const personality = await this.personalityService.importPersonality(jsonStr);
      
      const activate = 'Activate Now';
      const selection = await vscode.window.showInformationMessage(
        `Imported personality: ${personality.name}`,
        activate
      );

      if (selection === activate) {
        await this.personalityService.activatePersonality(personality.id);
      }
    } catch (error) {
      vscode.window.showErrorMessage(
        `Failed to import personality: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  private async refreshPersonalities(): Promise<void> {
    // The service will automatically notify the tree view through the event emitter
    vscode.window.showInformationMessage('Refreshed personalities');
  }

  dispose(): void {
    this.disposables.forEach(d => d.dispose());
  }
}