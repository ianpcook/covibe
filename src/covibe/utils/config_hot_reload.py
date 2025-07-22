"""Hot-reloading configuration management for prompt templates and LLM providers."""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Set
from datetime import datetime

# Optional watchdog import for file watching
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None

from ..services.prompt_manager import PromptConfig, load_prompt_config, PromptConfigError
from ..services.llm_provider_config import ProvidersConfig, load_provider_config
from .config_validation import PromptTemplateValidator, LLMProviderValidator


logger = logging.getLogger(__name__)


class ConfigurationCache:
    """Cache for configuration objects with automatic invalidation."""
    
    def __init__(self):
        """Initialize the configuration cache."""
        self._prompt_cache: Dict[str, tuple[PromptConfig, float]] = {}
        self._provider_cache: Optional[tuple[LLMProviderConfig, float]] = None
        self._file_timestamps: Dict[str, float] = {}
    
    def get_prompt_config(self, file_path: Path) -> Optional[PromptConfig]:
        """Get cached prompt configuration if still valid.
        
        Args:
            file_path: Path to prompt configuration file
            
        Returns:
            Cached PromptConfig if valid, None if not cached or stale
        """
        file_str = str(file_path)
        
        if not file_path.exists():
            # File was deleted, remove from cache
            self._prompt_cache.pop(file_str, None)
            self._file_timestamps.pop(file_str, None)
            return None
        
        current_mtime = file_path.stat().st_mtime
        
        if file_str in self._prompt_cache:
            config, cached_mtime = self._prompt_cache[file_str]
            if cached_mtime >= current_mtime:
                return config
            else:
                # File was modified, remove stale cache entry
                del self._prompt_cache[file_str]
        
        return None
    
    def set_prompt_config(self, file_path: Path, config: PromptConfig):
        """Cache prompt configuration.
        
        Args:
            file_path: Path to prompt configuration file
            config: PromptConfig to cache
        """
        file_str = str(file_path)
        mtime = file_path.stat().st_mtime
        self._prompt_cache[file_str] = (config, mtime)
        self._file_timestamps[file_str] = mtime
    
    def get_provider_config(self, file_path: Path) -> Optional[ProvidersConfig]:
        """Get cached provider configuration if still valid.
        
        Args:
            file_path: Path to provider configuration file
            
        Returns:
            Cached LLMProviderConfig if valid, None if not cached or stale
        """
        if not file_path.exists():
            self._provider_cache = None
            return None
        
        current_mtime = file_path.stat().st_mtime
        
        if self._provider_cache:
            config, cached_mtime = self._provider_cache
            if cached_mtime >= current_mtime:
                return config
            else:
                self._provider_cache = None
        
        return None
    
    def set_provider_config(self, file_path: Path, config: ProvidersConfig):
        """Cache provider configuration.
        
        Args:
            file_path: Path to provider configuration file
            config: LLMProviderConfig to cache
        """
        mtime = file_path.stat().st_mtime
        self._provider_cache = (config, mtime)
    
    def invalidate_prompt(self, file_path: Path):
        """Invalidate cached prompt configuration.
        
        Args:
            file_path: Path to prompt configuration file
        """
        file_str = str(file_path)
        self._prompt_cache.pop(file_str, None)
        self._file_timestamps.pop(file_str, None)
    
    def invalidate_provider(self):
        """Invalidate cached provider configuration."""
        self._provider_cache = None
    
    def clear(self):
        """Clear all cached configurations."""
        self._prompt_cache.clear()
        self._provider_cache = None
        self._file_timestamps.clear()


class ConfigFileWatcher(FileSystemEventHandler if WATCHDOG_AVAILABLE else object):
    """File system event handler for configuration file changes."""
    
    def __init__(self, hot_reload_manager: 'HotReloadManager'):
        """Initialize the file watcher.
        
        Args:
            hot_reload_manager: Reference to the hot reload manager
        """
        self.hot_reload_manager = hot_reload_manager
        self.debounce_time = 0.5  # Debounce file events for 500ms
        self.last_event_times: Dict[str, float] = {}
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Debounce events (editors often trigger multiple events)
        current_time = time.time()
        last_time = self.last_event_times.get(str(file_path), 0)
        
        if current_time - last_time < self.debounce_time:
            return
        
        self.last_event_times[str(file_path)] = current_time
        
        # Schedule reload
        asyncio.create_task(self.hot_reload_manager._handle_file_change(file_path))
    
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        asyncio.create_task(self.hot_reload_manager._handle_file_change(file_path))


