"""Implement the Observer and Watchdog pattern specific to AMI"""

import time
from pathlib import Path
from typing import Callable, Any
from watchdog.events import FileSystemEvent, FileSystemEventHandler

class ConfigMetadataPluginWatcher(FileSystemEventHandler):
    """Handler for config, metadata file changes, and plugin directory creation/deletion"""
    
    def __init__(
        self,
        config_file: Path,
        metadata_file: Path,
        plugins_dir: Path,
        callback: Callable[[Any], None]
    ):
        super().__init__()
        self.config_file = config_file          # e.g., ~/.config/ami/config.yaml
        self.metadata_file = metadata_file      # e.g., ~/.config/ami/metadata.json
        self.plugins_dir = plugins_dir          # e.g., ~/.local/share/ami/plugins/
        self.callback = callback                # Event Callback, return a string
        self.last_config_update = 0
        self.last_metadata_update = 0
        self.last_plugin_update = 0

        print(f"Filepath: {self.config_file} && {self.config_file.exists()}")
        print(f"Filepath: {self.metadata_file} && {self.metadata_file.exists()}")
        print(f"Filepath: {self.plugins_dir} && {self.plugins_dir.exists()}")
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events for config and metadata files"""
        if event.is_directory:
            return
        
        path = Path(event.src_path)
        now = time.time()
        print("---------------------")
        print(dir(event))
        print("---------------------")
        
        if path == self.config_file and now - self.last_config_update > 1:
            self.last_config_update = now
            print(f"Config file modified: {path}")
            # TODO: Reload config (e.g., config.reload())
            self.callback(str(path))
        
        elif path == self.metadata_file and now - self.last_metadata_update > 1:
            self.last_metadata_update = now
            print(f"Metadata file modified: {path}")
            # TODO: Reload plugin metadata (e.g., registry.reload_and_diff())
            self.callback(str(path))
    
    def on_created(self, event: FileSystemEvent):
        """Handle directory creation in plugins_dir (e.g., Git repo cloned)"""
        if not event.is_directory:
            return
        
        path = Path(event.src_path)
        now = time.time()

        if path.parent == self.plugins_dir and now - self.last_plugin_update > 1:
            self.last_plugin_update = now
            if (path / ".git").exists():  # Confirm it's a Git repo
                print(f"Git repo cloned: {path}")
                # TODO: Reload plugin metadata (e.g., registry.reload_and_diff())
                self.callback(str(path))
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle directory deletion in plugins_dir (e.g., Git repo removed)"""
        if not event.is_directory:
            return
        
        path = Path(event.src_path)
        now = time.time()

        if path.parent == self.plugins_dir and now - self.last_plugin_update > 1:
            self.last_plugin_update = now
            print(f"Plugin directory deleted: {path}")
            # TODO: Reload plugin metadata (e.g., registry.reload_and_diff())
            self.callback({"type": "metadata_changed", "path": str(path)})
