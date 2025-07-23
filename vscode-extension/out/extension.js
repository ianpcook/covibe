"use strict";
var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/extension.ts
var extension_exports = {};
__export(extension_exports, {
  activate: () => activate,
  deactivate: () => deactivate
});
module.exports = __toCommonJS(extension_exports);
var vscode10 = __toESM(require("vscode"));

// src/commands/commandManager.ts
var vscode3 = __toESM(require("vscode"));

// src/ui/quickPick.ts
var vscode = __toESM(require("vscode"));
async function showPersonalityInput() {
  return vscode.window.showInputBox({
    prompt: "Describe the AI personality you want",
    placeHolder: "e.g., Expert TypeScript developer focused on clean code and testing",
    validateInput: (value) => {
      if (!value || value.length < 10) {
        return "Please provide a more detailed description (at least 10 characters)";
      }
      if (value.length > 500) {
        return "Description is too long (max 500 characters)";
      }
      return null;
    }
  });
}
async function showPersonalityQuickPick(personalities, placeHolder = "Select a personality") {
  const items = personalities.map((p) => ({
    label: p.name,
    description: p.isActive ? "$(check) Active" : "",
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

// src/ui/progress.ts
var vscode2 = __toESM(require("vscode"));
async function withProgress(title, task) {
  return vscode2.window.withProgress({
    location: vscode2.ProgressLocation.Notification,
    title,
    cancellable: false
  }, task);
}

// src/commands/commandManager.ts
var CommandManager = class {
  constructor(context, personalityService2) {
    this.context = context;
    this.personalityService = personalityService2;
  }
  disposables = [];
  async registerCommands() {
    this.registerCommand("covibe.createPersonality", () => this.createPersonality());
    this.registerCommand("covibe.listPersonalities", () => this.listPersonalities());
    this.registerCommand("covibe.activatePersonality", () => this.activatePersonality());
    this.registerCommand("covibe.deletePersonality", (personalityId) => this.deletePersonality(personalityId));
    this.registerCommand("covibe.editPersonality", (personalityId) => this.editPersonality(personalityId));
    this.registerCommand("covibe.exportPersonality", (personalityId) => this.exportPersonality(personalityId));
    this.registerCommand("covibe.importPersonality", () => this.importPersonality());
    this.registerCommand("covibe.refreshPersonalities", () => this.refreshPersonalities());
  }
  registerCommand(command, callback) {
    const disposable = vscode3.commands.registerCommand(command, async (...args) => {
      try {
        await callback(...args);
      } catch (error) {
        console.error(`Command ${command} failed:`, error);
        vscode3.window.showErrorMessage(
          `Command failed: ${error instanceof Error ? error.message : "Unknown error"}`
        );
      }
    });
    this.disposables.push(disposable);
    this.context.subscriptions.push(disposable);
  }
  async createPersonality() {
    const name = await vscode3.window.showInputBox({
      prompt: "Enter a name for the personality",
      placeHolder: "e.g., Expert TypeScript Developer",
      validateInput: (value) => {
        if (!value || value.trim().length === 0) {
          return "Name is required";
        }
        if (value.length > 50) {
          return "Name is too long (max 50 characters)";
        }
        return null;
      }
    });
    if (!name) {
      return;
    }
    const description = await showPersonalityInput();
    if (!description) {
      return;
    }
    await withProgress("Creating personality...", async (progress) => {
      progress.report({ message: "Analyzing description..." });
      const personality = await this.personalityService.createPersonality(
        name.trim(),
        description.trim()
      );
      progress.report({ message: "Personality created!", increment: 100 });
      const activate2 = "Activate Now";
      const selection = await vscode3.window.showInformationMessage(
        `Personality "${personality.name}" created successfully!`,
        activate2
      );
      if (selection === activate2) {
        await this.personalityService.activatePersonality(personality.id);
        vscode3.window.showInformationMessage(`Personality "${personality.name}" is now active`);
      }
    });
  }
  async listPersonalities() {
    const personalities = await this.personalityService.getPersonalities();
    if (personalities.length === 0) {
      const create = "Create Personality";
      const selection = await vscode3.window.showInformationMessage(
        "No personalities found. Would you like to create one?",
        create
      );
      if (selection === create) {
        await this.createPersonality();
      }
      return;
    }
    const personality = await showPersonalityQuickPick(personalities);
    if (personality) {
      await this.personalityService.activatePersonality(personality.id);
      vscode3.window.showInformationMessage(`Activated personality: ${personality.name}`);
    }
  }
  async activatePersonality() {
    const personalities = await this.personalityService.getPersonalities();
    if (personalities.length === 0) {
      vscode3.window.showWarningMessage("No personalities available to activate");
      return;
    }
    const personality = await showPersonalityQuickPick(personalities);
    if (personality) {
      await this.personalityService.activatePersonality(personality.id);
      vscode3.window.showInformationMessage(`Activated personality: ${personality.name}`);
    }
  }
  async deletePersonality(personalityId) {
    let personality;
    if (personalityId) {
      personality = await this.personalityService.getPersonality(personalityId);
    } else {
      const personalities = await this.personalityService.getPersonalities();
      personality = await showPersonalityQuickPick(personalities, "Select personality to delete");
    }
    if (!personality) {
      return;
    }
    const confirm = await vscode3.window.showWarningMessage(
      `Are you sure you want to delete "${personality.name}"?`,
      { modal: true },
      "Delete"
    );
    if (confirm === "Delete") {
      await this.personalityService.deletePersonality(personality.id);
      vscode3.window.showInformationMessage(`Deleted personality: ${personality.name}`);
    }
  }
  async editPersonality(personalityId) {
    let personality;
    if (personalityId) {
      personality = await this.personalityService.getPersonality(personalityId);
    } else {
      const personalities = await this.personalityService.getPersonalities();
      personality = await showPersonalityQuickPick(personalities, "Select personality to edit");
    }
    if (!personality) {
      return;
    }
    const newDescription = await vscode3.window.showInputBox({
      prompt: "Edit personality description",
      value: personality.description,
      validateInput: (value) => {
        if (!value || value.length < 10) {
          return "Please provide a more detailed description";
        }
        if (value.length > 500) {
          return "Description is too long (max 500 characters)";
        }
        return null;
      }
    });
    if (newDescription && newDescription !== personality.description) {
      await this.personalityService.updatePersonality(personality.id, {
        description: newDescription
      });
      vscode3.window.showInformationMessage(`Updated personality: ${personality.name}`);
    }
  }
  async exportPersonality(personalityId) {
    let personality;
    if (personalityId) {
      personality = await this.personalityService.getPersonality(personalityId);
    } else {
      const personalities = await this.personalityService.getPersonalities();
      personality = await showPersonalityQuickPick(personalities, "Select personality to export");
    }
    if (!personality) {
      return;
    }
    const exportData = await this.personalityService.exportPersonality(personality.id);
    const uri = await vscode3.window.showSaveDialog({
      defaultUri: vscode3.Uri.file(`${personality.name.replace(/\s+/g, "-").toLowerCase()}.json`),
      filters: {
        "JSON files": ["json"]
      }
    });
    if (uri) {
      await vscode3.workspace.fs.writeFile(uri, Buffer.from(exportData, "utf8"));
      vscode3.window.showInformationMessage(`Exported personality to ${uri.fsPath}`);
    }
  }
  async importPersonality() {
    const uri = await vscode3.window.showOpenDialog({
      canSelectFiles: true,
      canSelectFolders: false,
      canSelectMany: false,
      filters: {
        "JSON files": ["json"]
      }
    });
    if (!uri || uri.length === 0) {
      return;
    }
    try {
      const data = await vscode3.workspace.fs.readFile(uri[0]);
      const jsonStr = Buffer.from(data).toString("utf8");
      const personality = await this.personalityService.importPersonality(jsonStr);
      const activate2 = "Activate Now";
      const selection = await vscode3.window.showInformationMessage(
        `Imported personality: ${personality.name}`,
        activate2
      );
      if (selection === activate2) {
        await this.personalityService.activatePersonality(personality.id);
      }
    } catch (error) {
      vscode3.window.showErrorMessage(
        `Failed to import personality: ${error instanceof Error ? error.message : "Unknown error"}`
      );
    }
  }
  async refreshPersonalities() {
    vscode3.window.showInformationMessage("Refreshed personalities");
  }
  dispose() {
    this.disposables.forEach((d) => d.dispose());
  }
};

// src/views/personalityTreeProvider.ts
var vscode4 = __toESM(require("vscode"));
var PersonalityTreeItem = class extends vscode4.TreeItem {
  constructor(personality, collapsibleState) {
    super(personality.name, collapsibleState);
    this.personality = personality;
    this.collapsibleState = collapsibleState;
    this.tooltip = new vscode4.MarkdownString(this.getTooltipContent());
    this.description = personality.isActive ? "Active" : "";
    this.contextValue = personality.isActive ? "activePersonality" : "personality";
    this.iconPath = new vscode4.ThemeIcon(
      personality.isActive ? "circle-filled" : "circle-outline"
    );
  }
  getTooltipContent() {
    const traits = this.personality.traits.slice(0, 3).map((t) => `- ${t.name}: ${t.value}`).join("\n");
    return `**${this.personality.name}**

${this.personality.description}

**Key Traits:**
${traits}`;
  }
};
var PersonalityTreeProvider = class {
  constructor(personalityService2) {
    this.personalityService = personalityService2;
    personalityService2.onDidChangePersonalities(() => {
      this.refresh();
    });
  }
  _onDidChangeTreeData = new vscode4.EventEmitter();
  onDidChangeTreeData = this._onDidChangeTreeData.event;
  refresh() {
    this._onDidChangeTreeData.fire();
  }
  getTreeItem(element) {
    return element;
  }
  async getChildren(element) {
    if (!element) {
      const personalities = await this.personalityService.getPersonalities();
      personalities.sort((a, b) => {
        if (a.isActive && !b.isActive)
          return -1;
        if (!a.isActive && b.isActive)
          return 1;
        return a.name.localeCompare(b.name);
      });
      return personalities.map((p) => new PersonalityTreeItem(p, vscode4.TreeItemCollapsibleState.None));
    }
    return [];
  }
  async getParent(_element) {
    return void 0;
  }
};

// src/services/personalityService.ts
var vscode7 = __toESM(require("vscode"));

// src/utils/helpers.ts
function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substring(2);
}

// src/services/ideDetectionService.ts
var vscode5 = __toESM(require("vscode"));
var path = __toESM(require("path"));
var IDEDetectionService = class _IDEDetectionService {
  static IDE_PATTERNS = [
    {
      type: "claude",
      patterns: ["CLAUDE.md", "claude.md"],
      defaultPath: "CLAUDE.md",
      displayName: "Claude"
    },
    {
      type: "cursor",
      patterns: [".cursor/rules", ".cursor-rules"],
      defaultPath: ".cursor/rules",
      displayName: "Cursor"
    },
    {
      type: "windsurf",
      patterns: [".windsurf/rules.md", ".windsurf"],
      defaultPath: ".windsurf/rules.md",
      displayName: "Windsurf"
    },
    {
      type: "continue",
      patterns: [".continue/config.json"],
      defaultPath: ".continue/config.json",
      displayName: "Continue"
    }
  ];
  fileWatcher;
  _onDidChangeIDEFiles = new vscode5.EventEmitter();
  onDidChangeIDEFiles = this._onDidChangeIDEFiles.event;
  async detectIDEFiles(workspaceFolder) {
    const folders = workspaceFolder ? [workspaceFolder] : vscode5.workspace.workspaceFolders || [];
    const ideFiles = [];
    for (const folder of folders) {
      for (const pattern of _IDEDetectionService.IDE_PATTERNS) {
        for (const filePattern of pattern.patterns) {
          const filePath = path.join(folder.uri.fsPath, filePattern);
          try {
            const uri = vscode5.Uri.file(filePath);
            const stat = await vscode5.workspace.fs.stat(uri);
            if (stat.type === vscode5.FileType.File) {
              const content = await vscode5.workspace.fs.readFile(uri);
              ideFiles.push({
                path: filePath,
                type: pattern.type,
                content: Buffer.from(content).toString("utf8"),
                lastModified: new Date(stat.mtime),
                workspaceFolderUri: folder.uri.toString()
              });
            }
          } catch (error) {
          }
        }
      }
    }
    return ideFiles;
  }
  watchIDEFiles() {
    const patterns = _IDEDetectionService.IDE_PATTERNS.flatMap((p) => p.patterns).map((p) => `**/${p}`);
    const globPattern = `{${patterns.join(",")}}`;
    this.fileWatcher = vscode5.workspace.createFileSystemWatcher(globPattern);
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
    const folder = workspaceFolder || vscode5.workspace.workspaceFolders?.[0];
    if (!folder) {
      throw new Error("No workspace folder found");
    }
    const existingFiles = await this.detectIDEFiles(folder);
    const existingFile = existingFiles.find((f) => f.type === type);
    if (existingFile) {
      return existingFile;
    }
    const pattern = _IDEDetectionService.IDE_PATTERNS.find((p) => p.type === type);
    if (!pattern) {
      throw new Error(`Unknown IDE type: ${type}`);
    }
    const filePath = path.join(folder.uri.fsPath, pattern.defaultPath);
    const dirPath = path.dirname(filePath);
    try {
      await vscode5.workspace.fs.createDirectory(vscode5.Uri.file(dirPath));
    } catch (error) {
    }
    const content = this.getDefaultContent(type);
    await vscode5.workspace.fs.writeFile(
      vscode5.Uri.file(filePath),
      Buffer.from(content, "utf8")
    );
    return {
      path: filePath,
      type,
      content,
      lastModified: /* @__PURE__ */ new Date(),
      workspaceFolderUri: folder.uri.toString()
    };
  }
  getDefaultContent(type) {
    switch (type) {
      case "claude":
        return "# CLAUDE.md\n\n<!-- Personality configuration will be added here -->\n";
      case "cursor":
        return "# Cursor Rules\n\n<!-- Personality configuration will be added here -->\n";
      case "windsurf":
        return "# Windsurf Rules\n\n<!-- Personality configuration will be added here -->\n";
      case "continue":
        return '{\n  "rules": []\n}\n';
      default:
        return "";
    }
  }
  dispose() {
    this.fileWatcher?.dispose();
    this._onDidChangeIDEFiles.dispose();
  }
};

// src/services/ideWriterService.ts
var vscode6 = __toESM(require("vscode"));
var IDEWriterService = class {
  async applyPersonalityToIDE(personality, ideFile) {
    const updatedContent = this.generateIDEContent(personality, ideFile);
    const proceed = await this.showDiffAndConfirm(ideFile, updatedContent);
    if (!proceed) {
      return;
    }
    await this.backupFile(ideFile);
    await vscode6.workspace.fs.writeFile(
      vscode6.Uri.file(ideFile.path),
      Buffer.from(updatedContent, "utf8")
    );
    vscode6.window.showInformationMessage(
      `Updated ${ideFile.type.toUpperCase()} configuration with personality: ${personality.name}`
    );
  }
  generateIDEContent(personality, ideFile) {
    switch (ideFile.type) {
      case "claude":
        return this.generateClaudeContent(personality, ideFile.content);
      case "cursor":
        return this.generateCursorContent(personality);
      case "windsurf":
        return this.generateWindsurfContent(personality);
      case "continue":
        return this.generateContinueContent(personality, ideFile.content);
      default:
        throw new Error(`Unsupported IDE type: ${ideFile.type}`);
    }
  }
  generateClaudeContent(personality, existingContent) {
    const hasExistingInstructions = existingContent.includes("# CLAUDE.md") || existingContent.includes("# Claude Instructions");
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
      const personalityMarkerStart = "# Claude Personality Configuration";
      const personalityMarkerEnd = "## Implementation Notes";
      if (existingContent.includes(personalityMarkerStart)) {
        const startIndex = existingContent.indexOf(personalityMarkerStart);
        const endIndex = existingContent.indexOf("\n\n", existingContent.indexOf(personalityMarkerEnd));
        return existingContent.substring(0, startIndex) + personalitySection.trim() + existingContent.substring(endIndex);
      } else {
        return personalitySection + "\n\n" + existingContent;
      }
    } else {
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
        traits: personality.traits.map((t) => ({
          category: t.category,
          name: t.name,
          value: t.value
        }))
      };
      return JSON.stringify(config, null, 2);
    } catch (error) {
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
    return Object.entries(traitsByCategory).map(([category, traits]) => {
      const categoryTitle = category.charAt(0).toUpperCase() + category.slice(1);
      const traitsList = traits.sort((a, b) => {
        const priorityOrder = { high: 0, medium: 1, low: 2 };
        return priorityOrder[a.priority] - priorityOrder[b.priority];
      }).map((t) => `- **${t.name}**: ${t.value} (${t.priority} priority)`).join("\n");
      return `### ${categoryTitle} Traits:
${traitsList}`;
    }).join("\n\n");
  }
  async showDiffAndConfirm(ideFile, _newContent) {
    const action = await vscode6.window.showInformationMessage(
      `Update ${ideFile.type.toUpperCase()} configuration file?`,
      { modal: true },
      "Update",
      "Cancel"
    );
    return action === "Update";
  }
  async backupFile(ideFile) {
    const backupPath = `${ideFile.path}.backup-${Date.now()}`;
    try {
      await vscode6.workspace.fs.copy(
        vscode6.Uri.file(ideFile.path),
        vscode6.Uri.file(backupPath),
        { overwrite: false }
      );
    } catch (error) {
    }
  }
};

// src/services/personalityService.ts
var PersonalityService = class {
  constructor(globalState, workspaceState) {
    this.globalState = globalState;
    this.workspaceState = workspaceState;
    this.ideDetectionService = new IDEDetectionService();
    this.ideWriterService = new IDEWriterService();
    this.loadPersonalities();
  }
  STORAGE_KEY = "covibe.personalities";
  personalities = /* @__PURE__ */ new Map();
  _onDidChangePersonalities = new vscode7.EventEmitter();
  onDidChangePersonalities = this._onDidChangePersonalities.event;
  ideDetectionService;
  ideWriterService;
  async loadPersonalities() {
    const stored = this.globalState.get(this.STORAGE_KEY, {});
    this.personalities.clear();
    for (const [id, personality] of Object.entries(stored)) {
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
    const id = generateId();
    const now = /* @__PURE__ */ new Date();
    const personality = {
      id,
      name,
      description,
      traits: traits || this.generateDefaultTraits(description),
      context: this.generateContext(name, description),
      isActive: false,
      created: now,
      modified: now,
      version: "1.0.0"
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
    return void 0;
  }
  async activatePersonality(id) {
    for (const personality2 of this.personalities.values()) {
      personality2.isActive = false;
    }
    const personality = this.personalities.get(id);
    if (personality) {
      personality.isActive = true;
      personality.workspaceId = vscode7.workspace.workspaceFolders?.[0]?.uri.toString();
      await this.savePersonalities();
      await this.workspaceState.update("activePersonalityId", id);
      await this.workspaceState.update("defaultPersonalityId", id);
      await this.applyPersonalityToWorkspace(personality);
    }
  }
  async applyPersonalityToWorkspace(personality) {
    try {
      if (!vscode7.workspace.isTrusted) {
        vscode7.window.showWarningMessage(
          "Cannot update IDE files in untrusted workspace"
        );
        return;
      }
      const ideFiles = await this.ideDetectionService.detectIDEFiles();
      if (ideFiles.length === 0) {
        const ideTypes = ["claude", "cursor", "windsurf"];
        const selection = await vscode7.window.showQuickPick(ideTypes, {
          placeHolder: "No AI IDE files found. Which one would you like to create?",
          canPickMany: false
        });
        if (selection) {
          const ideFile = await this.ideDetectionService.findOrCreateIDEFile(
            selection
          );
          await this.ideWriterService.applyPersonalityToIDE(personality, ideFile);
        }
      } else {
        for (const ideFile of ideFiles) {
          await this.ideWriterService.applyPersonalityToIDE(personality, ideFile);
        }
      }
    } catch (error) {
      console.error("Failed to apply personality to workspace:", error);
      vscode7.window.showErrorMessage(
        `Failed to update IDE files: ${error instanceof Error ? error.message : "Unknown error"}`
      );
    }
  }
  async updatePersonality(id, updates) {
    const personality = this.personalities.get(id);
    if (personality) {
      Object.assign(personality, updates);
      personality.modified = /* @__PURE__ */ new Date();
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
      throw new Error("Personality not found");
    }
    const exportData = {
      ...personality,
      exportVersion: "1.0",
      exportDate: (/* @__PURE__ */ new Date()).toISOString()
    };
    return JSON.stringify(exportData, null, 2);
  }
  async importPersonality(data) {
    try {
      const parsed = JSON.parse(data);
      if (!parsed.name || !parsed.description || !parsed.traits) {
        throw new Error("Invalid personality data: missing required fields");
      }
      return await this.createPersonality(
        parsed.name,
        parsed.description,
        parsed.traits
      );
    } catch (error) {
      throw new Error(`Failed to import personality: ${error instanceof Error ? error.message : "Invalid JSON"}`);
    }
  }
  generateDefaultTraits(description) {
    const traits = [];
    const lowerDesc = description.toLowerCase();
    if (lowerDesc.includes("typescript") || lowerDesc.includes("javascript")) {
      traits.push({
        category: "technical",
        name: "Language expertise",
        value: "Expert in TypeScript/JavaScript development",
        priority: "high"
      });
    }
    if (lowerDesc.includes("clean") || lowerDesc.includes("quality")) {
      traits.push({
        category: "technical",
        name: "Code quality",
        value: "Emphasizes clean, maintainable code",
        priority: "high"
      });
    }
    if (lowerDesc.includes("patient") || lowerDesc.includes("helpful")) {
      traits.push({
        category: "communication",
        name: "Teaching style",
        value: "Patient and thorough explanations",
        priority: "medium"
      });
    }
    if (traits.length === 0) {
      traits.push({
        category: "communication",
        name: "General approach",
        value: "Professional and helpful",
        priority: "medium"
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
};

// src/ui/statusBarManager.ts
var vscode8 = __toESM(require("vscode"));
var StatusBarManager = class {
  constructor(personalityService2) {
    this.personalityService = personalityService2;
    this.statusBarItem = vscode8.window.createStatusBarItem(
      vscode8.StatusBarAlignment.Right,
      100
    );
    this.statusBarItem.command = "covibe.listPersonalities";
    this.statusBarItem.tooltip = "Click to switch personality";
    this.disposables.push(
      this.personalityService.onDidChangePersonalities(() => this.updateStatusBar())
    );
    this.disposables.push(
      vscode8.workspace.onDidChangeConfiguration((e) => {
        if (e.affectsConfiguration("covibe.showStatusBar")) {
          this.updateStatusBar();
        }
      })
    );
    this.updateStatusBar();
  }
  statusBarItem;
  disposables = [];
  async updateStatusBar() {
    const config = vscode8.workspace.getConfiguration("covibe");
    const showStatusBar = config.get("showStatusBar", true);
    if (!showStatusBar) {
      this.statusBarItem.hide();
      return;
    }
    const activePersonality = await this.personalityService.getActivePersonality();
    if (activePersonality) {
      this.statusBarItem.text = `$(robot) ${activePersonality.name}`;
      this.statusBarItem.show();
    } else {
      this.statusBarItem.text = "$(robot) No Active Personality";
      this.statusBarItem.show();
    }
  }
  dispose() {
    this.statusBarItem.dispose();
    this.disposables.forEach((d) => d.dispose());
  }
};

// src/utils/telemetry.ts
var vscode9 = __toESM(require("vscode"));
var ActivationTelemetry = class {
  extensionId;
  extensionVersion;
  constructor(context) {
    const packageJson = context.extension.packageJSON;
    this.extensionId = packageJson.name;
    this.extensionVersion = packageJson.version;
  }
  async reportActivation() {
    if (!vscode9.env.isTelemetryEnabled) {
      return;
    }
    console.log(`Extension activated: ${this.extensionId} v${this.extensionVersion}`);
    console.log(`VS Code version: ${vscode9.version}`);
    console.log(`Platform: ${process.platform}`);
  }
  reportCommand(command, properties) {
    if (!vscode9.env.isTelemetryEnabled) {
      return;
    }
    console.log(`Command executed: ${command}`, properties);
  }
  reportError(error, context) {
    console.error(`Error in ${context || "unknown context"}:`, error);
  }
};

// src/extension.ts
var commandManager;
var personalityService;
var treeProvider;
var statusBarManager;
async function activate(context) {
  const startTime = Date.now();
  try {
    const telemetry = new ActivationTelemetry(context);
    await telemetry.reportActivation();
    personalityService = new PersonalityService(context.globalState, context.workspaceState);
    context.subscriptions.push(
      personalityService["ideDetectionService"].watchIDEFiles()
    );
    commandManager = new CommandManager(context, personalityService);
    await commandManager.registerCommands();
    treeProvider = new PersonalityTreeProvider(personalityService);
    const treeView = vscode10.window.createTreeView("covibe.personalities", {
      treeDataProvider: treeProvider,
      showCollapseAll: true
    });
    context.subscriptions.push(treeView);
    statusBarManager = new StatusBarManager(personalityService);
    context.subscriptions.push(statusBarManager);
    const hasShownWelcome = context.globalState.get("hasShownWelcome", false);
    if (!hasShownWelcome) {
      const showWalkthrough = "Show Walkthrough";
      const selection = await vscode10.window.showInformationMessage(
        "Welcome to Covibe! Configure personality traits for your AI coding assistant.",
        showWalkthrough
      );
      if (selection === showWalkthrough) {
        vscode10.window.showInformationMessage("Quick start: Use the Covibe view in the Activity Bar to create your first personality!");
      }
      await context.globalState.update("hasShownWelcome", true);
    }
    const activationTime = Date.now() - startTime;
    console.log(`Covibe extension activated in ${activationTime}ms`);
    const config = vscode10.workspace.getConfiguration("covibe");
    if (config.get("autoActivatePersonality")) {
      const defaultPersonalityId = context.workspaceState.get("defaultPersonalityId");
      if (defaultPersonalityId) {
        await personalityService.activatePersonality(defaultPersonalityId);
      }
    }
  } catch (error) {
    console.error("Failed to activate Covibe extension:", error);
    vscode10.window.showErrorMessage(`Failed to activate Covibe: ${error instanceof Error ? error.message : "Unknown error"}`);
  }
}
function deactivate() {
  commandManager?.dispose();
  statusBarManager?.dispose();
  console.log("Covibe extension deactivated");
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  activate,
  deactivate
});
//# sourceMappingURL=extension.js.map
