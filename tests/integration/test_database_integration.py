"""Integration tests for database functionality."""

import os
import tempfile
import pytest
from pathlib import Path
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
from src.covibe.utils.database import initialize_database, reset_database


@pytest.fixture
async def temp_db_file():
    """Create temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        db_path = tmp_file.name
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
async def db_config_with_file(temp_db_file):
    """Create database configuration with temporary file."""
    database_url = f"sqlite+aiosqlite:///{temp_db_file}"
    config = await initialize_database(database_url)
    yield config
    await config.close()


@pytest.fixture
async def persistence_service_with_file(db_config_with_file):
    """Create persistence service with file-based database."""
    return ConfigurationPersistenceService(db_config_with_file)


@pytest.fixture
def complex_personality_config():
    """Create complex personality configuration for integration testing."""
    return PersonalityConfig(
        id=str(uuid4()),
        profile=PersonalityProfile(
            id=str(uuid4()),
            name="Tony Stark",
            type=PersonalityType.FICTIONAL,
            traits=[
                PersonalityTrait(
                    category="intelligence",
                    trait="genius-level intellect",
                    intensity=10,
                    examples=[
                        "Builds advanced technology",
                        "Solves complex problems quickly",
                        "Understands multiple scientific disciplines",
                    ],
                ),
                PersonalityTrait(
                    category="personality",
                    trait="sarcastic",
                    intensity=8,
                    examples=[
                        "Makes witty remarks",
                        "Uses humor to deflect",
                        "Often condescending",
                    ],
                ),
                PersonalityTrait(
                    category="social",
                    trait="charismatic",
                    intensity=9,
                    examples=[
                        "Natural leader",
                        "Confident public speaker",
                        "Attracts followers",
                    ],
                ),
            ],
            communication_style=CommunicationStyle(
                tone="confident",
                formality=FormalityLevel.CASUAL,
                verbosity=VerbosityLevel.MODERATE,
                technical_level=TechnicalLevel.EXPERT,
            ),
            mannerisms=[
                "Uses technical jargon casually",
                "Makes pop culture references",
                "Gestures while speaking",
                "Often interrupts others",
                "Shows off knowledge",
            ],
            sources=[
                ResearchSource(
                    type="marvel_comics",
                    url="https://marvel.com/characters/iron-man-tony-stark",
                    confidence=0.95,
                    last_updated=datetime.utcnow(),
                ),
                ResearchSource(
                    type="mcu_movies",
                    url="https://marvelcinematicuniverse.fandom.com/wiki/Tony_Stark",
                    confidence=0.90,
                    last_updated=datetime.utcnow(),
                ),
                ResearchSource(
                    type="character_analysis",
                    confidence=0.85,
                    last_updated=datetime.utcnow(),
                ),
            ],
        ),
        context="You are Tony Stark, the brilliant inventor and Iron Man...",
        ide_type="cursor",
        file_path="/cursor/rules/tony_stark.mdc",
        active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


class TestDatabaseIntegration:
    """Integration tests for database functionality."""
    
    async def test_database_initialization(self, temp_db_file):
        """Test database initialization creates proper schema."""
        database_url = f"sqlite+aiosqlite:///{temp_db_file}"
        db_config = await initialize_database(database_url)
        
        # Verify database file was created
        assert os.path.exists(temp_db_file)
        
        # Verify we can create a session
        async with db_config.async_session() as session:
            assert session is not None
        
        await db_config.close()
    
    async def test_database_reset(self, temp_db_file):
        """Test database reset functionality."""
        database_url = f"sqlite+aiosqlite:///{temp_db_file}"
        
        # Initialize database
        db_config = await initialize_database(database_url)
        await db_config.close()
        
        # Reset database
        db_config = await reset_database(database_url)
        
        # Verify we can still use the database
        async with db_config.async_session() as session:
            assert session is not None
        
        await db_config.close()
    
    async def test_full_crud_workflow(self, persistence_service_with_file, complex_personality_config):
        """Test complete CRUD workflow with file-based database."""
        # Create
        config_id = await persistence_service_with_file.create_configuration(
            complex_personality_config,
            user_id="integration_test_user",
            created_by="integration_test",
        )
        assert config_id == complex_personality_config.id
        
        # Read
        retrieved_config = await persistence_service_with_file.get_configuration(config_id)
        assert retrieved_config is not None
        assert retrieved_config.profile.name == "Tony Stark"
        assert len(retrieved_config.profile.traits) == 3
        assert len(retrieved_config.profile.mannerisms) == 5
        assert len(retrieved_config.profile.sources) == 3
        
        # Update
        updated_config = complex_personality_config.model_copy()
        updated_config.profile.name = "Anthony Stark"
        updated_config.active = False
        
        success = await persistence_service_with_file.update_configuration(
            config_id,
            updated_config,
            updated_by="integration_test_updater",
        )
        assert success is True
        
        # Verify update
        updated_retrieved = await persistence_service_with_file.get_configuration(config_id)
        assert updated_retrieved.profile.name == "Anthony Stark"
        assert updated_retrieved.active is False
        
        # Delete
        success = await persistence_service_with_file.delete_configuration(
            config_id,
            deleted_by="integration_test_deleter",
        )
        assert success is True
        
        # Verify deletion
        deleted_config = await persistence_service_with_file.get_configuration(config_id)
        assert deleted_config is None
    
    async def test_concurrent_operations(self, persistence_service_with_file, complex_personality_config):
        """Test concurrent database operations."""
        import asyncio
        
        # Create multiple configurations concurrently
        async def create_config(name_suffix: str):
            config = complex_personality_config.model_copy()
            config.id = str(uuid4())
            config.profile.id = str(uuid4())
            config.profile.name = f"Tony Stark {name_suffix}"
            
            return await persistence_service_with_file.create_configuration(
                config,
                user_id=f"user_{name_suffix}",
                created_by="concurrent_test",
            )
        
        # Create 5 configurations concurrently
        tasks = [create_config(str(i)) for i in range(5)]
        config_ids = await asyncio.gather(*tasks)
        
        assert len(config_ids) == 5
        assert len(set(config_ids)) == 5  # All unique
        
        # Verify all configurations were created
        all_configs = await persistence_service_with_file.list_configurations(
            active_only=False,
            limit=10,
        )
        assert len(all_configs) == 5
    
    async def test_large_data_handling(self, persistence_service_with_file):
        """Test handling of large personality configurations."""
        # Create configuration with large amounts of data
        large_config = PersonalityConfig(
            id=str(uuid4()),
            profile=PersonalityProfile(
                id=str(uuid4()),
                name="Complex Character",
                type=PersonalityType.CUSTOM,
                traits=[
                    PersonalityTrait(
                        category=f"category_{i}",
                        trait=f"trait_{i}",
                        intensity=(i % 10) + 1,
                        examples=[f"example_{i}_{j}" for j in range(10)],
                    )
                    for i in range(50)  # 50 traits
                ],
                communication_style=CommunicationStyle(
                    tone="complex",
                    formality=FormalityLevel.MIXED,
                    verbosity=VerbosityLevel.VERBOSE,
                    technical_level=TechnicalLevel.EXPERT,
                ),
                mannerisms=[f"mannerism_{i}" for i in range(100)],  # 100 mannerisms
                sources=[
                    ResearchSource(
                        type=f"source_type_{i}",
                        url=f"https://example.com/source_{i}",
                        confidence=0.5 + (i % 50) / 100,
                        last_updated=datetime.utcnow(),
                    )
                    for i in range(20)  # 20 sources
                ],
            ),
            context="A" * 10000,  # Large context string
            ide_type="cursor",
            file_path="/cursor/rules/complex.mdc",
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        # Create configuration
        config_id = await persistence_service_with_file.create_configuration(
            large_config,
            user_id="large_data_test",
        )
        
        # Retrieve and verify
        retrieved_config = await persistence_service_with_file.get_configuration(config_id)
        assert retrieved_config is not None
        assert len(retrieved_config.profile.traits) == 50
        assert len(retrieved_config.profile.mannerisms) == 100
        assert len(retrieved_config.profile.sources) == 20
        assert len(retrieved_config.context) == 10000
    
    async def test_backup_restore_integration(self, persistence_service_with_file, complex_personality_config):
        """Test backup and restore functionality with file database."""
        # Create multiple configurations
        configs = []
        for i in range(3):
            config = complex_personality_config.model_copy()
            config.id = str(uuid4())
            config.profile.id = str(uuid4())
            config.profile.name = f"Character {i}"
            configs.append(config)
            
            await persistence_service_with_file.create_configuration(
                config,
                user_id="backup_test_user",
            )
        
        # Create backup
        checksum = await persistence_service_with_file.create_backup(
            backup_name="integration_test_backup",
            user_id="backup_test_user",
        )
        assert checksum is not None
        
        # Delete all configurations
        for config in configs:
            await persistence_service_with_file.delete_configuration(config.id)
        
        # Verify deletion
        remaining_configs = await persistence_service_with_file.list_configurations(
            user_id="backup_test_user",
            active_only=False,
        )
        assert len(remaining_configs) == 0
        
        # Get backup and restore
        backups = await persistence_service_with_file.list_backups(
            user_id="backup_test_user"
        )
        assert len(backups) == 1
        
        success, errors = await persistence_service_with_file.restore_backup(
            backups[0]["id"],
            restored_by="integration_test",
        )
        assert success is True
        assert len(errors) == 0
        
        # Verify restoration
        restored_configs = await persistence_service_with_file.list_configurations(
            user_id="backup_test_user",
            active_only=False,
        )
        assert len(restored_configs) == 3
        
        # Verify data integrity
        restored_names = {config.profile.name for config in restored_configs}
        expected_names = {"Character 0", "Character 1", "Character 2"}
        assert restored_names == expected_names
    
    async def test_history_tracking_integration(self, persistence_service_with_file, complex_personality_config):
        """Test configuration history tracking with file database."""
        # Create configuration
        config_id = await persistence_service_with_file.create_configuration(
            complex_personality_config,
            user_id="history_test_user",
            created_by="history_test_creator",
        )
        
        # Make multiple updates
        for i in range(5):
            updated_config = complex_personality_config.model_copy()
            updated_config.profile.name = f"Updated Name {i}"
            
            await persistence_service_with_file.update_configuration(
                config_id,
                updated_config,
                updated_by=f"updater_{i}",
            )
        
        # Get history
        history = await persistence_service_with_file.get_configuration_history(config_id)
        
        # Verify history entries
        assert len(history) == 6  # 1 create + 5 updates
        assert history[0]["change_type"] == "UPDATE"  # Most recent first
        assert history[-1]["change_type"] == "CREATE"  # Oldest last
        
        # Verify version numbers
        versions = [entry["version"] for entry in history]
        assert versions == [6, 5, 4, 3, 2, 1]  # Descending order
        
        # Test version restoration
        success = await persistence_service_with_file.restore_configuration_version(
            config_id,
            version=1,  # Restore to original
            restored_by="history_test_restorer",
        )
        assert success is True
        
        # Verify restoration
        restored_config = await persistence_service_with_file.get_configuration(config_id)
        assert restored_config.profile.name == complex_personality_config.profile.name
        
        # Verify new history entry was created
        updated_history = await persistence_service_with_file.get_configuration_history(config_id)
        assert len(updated_history) == 7  # Original 6 + 1 restore