class HotReloadManager:
    """Manages hot-reloading of configuration files."""
    
    def __init__(self, config_root: Path):
        """Initialize the hot reload manager.
        
        Args:
            config_root: Root directory for configuration files
        """
        self.config_root = config_root
        self.prompts_dir = config_root / "prompts"
        self.llm_dir = config_root / "llm"
        
        # Configuration cache
        self.cache = ConfigurationCache()
        
        # Validators
        self.prompt_validator = PromptTemplateValidator()
        self.provider_validator = LLMProviderValidator()
        
        # File watcher (only if watchdog is available)
        self.observer = Observer() if WATCHDOG_AVAILABLE else None
        self.watcher = ConfigFileWatcher(self) if WATCHDOG_AVAILABLE else None
        
        # Callbacks for configuration changes
        self.prompt_change_callbacks: Set[Callable[[Path, PromptConfig], None]] = set()
        self.provider_change_callbacks: Set[Callable[[ProvidersConfig], None]] = set()
        self.error_callbacks: Set[Callable[[Path, Exception], None]] = set()
        
        # State
        self.is_watching = False
    
    def start_watching(self):
        """Start watching configuration files for changes."""
        if self.is_watching:
            return
        
        if not WATCHDOG_AVAILABLE:
            logger.warning("Watchdog not available, file watching disabled")
            return
        
        # Watch prompts directory
        if self.prompts_dir.exists():
            self.observer.schedule(self.watcher, str(self.prompts_dir), recursive=False)
        
        # Watch LLM directory
        if self.llm_dir.exists():
            self.observer.schedule(self.watcher, str(self.llm_dir), recursive=False)
        
        self.observer.start()
        self.is_watching = True
        logger.info(f"Started watching configuration files in {self.config_root}")
    
    def stop_watching(self):
        """Stop watching configuration files."""
        if not self.is_watching or not WATCHDOG_AVAILABLE:
            return
        
        self.observer.stop()
        self.observer.join()
        self.is_watching = False
        logger.info("Stopped watching configuration files")
    
    def add_prompt_change_callback(self, callback: Callable[[Path, PromptConfig], None]):
        """Add callback for prompt configuration changes.
        
        Args:
            callback: Function to call when prompt config changes
        """
        self.prompt_change_callbacks.add(callback)
    
    def add_provider_change_callback(self, callback: Callable[[ProvidersConfig], None]):
        """Add callback for provider configuration changes.
        
        Args:
            callback: Function to call when provider config changes
        """
        self.provider_change_callbacks.add(callback)
    
    def add_error_callback(self, callback: Callable[[Path, Exception], None]):
        """Add callback for configuration errors.
        
        Args:
            callback: Function to call when configuration error occurs
        """
        self.error_callbacks.add(callback)
    
    def remove_prompt_change_callback(self, callback: Callable[[Path, PromptConfig], None]):
        """Remove prompt change callback."""
        self.prompt_change_callbacks.discard(callback)
    
    def remove_provider_change_callback(self, callback: Callable[[ProvidersConfig], None]):
        """Remove provider change callback."""
        self.provider_change_callbacks.discard(callback)
    
    def remove_error_callback(self, callback: Callable[[Path, Exception], None]):
        """Remove error callback."""
        self.error_callbacks.discard(callback)
    
    async def get_prompt_config(self, file_path: Path) -> Optional[PromptConfig]:
        """Get prompt configuration with caching and validation.
        
        Args:
            file_path: Path to prompt configuration file
            
        Returns:
            PromptConfig if valid, None if not found or invalid
        """
        # Check cache first
        cached_config = self.cache.get_prompt_config(file_path)
        if cached_config:
            return cached_config
        
        # Load and validate configuration
        try:
            config = await load_prompt_config(file_path)
            
            # Validate configuration
            validation_result = self.prompt_validator.validate_prompt_file(file_path)
            if not validation_result.valid:
                error_msg = "; ".join([issue.message for issue in validation_result.errors])
                raise PromptConfigError(f"Validation failed: {error_msg}")
            
            # Cache valid configuration
            self.cache.set_prompt_config(file_path, config)
            return config
            
        except Exception as e:
            logger.error(f"Error loading prompt config {file_path}: {e}")
            self._notify_error_callbacks(file_path, e)
            return None
    
    async def get_provider_config(self, file_path: Path) -> Optional[ProvidersConfig]:
        """Get provider configuration with caching and validation.
        
        Args:
            file_path: Path to provider configuration file
            
        Returns:
            LLMProviderConfig if valid, None if not found or invalid
        """
        # Check cache first
        cached_config = self.cache.get_provider_config(file_path)
        if cached_config:
            return cached_config
        
        # Load and validate configuration
        try:
            config = await load_provider_config(file_path)
            
            # Validate configuration
            validation_result = self.provider_validator.validate_provider_config(file_path)
            if not validation_result.valid:
                error_msg = "; ".join([issue.message for issue in validation_result.errors])
                raise Exception(f"Validation failed: {error_msg}")
            
            # Cache valid configuration
            self.cache.set_provider_config(file_path, config)
            return config
            
        except Exception as e:
            logger.error(f"Error loading provider config {file_path}: {e}")
            self._notify_error_callbacks(file_path, e)
            return None
    
    async def _handle_file_change(self, file_path: Path):
        """Handle configuration file changes.
        
        Args:
            file_path: Path to changed file
        """
        logger.info(f"Configuration file changed: {file_path}")
        
        try:
            # Determine file type and handle appropriately
            if file_path.parent == self.prompts_dir and file_path.suffix in ['.yaml', '.yml']:
                await self._handle_prompt_change(file_path)
            elif file_path.parent == self.llm_dir and file_path.suffix in ['.yaml', '.yml']:
                await self._handle_provider_change(file_path)
            else:
                logger.debug(f"Ignoring non-configuration file: {file_path}")
        
        except Exception as e:
            logger.error(f"Error handling file change {file_path}: {e}")
            self._notify_error_callbacks(file_path, e)
    
    async def _handle_prompt_change(self, file_path: Path):
        """Handle prompt configuration file changes.
        
        Args:
            file_path: Path to changed prompt file
        """
        # Invalidate cache
        self.cache.invalidate_prompt(file_path)
        
        # Reload configuration
        config = await self.get_prompt_config(file_path)
        
        if config:
            logger.info(f"Reloaded prompt configuration: {config.name}")
            
            # Notify callbacks
            for callback in self.prompt_change_callbacks:
                try:
                    callback(file_path, config)
                except Exception as e:
                    logger.error(f"Error in prompt change callback: {e}")
        else:
            logger.warning(f"Failed to reload prompt configuration: {file_path}")
    
    async def _handle_provider_change(self, file_path: Path):
        """Handle provider configuration file changes.
        
        Args:
            file_path: Path to changed provider file
        """
        # Invalidate cache
        self.cache.invalidate_provider()
        
        # Reload configuration
        config = await self.get_provider_config(file_path)
        
        if config:
            logger.info("Reloaded provider configuration")
            
            # Notify callbacks
            for callback in self.provider_change_callbacks:
                try:
                    callback(config)
                except Exception as e:
                    logger.error(f"Error in provider change callback: {e}")
        else:
            logger.warning(f"Failed to reload provider configuration: {file_path}")
    
    def _notify_error_callbacks(self, file_path: Path, error: Exception):
        """Notify error callbacks of configuration errors.
        
        Args:
            file_path: Path to file with error
            error: Exception that occurred
        """
        for callback in self.error_callbacks:
            try:
                callback(file_path, error)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")
    
    def force_reload_all(self):
        """Force reload of all cached configurations."""
        logger.info("Force reloading all configurations")
        self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            "prompt_configs_cached": len(self.cache._prompt_cache),
            "provider_config_cached": self.cache._provider_cache is not None,
            "total_files_tracked": len(self.cache._file_timestamps),
            "is_watching": self.is_watching
        }


