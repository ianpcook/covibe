"""Configuration persistence and management service."""

import json
import hashlib
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from uuid import uuid4

from sqlalchemy import select, delete, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.core import (
    PersonalityConfig,
    PersonalityProfile,
    PersonalityTrait,
    CommunicationStyle,
    ResearchSource,
    PersonalityType,
    FormalityLevel,
    VerbosityLevel,
    TechnicalLevel,
)
from ..models.database import (
    UserConfiguration,
    PersonalityProfileDB,
    PersonalityTraitDB,
    CommunicationStyleDB,
    MannerismDB,
    ResearchSourceDB,
    ConfigurationHistory,
    ConfigurationBackup,
    DatabaseConfig,
)


class ConfigurationPersistenceService:
    """Service for managing configuration persistence and CRUD operations."""
    
    def __init__(self, db_config: DatabaseConfig):
        self.db_config = db_config
    
    async def create_configuration(
        self,
        config: PersonalityConfig,
        user_id: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> str:
        """Create a new personality configuration."""
        async with self.db_config.async_session() as session:
            # Create user configuration
            user_config = UserConfiguration(
                id=config.id,
                user_id=user_id,
                name=config.profile.name,
                description=f"Personality configuration for {config.profile.name}",
                active=config.active,
            )
            session.add(user_config)
            
            # Create personality profile
            profile_db = await self._create_personality_profile_db(
                session, config.profile, config.id
            )
            
            # Create history entry
            await self._create_history_entry(
                session,
                config.id,
                "CREATE",
                f"Created configuration for {config.profile.name}",
                config.model_dump(),
                created_by,
            )
            
            await session.commit()
            return config.id
    
    async def get_configuration(self, config_id: str) -> Optional[PersonalityConfig]:
        """Retrieve a personality configuration by ID."""
        async with self.db_config.async_session() as session:
            stmt = (
                select(UserConfiguration)
                .options(
                    selectinload(UserConfiguration.personality_profiles)
                    .selectinload(PersonalityProfileDB.traits),
                    selectinload(UserConfiguration.personality_profiles)
                    .selectinload(PersonalityProfileDB.communication_style),
                    selectinload(UserConfiguration.personality_profiles)
                    .selectinload(PersonalityProfileDB.mannerisms),
                    selectinload(UserConfiguration.personality_profiles)
                    .selectinload(PersonalityProfileDB.research_sources),
                )
                .where(UserConfiguration.id == config_id)
            )
            result = await session.execute(stmt)
            user_config = result.scalar_one_or_none()
            
            if not user_config or not user_config.personality_profiles:
                return None
            
            # Convert database model to Pydantic model
            profile_db = user_config.personality_profiles[0]  # Assuming one profile per config
            profile = await self._convert_db_to_profile(profile_db)
            
            return PersonalityConfig(
                id=user_config.id,
                profile=profile,
                context=profile_db.context,
                ide_type=profile_db.ide_type,
                file_path=profile_db.file_path,
                active=user_config.active,
                created_at=user_config.created_at,
                updated_at=user_config.updated_at,
            )
    
    async def update_configuration(
        self,
        config_id: str,
        config: PersonalityConfig,
        updated_by: Optional[str] = None,
    ) -> bool:
        """Update an existing personality configuration."""
        async with self.db_config.async_session() as session:
            # Get existing configuration
            existing = await session.get(UserConfiguration, config_id)
            if not existing:
                return False
            
            # Update user configuration
            existing.name = config.profile.name
            existing.active = config.active
            existing.updated_at = datetime.utcnow()
            
            # Delete existing profile data
            await session.execute(
                delete(PersonalityProfileDB).where(
                    PersonalityProfileDB.configuration_id == config_id
                )
            )
            
            # Create new profile data
            await self._create_personality_profile_db(
                session, config.profile, config_id
            )
            
            # Create history entry
            await self._create_history_entry(
                session,
                config_id,
                "UPDATE",
                f"Updated configuration for {config.profile.name}",
                config.model_dump(),
                updated_by,
            )
            
            await session.commit()
            return True
    
    async def delete_configuration(
        self,
        config_id: str,
        deleted_by: Optional[str] = None,
    ) -> bool:
        """Delete a personality configuration."""
        async with self.db_config.async_session() as session:
            # Get existing configuration for history
            existing = await session.get(UserConfiguration, config_id)
            if not existing:
                return False
            
            # Create history entry before deletion
            await self._create_history_entry(
                session,
                config_id,
                "DELETE",
                f"Deleted configuration for {existing.name}",
                {"id": config_id, "name": existing.name},
                deleted_by,
            )
            
            # Delete configuration (cascades to related data)
            await session.execute(
                delete(UserConfiguration).where(UserConfiguration.id == config_id)
            )
            
            await session.commit()
            return True
    
    async def list_configurations(
        self,
        user_id: Optional[str] = None,
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> List[PersonalityConfig]:
        """List personality configurations with optional filtering."""
        async with self.db_config.async_session() as session:
            stmt = (
                select(UserConfiguration)
                .options(
                    selectinload(UserConfiguration.personality_profiles)
                    .selectinload(PersonalityProfileDB.traits),
                    selectinload(UserConfiguration.personality_profiles)
                    .selectinload(PersonalityProfileDB.communication_style),
                    selectinload(UserConfiguration.personality_profiles)
                    .selectinload(PersonalityProfileDB.mannerisms),
                    selectinload(UserConfiguration.personality_profiles)
                    .selectinload(PersonalityProfileDB.research_sources),
                )
                .limit(limit)
                .offset(offset)
                .order_by(UserConfiguration.updated_at.desc())
            )
            
            if user_id:
                stmt = stmt.where(UserConfiguration.user_id == user_id)
            if active_only:
                stmt = stmt.where(UserConfiguration.active == True)
            
            result = await session.execute(stmt)
            user_configs = result.scalars().all()
            
            configurations = []
            for user_config in user_configs:
                if user_config.personality_profiles:
                    profile_db = user_config.personality_profiles[0]
                    profile = await self._convert_db_to_profile(profile_db)
                    
                    configurations.append(
                        PersonalityConfig(
                            id=user_config.id,
                            profile=profile,
                            context=profile_db.context,
                            ide_type=profile_db.ide_type,
                            file_path=profile_db.file_path,
                            active=user_config.active,
                            created_at=user_config.created_at,
                            updated_at=user_config.updated_at,
                        )
                    )
            
            return configurations
    
    async def get_configuration_history(
        self,
        config_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get configuration change history."""
        async with self.db_config.async_session() as session:
            stmt = (
                select(ConfigurationHistory)
                .where(ConfigurationHistory.configuration_id == config_id)
                .order_by(ConfigurationHistory.created_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            history_entries = result.scalars().all()
            
            return [
                {
                    "id": entry.id,
                    "version": entry.version,
                    "change_type": entry.change_type,
                    "change_description": entry.change_description,
                    "created_at": entry.created_at,
                    "created_by": entry.created_by,
                    "data_snapshot": json.loads(entry.data_snapshot),
                }
                for entry in history_entries
            ]
    
    async def restore_configuration_version(
        self,
        config_id: str,
        version: int,
        restored_by: Optional[str] = None,
    ) -> bool:
        """Restore configuration to a specific version."""
        async with self.db_config.async_session() as session:
            # Get the version data
            stmt = (
                select(ConfigurationHistory)
                .where(
                    ConfigurationHistory.configuration_id == config_id,
                    ConfigurationHistory.version == version,
                )
            )
            result = await session.execute(stmt)
            history_entry = result.scalar_one_or_none()
            
            if not history_entry:
                return False
            
            # Parse the snapshot data
            snapshot_data = json.loads(history_entry.data_snapshot)
            config = PersonalityConfig(**snapshot_data)
            
            # Update the configuration
            return await self.update_configuration(
                config_id, config, f"system_restore_v{version}"
            )
    
    async def create_backup(
        self,
        backup_name: str,
        user_id: Optional[str] = None,
        config_ids: Optional[List[str]] = None,
    ) -> str:
        """Create a backup of configurations."""
        async with self.db_config.async_session() as session:
            # Get configurations to backup
            if config_ids:
                configurations = []
                for config_id in config_ids:
                    config = await self.get_configuration(config_id)
                    if config:
                        configurations.append(config)
            else:
                configurations = await self.list_configurations(
                    user_id=user_id, active_only=False
                )
            
            # Create backup data
            backup_data = {
                "version": "1.0",
                "created_at": datetime.utcnow().isoformat(),
                "configurations": [config.model_dump() for config in configurations],
            }
            
            # Convert data_snapshot to JSON-serializable format
            def json_serializer(obj):
                """JSON serializer for objects not serializable by default json code"""
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
            
            backup_json = json.dumps(backup_data, indent=2, default=json_serializer)
            backup_size = len(backup_json.encode('utf-8'))
            backup_checksum = hashlib.sha256(backup_json.encode('utf-8')).hexdigest()
            
            # Store backup
            backup = ConfigurationBackup(
                backup_name=backup_name,
                user_id=user_id,
                backup_data=backup_json,
                file_size=backup_size,
                checksum=backup_checksum,
            )
            session.add(backup)
            await session.commit()
            
            return backup_checksum
    
    async def restore_backup(
        self,
        backup_id: int,
        restored_by: Optional[str] = None,
    ) -> Tuple[bool, List[str]]:
        """Restore configurations from backup."""
        async with self.db_config.async_session() as session:
            backup = await session.get(ConfigurationBackup, backup_id)
            if not backup:
                return False, ["Backup not found"]
            
            # Verify backup integrity
            backup_checksum = hashlib.sha256(backup.backup_data.encode('utf-8')).hexdigest()
            if backup_checksum != backup.checksum:
                return False, ["Backup integrity check failed"]
            
            # Parse backup data
            try:
                backup_data = json.loads(backup.backup_data)
                configurations = backup_data.get("configurations", [])
            except json.JSONDecodeError:
                return False, ["Invalid backup data format"]
            
            # Restore configurations
            restored_configs = []
            errors = []
            
            for config_data in configurations:
                try:
                    config = PersonalityConfig(**config_data)
                    await self.create_configuration(
                        config, backup.user_id, f"backup_restore_{restored_by}"
                    )
                    restored_configs.append(config.id)
                except Exception as e:
                    errors.append(f"Failed to restore {config_data.get('id', 'unknown')}: {str(e)}")
            
            return len(restored_configs) > 0, errors
    
    async def list_backups(
        self,
        user_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List available backups."""
        async with self.db_config.async_session() as session:
            stmt = (
                select(ConfigurationBackup)
                .order_by(ConfigurationBackup.created_at.desc())
                .limit(limit)
            )
            
            if user_id:
                stmt = stmt.where(ConfigurationBackup.user_id == user_id)
            
            result = await session.execute(stmt)
            backups = result.scalars().all()
            
            return [
                {
                    "id": backup.id,
                    "backup_name": backup.backup_name,
                    "user_id": backup.user_id,
                    "created_at": backup.created_at,
                    "file_size": backup.file_size,
                    "checksum": backup.checksum,
                }
                for backup in backups
            ]
    
    async def _create_personality_profile_db(
        self,
        session: AsyncSession,
        profile: PersonalityProfile,
        config_id: str,
    ) -> PersonalityProfileDB:
        """Create personality profile database entries."""
        # Create main profile
        profile_db = PersonalityProfileDB(
            id=profile.id,
            configuration_id=config_id,
            name=profile.name,
            personality_type=profile.type.value,
            context="",  # Will be set by context generation
            ide_type="",  # Will be set by IDE integration
            file_path="",  # Will be set by IDE integration
        )
        session.add(profile_db)
        
        # Create traits
        for trait in profile.traits:
            trait_db = PersonalityTraitDB(
                profile_id=profile.id,
                category=trait.category,
                trait=trait.trait,
                intensity=trait.intensity,
                examples=json.dumps(trait.examples),
            )
            session.add(trait_db)
        
        # Create communication style
        style_db = CommunicationStyleDB(
            profile_id=profile.id,
            tone=profile.communication_style.tone,
            formality=profile.communication_style.formality.value,
            verbosity=profile.communication_style.verbosity.value,
            technical_level=profile.communication_style.technical_level.value,
        )
        session.add(style_db)
        
        # Create mannerisms
        for mannerism in profile.mannerisms:
            mannerism_db = MannerismDB(
                profile_id=profile.id,
                mannerism=mannerism,
            )
            session.add(mannerism_db)
        
        # Create research sources
        for source in profile.sources:
            source_db = ResearchSourceDB(
                profile_id=profile.id,
                source_type=source.type,
                url=source.url,
                confidence=source.confidence,
                last_updated=source.last_updated,
            )
            session.add(source_db)
        
        return profile_db
    
    async def _convert_db_to_profile(self, profile_db: PersonalityProfileDB) -> PersonalityProfile:
        """Convert database model to Pydantic model."""
        # Convert traits
        traits = [
            PersonalityTrait(
                category=trait.category,
                trait=trait.trait,
                intensity=trait.intensity,
                examples=json.loads(trait.examples),
            )
            for trait in profile_db.traits
        ]
        
        # Convert communication style
        communication_style = CommunicationStyle(
            tone=profile_db.communication_style.tone,
            formality=FormalityLevel(profile_db.communication_style.formality),
            verbosity=VerbosityLevel(profile_db.communication_style.verbosity),
            technical_level=TechnicalLevel(profile_db.communication_style.technical_level),
        )
        
        # Convert mannerisms
        mannerisms = [mannerism.mannerism for mannerism in profile_db.mannerisms]
        
        # Convert research sources
        sources = [
            ResearchSource(
                type=source.source_type,
                url=source.url,
                confidence=source.confidence,
                last_updated=source.last_updated,
            )
            for source in profile_db.research_sources
        ]
        
        return PersonalityProfile(
            id=profile_db.id,
            name=profile_db.name,
            type=PersonalityType(profile_db.personality_type),
            traits=traits,
            communication_style=communication_style,
            mannerisms=mannerisms,
            sources=sources,
        )
    
    async def _create_history_entry(
        self,
        session: AsyncSession,
        config_id: str,
        change_type: str,
        description: str,
        data_snapshot: Dict[str, Any],
        created_by: Optional[str] = None,
    ) -> None:
        """Create a configuration history entry."""
        # Get next version number
        stmt = (
            select(func.max(ConfigurationHistory.version))
            .where(ConfigurationHistory.configuration_id == config_id)
        )
        result = await session.execute(stmt)
        max_version = result.scalar() or 0
        
        # Convert data_snapshot to JSON-serializable format
        def json_serializer(obj):
            """JSON serializer for objects not serializable by default json code"""
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
        
        history_entry = ConfigurationHistory(
            configuration_id=config_id,
            version=max_version + 1,
            change_type=change_type,
            change_description=description,
            data_snapshot=json.dumps(data_snapshot, default=json_serializer),
            created_by=created_by,
        )
        session.add(history_entry)