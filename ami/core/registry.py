"""Registry system for managing add-ons and their components."""

import ast
from functools import cached_property
import json
from enum import Enum
from pathlib import Path
from types import ModuleType
<<<<<<< HEAD
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
=======
from typing import Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass
from importlib import import_module
>>>>>>> convostate

import git

from ami.core import LogBase, Config
from .headspace_importer import import_plugin

<<<<<<< HEAD
def extract_prompt(file_path: Path):
    # Read the file content
    with open(file_path, 'r') as file:
        source = file.read()

    tree = ast.parse(source)        # Parse the source code into an AST

    for node in ast.walk(tree):     # Traverse the AST to find the 'prompt' variable assignment
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'prompt':
                    if isinstance(node.value, ast.Constant):
                        return node.value.s
                    elif isinstance(node.value, ast.Constant):
                        return node.value.value
    return None

=======
>>>>>>> convostate
def validate_plugin_directory(plugin_dirpath: Path) -> bool:
    # TODO: Check if `plugin_dirpath` is a git repo OR a builtin
    if plugin_dirpath.is_dir():
        return True
    return False

<<<<<<< HEAD
=======
class PluginVertical(Enum):
    GUI = "GUI"
    HEADSPACE = "Headspace"
    BLUEPRINT = "Blueprint"

>>>>>>> convostate
class ComponentStatus(Enum):
    """Status of a component or add-on."""
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"

@dataclass
<<<<<<< HEAD
class Plugin:
=======
class Plugin(LogBase):
>>>>>>> convostate
    """Metadata for an entire add-on package."""
    name: str
    repo_url: str
    version: str
    location: Path
    status: ComponentStatus = ComponentStatus.DISABLED

    @cached_property
    def module(self) -> Optional[ModuleType]:
<<<<<<< HEAD
        return import_plugin(self.location)

    @cached_property
    def prompt(self) -> str:
        prompt = extract_prompt(self.location/"__init__.py")
        if prompt:
            return prompt
        else:
            return "This is the default Prompt!"

    def headspace(self):
        if 'get_headspace' in dir(self.module):
            return self.module.get_headspace()
        return None

    def blueprint(self):
        if 'get_blueprint' in dir(self.module):
            return self.module.get_blueprint()
        return None

    def gui(self):
        if 'get_gui' in dir(self.module):
            return self.module.get_gui()
        return None
=======
        """ Cached import for the plugin """
        self.logs.info(f"Plugin({self.name}).module @cached_property triggered. Plugin loading.")
        return import_plugin(self.location)

    @property
    def gui(self):
        """Returns the GUI object from the plugin, or None if not available."""
        return getattr(self.module, "GUI", None) if self.module else None

    @property
    def headspace(self):
        """Returns the Headspace object from the plugin, or None if not available."""
        return getattr(self.module, "Headspace", None) if self.module else None

    @property
    def blueprint(self):
        """Returns the Headspace object from the plugin, or None if not available."""
        return getattr(self.module, "Blueprint", None) if self.module else None

    def get_vertical(self, vertical: PluginVertical) -> None:
        """ Return a Class ready to be instanced or None """
        return getattr(self.module, vertical.value, None)

    @cached_property
    def examples(self):
        init_file = self.location / "__init__.py"

        if not init_file.exists():
            error_msg = f"Plugin {self.name} does not have an __init__.py"
            self.logs.error(error_msg)
            raise FileNotFoundError(error_msg)

        with open(init_file, 'r') as file:
            script_content = file.read()
        
        tree = ast.parse(script_content)
        
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'EXAMPLES':
                        value = node.value
                        if isinstance(value, ast.List):
                            return ast.literal_eval(value)
                        else:
                            raise ValueError(f"{self.name}.EXAMPLES needs to be of type list!")

        raise ValueError(f"Variable 'EXAMPLES' not found for the '{self.name}' plugin")
