"""Base classes for all plugin types in the AMI system."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class PluginType(Enum):
    """Types of plugins that can be registered."""
    HEADSPACE = "headspace"
    GUI = "gui"
    BLUEPRINT = "blueprint"

class PluginSource(Enum):
    """Source of the plugin - built-in or addon."""
    CORE = "core"
    ADDON = "addon"

@dataclass
class PluginInfo:
    """Metadata for a plugin."""
    name: str
    version: str
    type: PluginType
    source: PluginSource
    path: Path
    dependencies: Dict[str, str] = None  # name: version
    config: Dict[str, Any] = None

class PluginBase(ABC):
    """Base class for all plugins in the AMI system."""

    def __init__(self, plugin_info: PluginInfo):
        self.info = plugin_info
        self._initialized = False
        self._error = None

    @property
    def name(self) -> str:
        """Get plugin name."""
        return self.info.name

    @property
    def type(self) -> PluginType:
        """Get plugin type."""
        return self.info.type

    @property
    def is_initialized(self) -> bool:
        """Check if plugin is initialized."""
        return self._initialized

    @property
    def error(self) -> Optional[str]:
        """Get last error message if any."""
        return self._error

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the plugin. Should be called before using the plugin."""
        pass

    @abstractmethod
    async def cleanup(self) -> bool:
        """Clean up resources. Should be called when plugin is being unloaded."""
        pass

    def validate_dependencies(self) -> bool:
        """Validate that all required dependencies are available."""
        # This could be implemented to check versions of required plugins/packages
        return True

class HeadspacePlugin(PluginBase):
    """Base class for headspace plugins."""
    
    def __init__(self, plugin_info: PluginInfo):
        super().__init__(plugin_info)
        self.prompts = None
        
    @abstractmethod
    async def query(self, prompt: str, **kwargs) -> Any:
        """Process a query in this headspace."""
        pass

class GUIPlugin(PluginBase):
    """Base class for GUI plugins."""
    
    @abstractmethod
    async def create_widget(self, parent: Any) -> Any:
        """Create and return the main widget for this GUI plugin."""
        pass

class BlueprintPlugin(PluginBase):
    """Base class for blueprint plugins."""
    
    @abstractmethod
    def get_routes(self) -> list:
        """Get the Flask routes defined by this blueprint."""
        pass