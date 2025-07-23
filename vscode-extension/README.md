# Covibe VS Code Extension

AI Personality System for VS Code - Configure personality traits for your AI coding assistant.

## Features

- Create and manage AI personalities
- Activate personalities across workspaces  
- Native VS Code integration with tree view
- Import/export personality configurations
- Quick personality switching via status bar

## Installation

Install from VS Code marketplace (coming soon) or install from VSIX.

## Usage

1. Open the Covibe panel in the Activity Bar
2. Click "Create Personality" to create a new AI personality
3. Fill in the personality description
4. Activate the personality to apply it to your workspace

## Commands

- `Covibe: Create Personality` - Create a new AI personality
- `Covibe: List Personalities` - Show all personalities
- `Covibe: Activate Personality` - Activate a personality

## Development

```bash
npm install
npm run compile
# Press F5 to launch extension development host
```

## Testing Phase 1 MVP

To test the current implementation:

1. Open this project in VS Code
2. Press F5 to launch Extension Development Host
3. In the new window, look for Covibe icon in Activity Bar
4. Test personality creation and management

### Test Checklist

- [ ] Extension activates within 200ms
- [ ] Commands appear in Command Palette
- [ ] Tree view shows in sidebar
- [ ] Can create personalities
- [ ] Can activate personalities
- [ ] Status bar shows active personality
- [ ] Context menus work
- [ ] Import/export functionality

## Architecture

Built with TypeScript, esbuild bundling, and native VS Code APIs. No webviews - pure VS Code integration.