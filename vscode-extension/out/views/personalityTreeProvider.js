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
exports.PersonalityTreeProvider = exports.PersonalityTreeItem = void 0;
const vscode = __importStar(require("vscode"));
class PersonalityTreeItem extends vscode.TreeItem {
    personality;
    collapsibleState;
    constructor(personality, collapsibleState) {
        super(personality.name, collapsibleState);
        this.personality = personality;
        this.collapsibleState = collapsibleState;
        this.tooltip = new vscode.MarkdownString(this.getTooltipContent());
        this.description = personality.isActive ? 'Active' : '';
        this.contextValue = personality.isActive ? 'activePersonality' : 'personality';
        // Set icon based on active state
        this.iconPath = new vscode.ThemeIcon(personality.isActive ? 'circle-filled' : 'circle-outline');
    }
    getTooltipContent() {
        const traits = this.personality.traits
            .slice(0, 3)
            .map(t => `- ${t.name}: ${t.value}`)
            .join('\n');
        return `**${this.personality.name}**\n\n${this.personality.description}\n\n**Key Traits:**\n${traits}`;
    }
}
exports.PersonalityTreeItem = PersonalityTreeItem;
class PersonalityTreeProvider {
    personalityService;
    _onDidChangeTreeData = new vscode.EventEmitter();
    onDidChangeTreeData = this._onDidChangeTreeData.event;
    constructor(personalityService) {
        this.personalityService = personalityService;
        // Subscribe to personality changes
        personalityService.onDidChangePersonalities(() => {
            this.refresh();
        });
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    getTreeItem(element) {
        return element;
    }
    async getChildren(element) {
        if (!element) {
            // Root level - show all personalities
            const personalities = await this.personalityService.getPersonalities();
            // Sort personalities: active first, then by name
            personalities.sort((a, b) => {
                if (a.isActive && !b.isActive)
                    return -1;
                if (!a.isActive && b.isActive)
                    return 1;
                return a.name.localeCompare(b.name);
            });
            return personalities.map(p => new PersonalityTreeItem(p, vscode.TreeItemCollapsibleState.None));
        }
        return [];
    }
    async getParent(_element) {
        return undefined;
    }
}
exports.PersonalityTreeProvider = PersonalityTreeProvider;
//# sourceMappingURL=personalityTreeProvider.js.map