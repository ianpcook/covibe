"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.CommandManager = void 0;
const vscode = __importStar(require("vscode"));
const quickPick_1 = require("../ui/quickPick");
const progress_1 = require("../ui/progress");
class CommandManager {
    context;
    personalityService;
    disposables = [];
    constructor(context, personalityService) {
        this.context = context;
        this.personalityService = personalityService;
    }
    async registerCommands() {
        // Register all commands
        this.registerCommand('covibe.createPersonality', () => this.createPersonality());
        this.registerCommand('covibe.listPersonalities', () => this.listPersonalities());
        this.registerCommand('covibe.activatePersonality', () => this.activatePersonality());
        this.registerCommand('covibe.deletePersonality', (personalityId) => this.deletePersonality(personalityId));
        this.registerCommand('covibe.editPersonality', (personalityId) => this.editPersonality(personalityId));
        this.registerCommand('covibe.exportPersonality', (personalityId) => this.exportPersonality(personalityId));
        this.registerCommand('covibe.importPersonality', () => this.importPersonality());
        this.registerCommand('covibe.refreshPersonalities', () => this.refreshPersonalities());
    }
    registerCommand(command, callback) {
        const disposable = vscode.commands.registerCommand(command, async (...args) => {
            try {
                await callback(...args);
            }
            catch (error) {
                console.error(`Command ${command} failed:`, error);
                vscode.window.showErrorMessage(`Command failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
            }
        });
        this.disposables.push(disposable);
        this.context.subscriptions.push(disposable);
    }
    async createPersonality() {
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
        const description = await (0, quickPick_1.showPersonalityInput)();
        if (!description) {
            return;
        }
        // Create personality with progress
        await (0, progress_1.withProgress)('Creating personality...', async (progress) => {
            progress.report({ message: 'Analyzing description...' });
            const personality = await this.personalityService.createPersonality(name.trim(), description.trim());
            progress.report({ message: 'Personality created!', increment: 100 });
            // Show success message with action
            const activate = 'Activate Now';
            const selection = await vscode.window.showInformationMessage(`Personality "${personality.name}" created successfully!`, activate);
            if (selection === activate) {
                await this.personalityService.activatePersonality(personality.id);
                vscode.window.showInformationMessage(`Personality "${personality.name}" is now active`);
            }
        });
    }
    async listPersonalities() {
        const personalities = await this.personalityService.getPersonalities();
        if (personalities.length === 0) {
            const create = 'Create Personality';
            const selection = await vscode.window.showInformationMessage('No personalities found. Would you like to create one?', create);
            if (selection === create) {
                await this.createPersonality();
            }
            return;
        }
        const personality = await (0, quickPick_1.showPersonalityQuickPick)(personalities);
        if (personality) {
            await this.personalityService.activatePersonality(personality.id);
            vscode.window.showInformationMessage(`Activated personality: ${personality.name}`);
        }
    }
    async activatePersonality() {
        const personalities = await this.personalityService.getPersonalities();
        if (personalities.length === 0) {
            vscode.window.showWarningMessage('No personalities available to activate');
            return;
        }
        const personality = await (0, quickPick_1.showPersonalityQuickPick)(personalities);
        if (personality) {
            await this.personalityService.activatePersonality(personality.id);
            vscode.window.showInformationMessage(`Activated personality: ${personality.name}`);
        }
    }
    async deletePersonality(personalityId) {
        let personality;
        if (personalityId) {
            personality = await this.personalityService.getPersonality(personalityId);
        }
        else {
            const personalities = await this.personalityService.getPersonalities();
            personality = await (0, quickPick_1.showPersonalityQuickPick)(personalities, 'Select personality to delete');
        }
        if (!personality) {
            return;
        }
        const confirm = await vscode.window.showWarningMessage(`Are you sure you want to delete "${personality.name}"?`, { modal: true }, 'Delete');
        if (confirm === 'Delete') {
            await this.personalityService.deletePersonality(personality.id);
            vscode.window.showInformationMessage(`Deleted personality: ${personality.name}`);
        }
    }
    async editPersonality(personalityId) {
        let personality;
        if (personalityId) {
            personality = await this.personalityService.getPersonality(personalityId);
        }
        else {
            const personalities = await this.personalityService.getPersonalities();
            personality = await (0, quickPick_1.showPersonalityQuickPick)(personalities, 'Select personality to edit');
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
    async exportPersonality(personalityId) {
        let personality;
        if (personalityId) {
            personality = await this.personalityService.getPersonality(personalityId);
        }
        else {
            const personalities = await this.personalityService.getPersonalities();
            personality = await (0, quickPick_1.showPersonalityQuickPick)(personalities, 'Select personality to export');
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
    async importPersonality() {
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
            const data = await vscode.workspace.fs.readFile(uri[0]);
            const jsonStr = Buffer.from(data).toString('utf8');
            const personality = await this.personalityService.importPersonality(jsonStr);
            const activate = 'Activate Now';
            const selection = await vscode.window.showInformationMessage(`Imported personality: ${personality.name}`, activate);
            if (selection === activate) {
                await this.personalityService.activatePersonality(personality.id);
            }
        }
        catch (error) {
            vscode.window.showErrorMessage(`Failed to import personality: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }
    async refreshPersonalities() {
        // The service will automatically notify the tree view through the event emitter
        vscode.window.showInformationMessage('Refreshed personalities');
    }
    dispose() {
        this.disposables.forEach(d => d.dispose());
    }
}
exports.CommandManager = CommandManager;
//# sourceMappingURL=commandManager.js.map