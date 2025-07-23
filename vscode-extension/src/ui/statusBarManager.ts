import * as vscode from 'vscode';
import { PersonalityService } from '../services/personalityService';

export class StatusBarManager implements vscode.Disposable {
  private statusBarItem: vscode.StatusBarItem;
  private disposables: vscode.Disposable[] = [];

  constructor(private personalityService: PersonalityService) {
    this.statusBarItem = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Right,
      100
    );
    
    this.statusBarItem.command = 'covibe.listPersonalities';
    this.statusBarItem.tooltip = 'Click to switch personality';
    
    // Subscribe to personality changes
    this.disposables.push(
      this.personalityService.onDidChangePersonalities(() => this.updateStatusBar())
    );

    // Subscribe to configuration changes
    this.disposables.push(
      vscode.workspace.onDidChangeConfiguration(e => {
        if (e.affectsConfiguration('covibe.showStatusBar')) {
          this.updateStatusBar();
        }
      })
    );

    // Initial update
    this.updateStatusBar();
  }

  private async updateStatusBar(): Promise<void> {
    const config = vscode.workspace.getConfiguration('covibe');
    const showStatusBar = config.get<boolean>('showStatusBar', true);

    if (!showStatusBar) {
      this.statusBarItem.hide();
      return;
    }

    const activePersonality = await this.personalityService.getActivePersonality();
    
    if (activePersonality) {
      this.statusBarItem.text = `$(robot) ${activePersonality.name}`;
      this.statusBarItem.show();
    } else {
      this.statusBarItem.text = '$(robot) No Active Personality';
      this.statusBarItem.show();
    }
  }

  dispose(): void {
    this.statusBarItem.dispose();
    this.disposables.forEach(d => d.dispose());
  }
}