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
exports.PersonalityService = void 0;
const vscode = __importStar(require("vscode"));
const helpers_1 = require("../utils/helpers");
const ideDetectionService_1 = require("./ideDetectionService");
const ideWriterService_1 = require("./ideWriterService");
class PersonalityService {
    globalState;
    workspaceState;
    STORAGE_KEY = 'covibe.personalities';
    personalities = new Map();
    _onDidChangePersonalities = new vscode.EventEmitter();
    onDidChangePersonalities = this._onDidChangePersonalities.event;
    ideDetectionService;
    ideWriterService;
    constructor(globalState, workspaceState) {
        this.globalState = globalState;
        this.workspaceState = workspaceState;
        this.ideDetectionService = new ideDetectionService_1.IDEDetectionService();
        this.ideWriterService = new ideWriterService_1.IDEWriterService();
        this.loadPersonalities();
    }
    async loadPersonalities() {
        const stored = this.globalState.get(this.STORAGE_KEY, {});
        this.personalities.clear();
        for (const [id, personality] of Object.entries(stored)) {
            // Convert dates from strings
            personality.created = new Date(personality.created);
            personality.modified = new Date(personality.modified);
            this.personalities.set(id, personality);
        }
    }
    async savePersonalities() {
        const toStore = {};
        for (const [id, personality] of this.personalities) {
            toStore[id] = personality;
        }
        await this.globalState.update(this.STORAGE_KEY, toStore);
        this._onDidChangePersonalities.fire();
    }
    async createPersonality(name, description, traits) {
        const id = (0, helpers_1.generateId)();
        const now = new Date();
        const personality = {
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
    async getPersonalities() {
        return Array.from(this.personalities.values());
    }
    async getPersonality(id) {
        return this.personalities.get(id);
    }
    async getActivePersonality() {
        for (const personality of this.personalities.values()) {
            if (personality.isActive) {
                return personality;
            }
        }
        return undefined;
    }
    async activatePersonality(id) {
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
    async applyPersonalityToWorkspace(personality) {
        try {
            // Check workspace trust
            if (!vscode.workspace.isTrusted) {
                vscode.window.showWarningMessage('Cannot update IDE files in untrusted workspace');
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
                    const ideFile = await this.ideDetectionService.findOrCreateIDEFile(selection);
                    await this.ideWriterService.applyPersonalityToIDE(personality, ideFile);
                }
            }
            else {
                // Update all existing IDE files
                for (const ideFile of ideFiles) {
                    await this.ideWriterService.applyPersonalityToIDE(personality, ideFile);
                }
            }
        }
        catch (error) {
            console.error('Failed to apply personality to workspace:', error);
            vscode.window.showErrorMessage(`Failed to update IDE files: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }
    async updatePersonality(id, updates) {
        const personality = this.personalities.get(id);
        if (personality) {
            Object.assign(personality, updates);
            personality.modified = new Date();
            await this.savePersonalities();
        }
    }
    async deletePersonality(id) {
        this.personalities.delete(id);
        await this.savePersonalities();
    }
    async exportPersonality(id) {
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
    async importPersonality(data) {
        try {
            const parsed = JSON.parse(data);
            // Validate required fields
            if (!parsed.name || !parsed.description || !parsed.traits) {
                throw new Error('Invalid personality data: missing required fields');
            }
            // Create new personality with imported data
            return await this.createPersonality(parsed.name, parsed.description, parsed.traits);
        }
        catch (error) {
            throw new Error(`Failed to import personality: ${error instanceof Error ? error.message : 'Invalid JSON'}`);
        }
    }
    generateDefaultTraits(description) {
        // Generate basic traits based on description keywords
        const traits = [];
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
    generateContext(name, description) {
        return `You are ${name}. ${description}

Key traits:
- Focus on code quality and best practices
- Provide clear, actionable feedback
- Be constructive and supportive`;
    }
    dispose() {
        this._onDidChangePersonalities.dispose();
        this.ideDetectionService.dispose();
    }
}
exports.PersonalityService = PersonalityService;
//# sourceMappingURL=personalityService.js.map