>>>>>>> convostate

    def enable(self):
        self.status = ComponentStatus.ACTIVE

    def disable(self):
        self.status = ComponentStatus.DISABLED

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "repo_url": self.repo_url,
            "version": self.version,
            "location": str(self.location),
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Plugin":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            repo_url=data["repo_url"],
            version=data["version"],
            location=Path(data["location"]),
            status=ComponentStatus(data["status"]),
        )

@dataclass
<<<<<<< HEAD
class PluginCache:
=======
class PluginCache(LogBase):
>>>>>>> convostate
    """Cache for plugins."""
    plugins: Dict[str, Plugin]


    def __getitem__(self, plugin_name: str) -> Optional[Plugin]:
        if plugin_name in self.plugins:
            return self.plugins[plugin_name]
        return

    @property
<<<<<<< HEAD
=======
    def names(self) -> List[str]:
        return list(self.plugins.keys())

    @property
    def examples(self) -> Dict[str, str]:
        return { plugin.name: plugin.examples for plugin in self.plugins.values() }

    @property
>>>>>>> convostate
    def view(self):
        print("PluginCache")
        for name, plugin in self.plugins.items():
            print(f"    <Plugin[name:{name}, repo_url:{plugin.repo_url} version:{plugin.version}, status:{plugin.status}]>")

<<<<<<< HEAD
=======
    def values(self):
        return self.plugins.values()

>>>>>>> convostate
    @classmethod
    def from_metadata(cls, metadata_filepath: Path) -> "PluginCache":
        """Create a PluginCache instance from a JSON metadata file."""
        try:
            with open(metadata_filepath, 'r') as f:
                data = json.load(f)
            return cls({name: Plugin.from_dict(addon_data) for name, addon_data in data.items()})
        except Exception as e:
            print(f"Error loading metadata from {metadata_filepath}: {e}")
            raise

    @classmethod
    def load_from_plugin_dir(cls, primary_plugin_dir: Path, secondary_plugin_dir: Optional[Path] = None) -> "PluginCache":
        """Load metadata from plugin directories."""

        def get_version_from_init(init_file_path: Path) -> Optional[str]:
            """Extract __version__ from __init__.py without importing."""
            try:
                with open(init_file_path, 'r') as file:
                    tree = ast.parse(file.read(), filename=str(init_file_path))
                    for node in tree.body:
                        if isinstance(node, ast.Assign):
                            for target in node.targets:
                                if isinstance(target, ast.Name) and target.id == '__version__':
                                    if isinstance(node.value, ast.Constant):
                                        return node.value.s
                                    elif isinstance(node.value, ast.Constant):
                                        return node.value.value
            except Exception as e:
                print(f"Error parsing {init_file_path}: {e}")
            return None

        def get_git_version_and_url(plugin_dir: Path) -> Tuple[Optional[str], Optional[str]]:
            """Get the latest git tag and remote URL for a plugin directory."""
            try:
                repo = git.Repo(str(plugin_dir))
                tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime)
                latest_tag = tags[-1].name if tags else None
                remote_url = repo.remotes.origin.url if repo.remotes.origin else None
                return latest_tag, remote_url
            except git.InvalidGitRepositoryError:
                return None, None
            except Exception as e:
                print(f"Error getting git info for {plugin_dir}: {e}")
                return None, None

        def load_builtin_plugins(directory: Path) -> List[Plugin]:
            if not directory.is_dir():
                return []
            plugins = []
            for plugin_dir in directory.iterdir():
                if plugin_dir.is_dir():
                    init_file = plugin_dir / '__init__.py'
                    if init_file.exists():
                        version = get_version_from_init(init_file)
                        if version:
                            plugins.append(Plugin(
                                name=plugin_dir.name,
                                repo_url="builtin",
                                version=version,
                                location=plugin_dir
                            ))
            return plugins

        def load_third_party_plugins(directory: Path) -> List[Plugin]:
            if not directory.is_dir():
                return []
            plugins = []
            for plugin_dir in directory.iterdir():
                if plugin_dir.is_dir():
                    version, repo_url = get_git_version_and_url(plugin_dir)
                    if version and repo_url:
                        plugins.append(Plugin(
                            name=plugin_dir.name,
                            repo_url=repo_url,
                            version=version,
                            location=plugin_dir
                        ))
            return plugins

        builtin_plugins = load_builtin_plugins(primary_plugin_dir)
        third_party_plugins = load_third_party_plugins(secondary_plugin_dir) if secondary_plugin_dir else []

        all_plugins = builtin_plugins + third_party_plugins
        return cls({plugin.name: plugin for plugin in all_plugins})

    def to_dict(self) -> Dict[str, dict]:
        return {name: plugin.to_dict() for name, plugin in self.plugins.items()}

    def save(self, metadata_filepath: Path):
        """Save the plugin metadata to the specified JSON file."""
        try:
            with open(metadata_filepath, 'w') as f:
                json.dump(self.to_dict(), f, indent=4)
        except Exception as e:
            print(f"Error saving metadata to {metadata_filepath}: {e}")

