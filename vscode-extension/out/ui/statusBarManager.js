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
exports.StatusBarManager = void 0;
const vscode = __importStar(require("vscode"));
class StatusBarManager {
    personalityService;
    statusBarItem;
    disposables = [];
    constructor(personalityService) {
        this.personalityService = personalityService;
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        this.statusBarItem.command = 'covibe.listPersonalities';
        this.statusBarItem.tooltip = 'Click to switch personality';
        // Subscribe to personality changes
        this.disposables.push(this.personalityService.onDidChangePersonalities(() => this.updateStatusBar()));
        // Subscribe to configuration changes
        this.disposables.push(vscode.workspace.onDidChangeConfiguration(e => {
            if (e.affectsConfiguration('covibe.showStatusBar')) {
                this.updateStatusBar();
            }
        }));
        // Initial update
        this.updateStatusBar();
    }
    async updateStatusBar() {
        const config = vscode.workspace.getConfiguration('covibe');
        const showStatusBar = config.get('showStatusBar', true);
        if (!showStatusBar) {
            this.statusBarItem.hide();
            return;
        }
        const activePersonality = await this.personalityService.getActivePersonality();
        if (activePersonality) {
            this.statusBarItem.text = `$(robot) ${activePersonality.name}`;
            this.statusBarItem.show();
        }
        else {
            this.statusBarItem.text = '$(robot) No Active Personality';
            this.statusBarItem.show();
        }
    }
    dispose() {
        this.statusBarItem.dispose();
        this.disposables.forEach(d => d.dispose());
    }
}
exports.StatusBarManager = StatusBarManager;
//# sourceMappingURL=statusBarManager.js.map