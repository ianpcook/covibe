import * as vscode from 'vscode';
import { Personality } from '../models/personality';
import { PersonalityService } from '../services/personalityService';

export class PersonalityTreeItem extends vscode.TreeItem {
  constructor(
    public readonly personality: Personality,
    public override readonly collapsibleState: vscode.TreeItemCollapsibleState
  ) {
    super(personality.name, collapsibleState);
    
    this.tooltip = new vscode.MarkdownString(this.getTooltipContent());
    this.description = personality.isActive ? 'Active' : '';
    this.contextValue = personality.isActive ? 'activePersonality' : 'personality';
    
    // Set icon based on active state
    this.iconPath = new vscode.ThemeIcon(
      personality.isActive ? 'circle-filled' : 'circle-outline'
    );
  }

  private getTooltipContent(): string {
    const traits = this.personality.traits
      .slice(0, 3)
      .map(t => `- ${t.name}: ${t.value}`)
      .join('\n');
      
    return `**${this.personality.name}**\n\n${this.personality.description}\n\n**Key Traits:**\n${traits}`;
  }
}

export class PersonalityTreeProvider implements vscode.TreeDataProvider<PersonalityTreeItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<PersonalityTreeItem | undefined | null | void>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  constructor(private personalityService: PersonalityService) {
    // Subscribe to personality changes
    personalityService.onDidChangePersonalities(() => {
      this.refresh();
    });
  }

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: PersonalityTreeItem): vscode.TreeItem {
    return element;
  }

  async getChildren(element?: PersonalityTreeItem): Promise<PersonalityTreeItem[]> {
    if (!element) {
      // Root level - show all personalities
      const personalities = await this.personalityService.getPersonalities();
      
      // Sort personalities: active first, then by name
      personalities.sort((a, b) => {
        if (a.isActive && !b.isActive) return -1;
        if (!a.isActive && b.isActive) return 1;
        return a.name.localeCompare(b.name);
      });

      return personalities.map(p => new PersonalityTreeItem(p, vscode.TreeItemCollapsibleState.None));
    }
    
    return [];
  }

  async getParent(_element: PersonalityTreeItem): Promise<PersonalityTreeItem | undefined> {
    return undefined;
  }
}