class PluginRegistry(LogBase):
    """
    Central registry for managing add-ons and their components.

    This class manages the metadata and loading of add-on components,
    integrating with the IPC system for cross-process communication.
    """

    def __init__(self, ipc_manager: "IPCManager"):
        super().__init__()
        self.ipc_manager = ipc_manager
<<<<<<< HEAD
        config = Config()

        # Load in the metadata file or create it if non-existent
        if config.plugin_metadata_filepath.exists():
            self.logs.info("PluginRegistry.__init__: Loading PluginRegistry from metadata file.")
            self.plugin_cache = PluginCache.from_metadata(config.plugin_metadata_filepath)
        else:
            self.logs.info("PluginRegistry.__init__: Loading PluginRegistry from directories.")
            self.plugin_cache = PluginCache.load_from_plugin_dir(config.builtin_plugins, config.plugins_dir)

        self._config = config
        self.update_from_config()

=======
        self.config = Config()

        # Load in the metadata file or create it if non-existent
        if self.config.plugin_metadata_filepath.exists():
            self.logs.info("PluginRegistry.__init__: Loading PluginRegistry from metadata file.")
            self._plugin_cache = PluginCache.from_metadata(self.config.plugin_metadata_filepath)
        else:
            self.logs.info("PluginRegistry.__init__: Loading PluginRegistry from directories.")
            self._plugin_cache = PluginCache.load_from_plugin_dir(self.config.builtin_plugins, self.config.plugins_dir)
        self.update_from_config()

    @property
    def plugin_cache(self) -> PluginCache:
        return self._plugin_cache
>>>>>>> convostate

    def __getitem__(self, plugin_name: str) -> Optional[Plugin]:
        return self.plugin_cache[plugin_name]

<<<<<<< HEAD
=======
    @property
    def names(self) -> List[str]:
        """ Return a list of Headspace names in the registry """
        return self.plugin_cache.names

    @property
    def routing_examples(self) -> List[str]:
        routes = { name: ", ".join(examples) for name, examples in self.plugin_cache.examples.items()  }
        return [ f"{name}: {examples}" for name, examples in routes.items() ]
#       return random.shuffle([ f"{name}: {examples}" for name, examples in routes.items() ])

    def get_plugins_by_vertical(self, vertical: PluginVertical):
        return [ plugin for plugin in self.plugin_cache.values() if plugin.get_vertical(vertical) ]

>>>>>>> convostate
    def to_dict(self) -> dict:
        """Initial metadata for plugins."""
        return self.plugin_cache.to_dict()

    def update_from_config(self):
        """Update plugin statuses based on current config."""
        changes_made = False
        for plugin in self.plugin_cache.plugins.values():
            old_status = plugin.status
<<<<<<< HEAD
            if plugin.name in self._config.enabled_plugins:
=======
            if plugin.name in self.config.enabled_plugins:
>>>>>>> convostate
                plugin.enable()
            else:
                plugin.disable()
            if old_status != plugin.status:
                changes_made = True

        if changes_made:
<<<<<<< HEAD
            self.plugin_cache.save(self._config.plugin_metadata_filepath)

    def get_plugins_by_type(Plugin
=======
            self.plugin_cache.save(self.config.plugin_metadata_filepath)

>>>>>>> convostate
