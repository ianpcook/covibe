#!/usr/bin/env python3
"""
Configuration Management CLI for Covibe

This script provides command-line utilities for managing prompt templates
and LLM provider configurations.

Usage:
    python scripts/config-cli.py --help
    python scripts/config-cli.py prompt list
    python scripts/config-cli.py prompt create "My Prompt" "Content here"
    python scripts/config-cli.py llm test
    python scripts/config-cli.py backup list
"""

import sys
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.covibe.cli.config_manager import main
except ImportError:
    print("Error: Could not import configuration manager.")
    print("Make sure you're running this script from the project root directory.")
    print(f"Project root detected as: {project_root}")
    sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())