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
exports.IDEWriterService = void 0;
const vscode = __importStar(require("vscode"));
class IDEWriterService {
    async applyPersonalityToIDE(personality, ideFile) {
        const updatedContent = this.generateIDEContent(personality, ideFile);
        // Show diff before applying
        const proceed = await this.showDiffAndConfirm(ideFile, updatedContent);
        if (!proceed) {
            return;
        }
        // Backup existing file
        await this.backupFile(ideFile);
        // Write updated content
        await vscode.workspace.fs.writeFile(vscode.Uri.file(ideFile.path), Buffer.from(updatedContent, 'utf8'));
        vscode.window.showInformationMessage(`Updated ${ideFile.type.toUpperCase()} configuration with personality: ${personality.name}`);
    }
    generateIDEContent(personality, ideFile) {
        switch (ideFile.type) {
            case 'claude':
                return this.generateClaudeContent(personality, ideFile.content);
            case 'cursor':
                return this.generateCursorContent(personality);
            case 'windsurf':
                return this.generateWindsurfContent(personality);
            case 'continue':
                return this.generateContinueContent(personality, ideFile.content);
            default:
                throw new Error(`Unsupported IDE type: ${ideFile.type}`);
        }
    }
    generateClaudeContent(personality, existingContent) {
        // Check if there's existing CLAUDE.md content to preserve
        const hasExistingInstructions = existingContent.includes('# CLAUDE.md') ||
            existingContent.includes('# Claude Instructions');
        const personalitySection = `
# Claude Personality Configuration

The following information MUST be used to guide the style of text output to the user. This is a kind of personality that Claude will take on and emulate through interactions with the user.

## Profile: ${personality.name}

**Description**: ${personality.description}

## Communication Guidelines

${this.formatTraits(personality)}

## Behavioral Patterns

${personality.context}

## Implementation Notes
- Embody these characteristics consistently throughout conversations
- Adapt the personality to the context while maintaining core traits
- Balance personality expression with helpfulness and accuracy
`;
        if (hasExistingInstructions) {
            // Preserve existing content and add/update personality section
            const personalityMarkerStart = '# Claude Personality Configuration';
            const personalityMarkerEnd = '## Implementation Notes';
            if (existingContent.includes(personalityMarkerStart)) {
                // Replace existing personality section
                const startIndex = existingContent.indexOf(personalityMarkerStart);
                const endIndex = existingContent.indexOf('\n\n', existingContent.indexOf(personalityMarkerEnd));
                return existingContent.substring(0, startIndex) +
                    personalitySection.trim() +
                    existingContent.substring(endIndex);
            }
            else {
                // Add personality section at the beginning
                return personalitySection + '\n\n' + existingContent;
            }
        }
        else {
            // Create new CLAUDE.md with personality
            return `# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

${personalitySection}`;
        }
    }
    generateCursorContent(personality) {
        return `# Cursor Rules

## AI Assistant Personality: ${personality.name}

${personality.description}

### Key Traits:
${this.formatTraits(personality)}

### Context:
${personality.context}

### Guidelines:
- Apply these personality traits in all interactions
- Maintain consistency with the defined characteristics
- Balance personality with technical accuracy
`;
    }
    generateWindsurfContent(personality) {
        return `# Windsurf Rules

## Personality Configuration

**Name**: ${personality.name}
**Description**: ${personality.description}

### Traits:
${this.formatTraits(personality)}

### Behavioral Context:
${personality.context}

---
Generated by Covibe VS Code Extension
`;
    }
    generateContinueContent(personality, existingContent) {
        try {
            const config = JSON.parse(existingContent);
            config.rules = config.rules || [];
            config.personality = {
                name: personality.name,
                description: personality.description,
                traits: personality.traits.map(t => ({
                    category: t.category,
                    name: t.name,
                    value: t.value
                }))
            };
            return JSON.stringify(config, null, 2);
        }
        catch (error) {
            // If existing content is not valid JSON, create new
            return JSON.stringify({
                rules: [],
                personality: {
                    name: personality.name,
                    description: personality.description,
                    traits: personality.traits
                }
            }, null, 2);
        }
    }
    formatTraits(personality) {
        const traitsByCategory = personality.traits.reduce((acc, trait) => {
            if (!acc[trait.category]) {
                acc[trait.category] = [];
            }
            acc[trait.category].push(trait);
            return acc;
        }, {});
        return Object.entries(traitsByCategory)
            .map(([category, traits]) => {
            const categoryTitle = category.charAt(0).toUpperCase() + category.slice(1);
            const traitsList = traits
                .sort((a, b) => {
                const priorityOrder = { high: 0, medium: 1, low: 2 };
                return priorityOrder[a.priority] - priorityOrder[b.priority];
            })
                .map(t => `- **${t.name}**: ${t.value} (${t.priority} priority)`)
                .join('\n');
            return `### ${categoryTitle} Traits:\n${traitsList}`;
        })
            .join('\n\n');
    }
    async showDiffAndConfirm(ideFile, _newContent) {
        // For MVP, just show confirmation dialog
        // In future, could show actual diff view
        const action = await vscode.window.showInformationMessage(`Update ${ideFile.type.toUpperCase()} configuration file?`, { modal: true }, 'Update', 'Cancel');
        return action === 'Update';
    }
    async backupFile(ideFile) {
        const backupPath = `${ideFile.path}.backup-${Date.now()}`;
        try {
            await vscode.workspace.fs.copy(vscode.Uri.file(ideFile.path), vscode.Uri.file(backupPath), { overwrite: false });
        }
        catch (error) {
            // File might not exist yet, that's ok
        }
    }
}
exports.IDEWriterService = IDEWriterService;
//# sourceMappingURL=ideWriterService.js.map