"""Database models for personality system persistence."""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class UserConfiguration(Base):
    """User configuration storage."""
    __tablename__ = "user_configurations"
    
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    personality_profiles = relationship("PersonalityProfileDB", back_populates="configuration", cascade="all, delete-orphan")
    config_history = relationship("ConfigurationHistory", back_populates="configuration", cascade="all, delete-orphan")


class PersonalityProfileDB(Base):
    """Personality profile database storage."""
    __tablename__ = "personality_profiles"
    
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    configuration_id: Mapped[str] = mapped_column(String(255), ForeignKey("user_configurations.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    personality_type: Mapped[str] = mapped_column(String(50), nullable=False)
    context: Mapped[str] = mapped_column(Text, nullable=False)
    ide_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    configuration = relationship("UserConfiguration", back_populates="personality_profiles")
    traits = relationship("PersonalityTraitDB", back_populates="profile", cascade="all, delete-orphan")
    communication_style = relationship("CommunicationStyleDB", back_populates="profile", uselist=False, cascade="all, delete-orphan")
    mannerisms = relationship("MannerismDB", back_populates="profile", cascade="all, delete-orphan")
    research_sources = relationship("ResearchSourceDB", back_populates="profile", cascade="all, delete-orphan")


class PersonalityTraitDB(Base):
    """Personality trait database storage."""
    __tablename__ = "personality_traits"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[str] = mapped_column(String(255), ForeignKey("personality_profiles.id"))
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    trait: Mapped[str] = mapped_column(String(255), nullable=False)
    intensity: Mapped[int] = mapped_column(Integer, nullable=False)
    examples: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    
    # Relationships
    profile = relationship("PersonalityProfileDB", back_populates="traits")


class CommunicationStyleDB(Base):
    """Communication style database storage."""
    __tablename__ = "communication_styles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[str] = mapped_column(String(255), ForeignKey("personality_profiles.id"))
    tone: Mapped[str] = mapped_column(String(100), nullable=False)
    formality: Mapped[str] = mapped_column(String(50), nullable=False)
    verbosity: Mapped[str] = mapped_column(String(50), nullable=False)
    technical_level: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Relationships
    profile = relationship("PersonalityProfileDB", back_populates="communication_style")


class MannerismDB(Base):
    """Mannerism database storage."""
    __tablename__ = "mannerisms"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[str] = mapped_column(String(255), ForeignKey("personality_profiles.id"))
    mannerism: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Relationships
    profile = relationship("PersonalityProfileDB", back_populates="mannerisms")


class ResearchSourceDB(Base):
    """Research source database storage."""
    __tablename__ = "research_sources"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[str] = mapped_column(String(255), ForeignKey("personality_profiles.id"))
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    # Relationships
    profile = relationship("PersonalityProfileDB", back_populates="research_sources")


class ConfigurationHistory(Base):
    """Configuration change history for versioning."""
    __tablename__ = "configuration_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    configuration_id: Mapped[str] = mapped_column(String(255), ForeignKey("user_configurations.id"))
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)  # CREATE, UPDATE, DELETE
    change_description: Mapped[str] = mapped_column(Text, nullable=False)
    data_snapshot: Mapped[str] = mapped_column(Text, nullable=False)  # JSON snapshot
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Relationships
    configuration = relationship("UserConfiguration", back_populates="config_history")


class ConfigurationBackup(Base):
    """Configuration backup storage."""
    __tablename__ = "configuration_backups"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    backup_name: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    backup_data: Mapped[str] = mapped_column(Text, nullable=False)  # JSON data
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256


# Database configuration
class DatabaseConfig:
    """Database configuration and session management."""
    
    def __init__(self, database_url: str = "sqlite+aiosqlite:///./personality_system.db"):
        self.database_url = database_url
        self.engine = create_async_engine(
            database_url,
            echo=False,
            future=True,
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    
    async def create_tables(self) -> None:
        """Create all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables(self) -> None:
        """Drop all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    async def get_session(self) -> AsyncSession:
        """Get async database session."""
        async with self.async_session() as session:
            yield session
    
    async def close(self) -> None:
        """Close database engine."""
        await self.engine.dispose()