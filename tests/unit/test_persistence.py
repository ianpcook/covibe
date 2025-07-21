"""Tests for configuration persistence service."""

import json
import pytest
from datetime import datetime
from uuid import uuid4

from src.covibe.models.core import (
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
from src.covibe.models.database import DatabaseConfig
from src.covibe.services.persistence import ConfigurationPersistenceService


@pytest.fixture
async def db_config():
    """Create test database configuration."""
    config = DatabaseConfig("sqlite+aiosqlite:///:memory:")
    await config.create_tables()
    yield config
    await config.close()


@pytest.fixture
async def persistence_service(db_config):
    """Create persistence service with test database."""
    return ConfigurationPersistenceService(db_config)


@pytest.fixture
def sample_personality_config():
    """Create sample personality configuration for testing."""
    return PersonalityConfig(
        id=str(uuid4()),
        profile=PersonalityProfile(
            id=str(uuid4()),
            name="Sherlock Holmes",
            type=PersonalityType.FICTIONAL,
            traits=[
                PersonalityTrait(
                    category="analytical",
                    trait="deductive reasoning",
                    intensity=10,
                    examples=["Elementary, my dear Watson", "The game is afoot"],
                ),
                PersonalityTrait(
                    category="social",
                    trait="aloof",
                    intensity=7,
                    examples=["Prefers solitude", "Dismissive of small talk"],
                ),
            ],
            communication_style=CommunicationStyle(
                tone="analytical",
                formality=FormalityLevel.FORMAL,
                verbosity=VerbosityLevel.VERBOSE,
                technical_level=TechnicalLevel.EXPERT,
            ),
            mannerisms=[
                "Uses precise language",
                "Makes logical deductions",
                "Often condescending",
            ],
            sources=[
                ResearchSource(
                    type="literary",
                    url="https://example.com/sherlock",
                    confidence=0.95,
                    last_updated=datetime.utcnow(),
                ),
            ],
        ),
        context="You are Sherlock Holmes, the brilliant detective...",
        ide_type="cursor",
        file_path="/cursor/rules/sherlock.mdc",
        active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


class TestConfigurationPersistenceService:
    """Test configuration persistence service."""
    
    async def test_create_configuration(self, persistence_service, sample_personality_config):
        """Test creating a new configuration."""
        config_id = await persistence_service.create_configuration(
            sample_personality_config,
            user_id="test_user",
            created_by="test_system",
        )
        
        assert config_id == sample_personality_config.id
        
        # Verify configuration was created
        retrieved_config = await persistence_service.get_configuration(config_id)
        assert retrieved_config is not None
        assert retrieved_config.id == sample_personality_config.id
        assert retrieved_config.profile.name == sample_personality_config.profile.name
        assert len(retrieved_config.profile.traits) == 2
        assert len(retrieved_config.profile.mannerisms) == 3
        assert len(retrieved_config.profile.sources) == 1
    
    async def test_get_configuration_not_found(self, persistence_service):
        """Test getting non-existent configuration."""
        config = await persistence_service.get_configuration("nonexistent")
        assert config is None
    
    async def test_update_configuration(self, persistence_service, sample_personality_config):
        """Test updating an existing configuration."""
        # Create initial configuration
        config_id = await persistence_service.create_configuration(
            sample_personality_config,
            user_id="test_user",
        )
        
        # Update configuration
        updated_config = sample_personality_config.model_copy(deep=True)
        updated_config.profile.name = "Updated Sherlock"
        updated_config.active = False
        
        success = await persistence_service.update_configuration(
            config_id,
            updated_config,
            updated_by="test_updater",
        )
        
        assert success is True
        
        # Verify update
        retrieved_config = await persistence_service.get_configuration(config_id)
        assert retrieved_config.profile.name == "Updated Sherlock"
        assert retrieved_config.active is False
    
    async def test_update_nonexistent_configuration(self, persistence_service, sample_personality_config):
        """Test updating non-existent configuration."""
        success = await persistence_service.update_configuration(
            "nonexistent",
            sample_personality_config,
        )
        assert success is False
    
    async def test_delete_configuration(self, persistence_service, sample_personality_config):
        """Test deleting a configuration."""
        # Create configuration
        config_id = await persistence_service.create_configuration(
            sample_personality_config,
            user_id="test_user",
        )
        
        # Delete configuration
        success = await persistence_service.delete_configuration(
            config_id,
            deleted_by="test_deleter",
        )
        
        assert success is True
        
        # Verify deletion
        retrieved_config = await persistence_service.get_configuration(config_id)
        assert retrieved_config is None
    
    async def test_delete_nonexistent_configuration(self, persistence_service):
        """Test deleting non-existent configuration."""
        success = await persistence_service.delete_configuration("nonexistent")
        assert success is False
    
    async def test_list_configurations(self, persistence_service, sample_personality_config):
        """Test listing configurations."""
        # Create multiple configurations
        config1 = sample_personality_config.model_copy(deep=True)
        config1.id = str(uuid4())
        config1.profile.id = str(uuid4())
        config1.profile.name = "Config 1"
        
        config2 = sample_personality_config.model_copy(deep=True)
        config2.id = str(uuid4())
        config2.profile.id = str(uuid4())
        config2.profile.name = "Config 2"
        config2.active = False
        
        await persistence_service.create_configuration(config1, user_id="user1")
        await persistence_service.create_configuration(config2, user_id="user2")
        
        # Test listing all active configurations
        active_configs = await persistence_service.list_configurations(active_only=True)
        assert len(active_configs) == 1
        assert active_configs[0].profile.name == "Config 1"
        
        # Test listing all configurations
        all_configs = await persistence_service.list_configurations(active_only=False)
        assert len(all_configs) == 2
        
        # Test filtering by user
        user1_configs = await persistence_service.list_configurations(user_id="user1")
        assert len(user1_configs) == 1
        assert user1_configs[0].profile.name == "Config 1"
    
    async def test_configuration_history(self, persistence_service, sample_personality_config):
        """Test configuration history tracking."""
        # Create configuration
        config_id = await persistence_service.create_configuration(
            sample_personality_config,
            user_id="test_user",
            created_by="test_creator",
        )
        
        # Update configuration
        updated_config = sample_personality_config.model_copy(deep=True)
        updated_config.profile.name = "Updated Name"
        await persistence_service.update_configuration(
            config_id,
            updated_config,
            updated_by="test_updater",
        )
        
        # Get history
        history = await persistence_service.get_configuration_history(config_id)
        
        assert len(history) == 2
        assert history[0]["change_type"] == "UPDATE"
        assert history[1]["change_type"] == "CREATE"
        assert history[0]["created_by"] == "test_updater"
        assert history[1]["created_by"] == "test_creator"
    
    async def test_restore_configuration_version(self, persistence_service, sample_personality_config):
        """Test restoring configuration to previous version."""
        # Create configuration
        config_id = await persistence_service.create_configuration(
            sample_personality_config,
            user_id="test_user",
        )
        
        # Update configuration
        updated_config = sample_personality_config.model_copy()
        updated_config.profile.name = "Updated Name"
        await persistence_service.update_configuration(config_id, updated_config)
        
        # Restore to version 1 (original)
        success = await persistence_service.restore_configuration_version(
            config_id,
            version=1,
            restored_by="test_restorer",
        )
        
        assert success is True
        
        # Verify restoration
        restored_config = await persistence_service.get_configuration(config_id)
        assert restored_config.profile.name == sample_personality_config.profile.name
    
    async def test_create_backup(self, persistence_service, sample_personality_config):
        """Test creating configuration backup."""
        # Create configurations
        config1 = sample_personality_config.model_copy(deep=True)
        config1.id = str(uuid4())
        config1.profile.id = str(uuid4())
        
        config2 = sample_personality_config.model_copy(deep=True)
        config2.id = str(uuid4())
        config2.profile.id = str(uuid4())
        
        await persistence_service.create_configuration(config1, user_id="test_user")
        await persistence_service.create_configuration(config2, user_id="test_user")
        
        # Create backup
        checksum = await persistence_service.create_backup(
            backup_name="test_backup",
            user_id="test_user",
        )
        
        assert checksum is not None
        assert len(checksum) == 64  # SHA-256 hash length
        
        # List backups
        backups = await persistence_service.list_backups(user_id="test_user")
        assert len(backups) == 1
        assert backups[0]["backup_name"] == "test_backup"
        assert backups[0]["checksum"] == checksum
    
    async def test_restore_backup(self, persistence_service, sample_personality_config):
        """Test restoring from backup."""
        # Create configuration and backup
        await persistence_service.create_configuration(
            sample_personality_config,
            user_id="test_user",
        )
        
        checksum = await persistence_service.create_backup(
            backup_name="test_backup",
            user_id="test_user",
        )
        
        # Delete original configuration
        await persistence_service.delete_configuration(sample_personality_config.id)
        
        # Get backup ID
        backups = await persistence_service.list_backups(user_id="test_user")
        backup_id = backups[0]["id"]
        
        # Restore backup
        success, errors = await persistence_service.restore_backup(
            backup_id,
            restored_by="test_restorer",
        )
        
        assert success is True
        assert len(errors) == 0
        
        # Verify restoration
        configs = await persistence_service.list_configurations(
            user_id="test_user",
            active_only=False,
        )
        assert len(configs) == 1
        assert configs[0].profile.name == sample_personality_config.profile.name
    
    async def test_list_configurations_pagination(self, persistence_service, sample_personality_config):
        """Test configuration listing with pagination."""
        # Create multiple configurations
        for i in range(5):
            config = sample_personality_config.model_copy(deep=True)
            config.id = str(uuid4())
            config.profile.id = str(uuid4())
            config.profile.name = f"Config {i}"
            await persistence_service.create_configuration(config, user_id="test_user")
        
        # Test pagination
        page1 = await persistence_service.list_configurations(
            user_id="test_user",
            limit=3,
            offset=0,
        )
        assert len(page1) == 3
        
        page2 = await persistence_service.list_configurations(
            user_id="test_user",
            limit=3,
            offset=3,
        )
        assert len(page2) == 2
        
        # Verify no overlap
        page1_ids = {config.id for config in page1}
        page2_ids = {config.id for config in page2}
        assert len(page1_ids.intersection(page2_ids)) == 0