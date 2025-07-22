"""Database utilities and initialization."""

import os
from pathlib import Path
from typing import Optional

from ..models.database import DatabaseConfig


async def initialize_database(database_url: Optional[str] = None) -> DatabaseConfig:
    """Initialize database with tables and return config."""
    if not database_url:
        database_url = os.getenv(
            "DATABASE_URL",
            "sqlite+aiosqlite:///./personality_system.db"
        )
    
    db_config = DatabaseConfig(database_url)
    await db_config.create_tables()
    return db_config


async def get_database_config() -> DatabaseConfig:
    """Get database configuration from environment or default."""
    database_url = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./personality_system.db"
    )
    return DatabaseConfig(database_url)


async def reset_database(database_url: Optional[str] = None) -> DatabaseConfig:
    """Reset database by dropping and recreating all tables."""
    if not database_url:
        database_url = os.getenv(
            "DATABASE_URL",
            "sqlite+aiosqlite:///./personality_system.db"
        )
    
    db_config = DatabaseConfig(database_url)
    await db_config.drop_tables()
    await db_config.create_tables()
    return db_config