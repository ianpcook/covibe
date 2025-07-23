import * as vscode from 'vscode';
import { CommandManager } from './commands/commandManager';
import { PersonalityTreeProvider } from './views/personalityTreeProvider';
import { PersonalityService } from './services/personalityService';
import { StatusBarManager } from './ui/statusBarManager';
import { ActivationTelemetry } from './utils/telemetry';

let commandManager: CommandManager;
let personalityService: PersonalityService;
let treeProvider: PersonalityTreeProvider;
let statusBarManager: StatusBarManager;

export async function activate(context: vscode.ExtensionContext): Promise<void> {
  const startTime = Date.now();
  
  try {
    // Track activation
    const telemetry = new ActivationTelemetry(context);
    await telemetry.reportActivation();

    // Initialize core services with lazy loading
    personalityService = new PersonalityService(context.globalState, context.workspaceState);
    
    // Set up IDE file watching
    context.subscriptions.push(
      personalityService['ideDetectionService'].watchIDEFiles()
    );
    
    // Register commands
    commandManager = new CommandManager(context, personalityService);
    await commandManager.registerCommands();

    // Set up tree view
    treeProvider = new PersonalityTreeProvider(personalityService);
    const treeView = vscode.window.createTreeView('covibe.personalities', {
      treeDataProvider: treeProvider,
      showCollapseAll: true
    });
    context.subscriptions.push(treeView);

    // Initialize status bar
    statusBarManager = new StatusBarManager(personalityService);
    context.subscriptions.push(statusBarManager);

    // Show welcome message on first activation
    const hasShownWelcome = context.globalState.get<boolean>('hasShownWelcome', false);
    if (!hasShownWelcome) {
      const showWalkthrough = 'Show Walkthrough';
      const selection = await vscode.window.showInformationMessage(
        'Welcome to Covibe! Configure personality traits for your AI coding assistant.',
        showWalkthrough
      );
      
      if (selection === showWalkthrough) {
        // TODO: Add walkthrough in future version
        vscode.window.showInformationMessage('Quick start: Use the Covibe view in the Activity Bar to create your first personality!');
      }
      
      await context.globalState.update('hasShownWelcome', true);
    }

    // Log successful activation
    const activationTime = Date.now() - startTime;
    console.log(`Covibe extension activated in ${activationTime}ms`);
    
    // Auto-activate default personality if configured
    const config = vscode.workspace.getConfiguration('covibe');
    if (config.get<boolean>('autoActivatePersonality')) {
      const defaultPersonalityId = context.workspaceState.get<string>('defaultPersonalityId');
      if (defaultPersonalityId) {
        await personalityService.activatePersonality(defaultPersonalityId);
      }
    }

  } catch (error) {
    console.error('Failed to activate Covibe extension:', error);
    vscode.window.showErrorMessage(`Failed to activate Covibe: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

export function deactivate(): void {
  // Cleanup resources
  commandManager?.dispose();
  statusBarManager?.dispose();
  console.log('Covibe extension deactivated');
}