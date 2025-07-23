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
exports.showPersonalityInput = showPersonalityInput;
exports.showPersonalityQuickPick = showPersonalityQuickPick;
const vscode = __importStar(require("vscode"));
async function showPersonalityInput() {
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
async function showPersonalityQuickPick(personalities, placeHolder = 'Select a personality') {
    const items = personalities.map(p => ({
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
//# sourceMappingURL=quickPick.js.map