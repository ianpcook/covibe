# Covibe Documentation

Welcome to Covibe, the Agent Personality System that enhances your coding agents with configurable personality traits.

## Table of Contents

- [Quick Start Guide](./setup/quick-start.md)
- [Installation Guide](./setup/installation.md)
- [API Documentation](./api/README.md)
- [User Guide](./user-guide/README.md)
- [Developer Guide](./developer-guide/README.md)
- [Deployment Guide](./deployment/README.md)
- [Troubleshooting](./troubleshooting.md)

## What is Covibe?

Covibe transforms your coding experience by adding personality to your AI coding assistants. Whether you want your agent to respond like Tony Stark, Yoda, or a patient mentor, Covibe makes it possible.

### Key Features

- **Multiple Input Methods**: Web interface, REST API, and chat interface
- **Automatic Research**: Intelligent personality research from multiple sources
- **IDE Integration**: Native support for Cursor, Claude, Windsurf, and more
- **Persistent Configurations**: Save and manage multiple personality profiles
- **Real-time Chat**: Conversational personality configuration and refinement

### Supported IDEs

- **Cursor**: Creates `.mdc` files in `/cursor/rules/` directory
- **Claude**: Manages `CLAUDE.md` file in project root
- **Windsurf**: Handles `.windsurf` configuration files
- **Generic**: Provides multiple format options for manual integration

## Quick Start

1. **Install Covibe**
   ```bash
   pip install covibe
   # or
   docker run -p 8000:8000 covibe/backend
   ```

2. **Start the service**
   ```bash
   covibe start
   ```

3. **Open the web interface**
   Navigate to `http://localhost:8000` in your browser

4. **Configure a personality**
   - Enter a personality description (e.g., "Tony Stark")
   - Select your project directory
   - Click "Generate Configuration"

5. **Start coding**
   Your coding agent now has personality!

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │    │    REST API     │    │  Chat Interface │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │  Request Orchestrator     │
                    └─────────────┬─────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
┌─────────┴─────────┐   ┌─────────┴─────────┐   ┌─────────┴─────────┐
│ Personality       │   │ Context           │   │ IDE Integration   │
│ Research          │   │ Generation        │   │ System            │
└───────────────────┘   └───────────────────┘   └───────────────────┘
```

## Getting Help

- **Documentation**: Browse the guides in this documentation
- **API Reference**: Check the [OpenAPI specification](./api/openapi.yaml)
- **Issues**: Report bugs on [GitHub Issues](https://github.com/covibe/covibe/issues)
- **Support**: Email support@covibe.dev
- **Community**: Join our [Discord server](https://discord.gg/covibe)

## Contributing

We welcome contributions! See our [Contributing Guide](../CONTRIBUTING.md) for details.

## License

Covibe is released under the MIT License. See [LICENSE](../LICENSE) for details.