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
exports.IDEDetectionService = void 0;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
class IDEDetectionService {
    static IDE_PATTERNS = [
        {
            type: 'claude',
            patterns: ['CLAUDE.md', 'claude.md'],
            defaultPath: 'CLAUDE.md',
            displayName: 'Claude'
        },
        {
            type: 'cursor',
            patterns: ['.cursor/rules', '.cursor-rules'],
            defaultPath: '.cursor/rules',
            displayName: 'Cursor'
        },
        {
            type: 'windsurf',
            patterns: ['.windsurf/rules.md', '.windsurf'],
            defaultPath: '.windsurf/rules.md',
            displayName: 'Windsurf'
        },
        {
            type: 'continue',
            patterns: ['.continue/config.json'],
            defaultPath: '.continue/config.json',
            displayName: 'Continue'
        }
    ];
    fileWatcher;
    _onDidChangeIDEFiles = new vscode.EventEmitter();
    onDidChangeIDEFiles = this._onDidChangeIDEFiles.event;
    async detectIDEFiles(workspaceFolder) {
        const folders = workspaceFolder
            ? [workspaceFolder]
            : vscode.workspace.workspaceFolders || [];
        const ideFiles = [];
        for (const folder of folders) {
            for (const pattern of IDEDetectionService.IDE_PATTERNS) {
                for (const filePattern of pattern.patterns) {
                    const filePath = path.join(folder.uri.fsPath, filePattern);
                    try {
                        const uri = vscode.Uri.file(filePath);
                        const stat = await vscode.workspace.fs.stat(uri);
                        if (stat.type === vscode.FileType.File) {
                            const content = await vscode.workspace.fs.readFile(uri);
                            ideFiles.push({
                                path: filePath,
                                type: pattern.type,
                                content: Buffer.from(content).toString('utf8'),
                                lastModified: new Date(stat.mtime),
                                workspaceFolderUri: folder.uri.toString()
                            });
                        }
                    }
                    catch (error) {
                        // File doesn't exist, continue
                    }
                }
            }
        }
        return ideFiles;
    }
    watchIDEFiles() {
        // Create file watcher for all IDE patterns
        const patterns = IDEDetectionService.IDE_PATTERNS
            .flatMap(p => p.patterns)
            .map(p => `**/${p}`);
        const globPattern = `{${patterns.join(',')}}`;
        this.fileWatcher = vscode.workspace.createFileSystemWatcher(globPattern);
        // Handle file changes
        this.fileWatcher.onDidChange(async () => {
            const files = await this.detectIDEFiles();
            this._onDidChangeIDEFiles.fire(files);
        });
        this.fileWatcher.onDidCreate(async () => {
            const files = await this.detectIDEFiles();
            this._onDidChangeIDEFiles.fire(files);
        });
        this.fileWatcher.onDidDelete(async () => {
            const files = await this.detectIDEFiles();
            this._onDidChangeIDEFiles.fire(files);
        });
        return this.fileWatcher;
    }
    async findOrCreateIDEFile(type, workspaceFolder) {
        const folder = workspaceFolder || vscode.workspace.workspaceFolders?.[0];
        if (!folder) {
            throw new Error('No workspace folder found');
        }
        // Check if file already exists
        const existingFiles = await this.detectIDEFiles(folder);
        const existingFile = existingFiles.find(f => f.type === type);
        if (existingFile) {
            return existingFile;
        }
        // Create new file
        const pattern = IDEDetectionService.IDE_PATTERNS.find(p => p.type === type);
        if (!pattern) {
            throw new Error(`Unknown IDE type: ${type}`);
        }
        const filePath = path.join(folder.uri.fsPath, pattern.defaultPath);
        const dirPath = path.dirname(filePath);
        // Ensure directory exists
        try {
            await vscode.workspace.fs.createDirectory(vscode.Uri.file(dirPath));
        }
        catch (error) {
            // Directory might already exist
        }
        // Create empty file
        const content = this.getDefaultContent(type);
        await vscode.workspace.fs.writeFile(vscode.Uri.file(filePath), Buffer.from(content, 'utf8'));
        return {
            path: filePath,
            type,
            content,
            lastModified: new Date(),
            workspaceFolderUri: folder.uri.toString()
        };
    }
    getDefaultContent(type) {
        switch (type) {
            case 'claude':
                return '# CLAUDE.md\n\n<!-- Personality configuration will be added here -->\n';
            case 'cursor':
                return '# Cursor Rules\n\n<!-- Personality configuration will be added here -->\n';
            case 'windsurf':
                return '# Windsurf Rules\n\n<!-- Personality configuration will be added here -->\n';
            case 'continue':
                return '{\n  "rules": []\n}\n';
            default:
                return '';
        }
    }
    dispose() {
        this.fileWatcher?.dispose();
        this._onDidChangeIDEFiles.dispose();
    }
}
exports.IDEDetectionService = IDEDetectionService;
//# sourceMappingURL=ideDetectionService.js.map