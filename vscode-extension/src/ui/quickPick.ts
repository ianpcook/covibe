import * as vscode from 'vscode';
import { Personality } from '../models/personality';

export async function showPersonalityInput(): Promise<string | undefined> {
  return vscode.window.showInputBox({
    prompt: 'Describe the AI personality you want',
    placeHolder: 'e.g., Expert TypeScript developer focused on clean code and testing',
    validateInput: (value) => {
      if (!value || value.length < 10) {
        return 'Please provide a more detailed description (at least 10 characters)';
      }
      if (value.length > 500) {
        return 'Description is too long (max 500 characters)';
      }
      return null;
    }
  });
}

export async function showPersonalityQuickPick(
  personalities: Personality[],
  placeHolder = 'Select a personality'
): Promise<Personality | undefined> {
  const items: (vscode.QuickPickItem & { personality: Personality })[] = personalities.map(p => ({
    label: p.name,
    description: p.isActive ? '$(check) Active' : '',
    detail: p.description,
    personality: p
  }));

  const selected = await vscode.window.showQuickPick(items, {
    placeHolder,
    matchOnDescription: true,
    matchOnDetail: true
  });

  return selected?.personality;
}