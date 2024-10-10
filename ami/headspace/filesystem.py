""" filesystem.py """

from pathlib import Path
from typing import Optional
from shutil import copy2

import yaml

from ami.config import Config

class Filesystem:
    """
    The Filesystem class is used as a directory cursor for a Headspace module.
    Expected implementation is `filesystem = Filesystem(headspace_name)`
    """

    def __init__(self, filesystem_name: str, default_config: Optional[Path] = None):
        """
        Filesystem class represents a directory structure for managing headspaces.

        Args:
            filesystem_name (str): The name of the filesystem directory.
        """
        config = Config()
        self._filesystem: Path = config.headspaces_dir / filesystem_name

        self._yaml = None
        self.load_config(default_config)

    def __getitem__(self, headspace_name) -> Path:
        """
        Returns the path to a headspace directory within the filesystem.

        Args:
            headspace_name (str): The name of the headspace directory.

        Returns:
            Path: The path to the headspace directory.
        """
        return self._filesystem / headspace_name

    def __truediv__(self, directory: str) -> Path:
        """
        Returns the path to a directory within the filesystem.
        Creates the filesystem director if it doesn't already exist.

        Args:
            directory (str): The name of the directory.

        Returns:
            Path: The path to the directory.
        """
        if not self._filesystem.is_dir():
            self._filesystem.mkdir(parents=True, exist_ok=True)
        return self._filesystem / directory

    def __repr__(self) -> str:
        """ Returns the representation of the Filesystem instance """
        return f"<{self.__module__}({self.name}) path='{self._filesystem}'>"

    @property
    def path(self) -> Path:
        """ Get the path this filesystem holds near and dear """
        return self._filesystem

    @property
    def name(self) -> str:
        """ Returns the name of the filesystem directory. """
        return self._filesystem.name

    @property
    def yaml(self):
        """ Returns the yaml config file, hopefully as a dictionary """
        return self._yaml

    @property
    def contents(self) -> list:
        """ Returns a list of files and directories in the filesystem. """
        if not self._filesystem.is_dir():
            return []
        else:
            return [p.name for p in self._filesystem.iterdir()]

    @property
    def config_file(self):
        return self._filesystem / "config.yaml"

    def load_config(self, default_config: Optional[Path] = None):

        if not self.config_file.exists():
            if default_config and default_config.is_file():
                self.config_file.parent.mkdir(parents=True, exist_ok=True)
                copy2(default_config, self.config_file)
            else:
                raise FileNotFoundError(f"Cannot find local or default config file for {self._filesystem.name}")

        with open(self.config_file, "r", encoding="utf-8") as f:
            self._yaml = yaml.safe_load(f)