# Global hot reload manager instance
_hot_reload_manager: Optional[HotReloadManager] = None


def get_hot_reload_manager(config_root: Optional[Path] = None) -> HotReloadManager:
    """Get the global hot reload manager instance.
    
    Args:
        config_root: Configuration root directory (only used for first call)
        
    Returns:
        HotReloadManager instance
    """
    global _hot_reload_manager
    
    if _hot_reload_manager is None:
        if config_root is None:
            config_root = Path("config")
        _hot_reload_manager = HotReloadManager(config_root)
    
    return _hot_reload_manager


def start_hot_reload(config_root: Optional[Path] = None):
    """Start hot reloading for configuration files.
    
    Args:
        config_root: Configuration root directory
    """
    manager = get_hot_reload_manager(config_root)
    manager.start_watching()


def stop_hot_reload():
    """Stop hot reloading."""
    global _hot_reload_manager
    
    if _hot_reload_manager:
        _hot_reload_manager.stop_watching()


async def get_prompt_config_with_reload(file_path: Path) -> Optional[PromptConfig]:
    """Get prompt configuration with hot reload support.
    
    Args:
        file_path: Path to prompt configuration file
        
    Returns:
        PromptConfig if valid, None otherwise
    """
    manager = get_hot_reload_manager()
    return await manager.get_prompt_config(file_path)


async def get_provider_config_with_reload(file_path: Path) -> Optional[ProvidersConfig]:
    """Get provider configuration with hot reload support.
    
    Args:
        file_path: Path to provider configuration file
        
    Returns:
        LLMProviderConfig if valid, None otherwise
    """
    manager = get_hot_reload_manager()
    return await manager.get_provider_config(file_path)