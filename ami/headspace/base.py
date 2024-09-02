""" Foundational to Headspace """

from pathlib import Path
from tkinter import Frame
from typing import Optional, Tuple
from sys import modules as sys_modules

import yaml
from pydantic import BaseModel, Field

from ami.base import Base
from ami.headspace.filesystem import Filesystem

class LocalConfig:
    """ Currently Not in Use """
    def __init__(self, config_filepath: Path | str):
        """ Initiate a local config object to hold the config for the given Headspace module
            To be fleshed out with the introduction of the config editing Headspace module
        """
        config_filepath = Path(config_filepath)

class Primitive(Base):
    """
    Primitive is the object all module specific Parent inherit from.
    Abstract Base Class for establishing the Filesystem necesarry for Headspace modules.
    """

    def __new__(cls, *args, **kwargs):
        """ This class is only inheritable, cannot be instantiated alone """
        if cls is Primitive:
            raise TypeError("Primitive class cannot be instantiated directly.")
        return super().__new__(cls, *args, **kwargs)

    def __init__(self):
        """
        Initialize the Primitive object.

        This method sets up the necessary configuration and filesystem for the Headspace module.
        It loads the module's config.yaml file and initializes the filesystem.

        Raises:
            ImportError: If the module has not been imported correctly.
            FileNotFoundError: If the module's config.yaml file is missing.
        """
        super().__init__()
        try:
            package = sys_modules[self.__module__].__package__
            config_file = Path(sys_modules[package].__path__[0]) / "config.yaml"
            self.logs.info(f"Primitive modules: {self.__module__}")
            self.logs.info(f"Primitive package: {package}")
            self.logs.info(f"Primitive config_file: {config_file}")
        except AttributeError as exc:
            self.logs.critical(f"Package not found. Fatality! '{self.__module__}'")
            raise ImportError(f'{self.__module__} has not been imported!') from exc

        if not config_file.is_file():
            error = f"Module '{self.__module__}' is missing its 'config.yaml' file. Fatality."
            self.logs.critical(error)
            raise FileNotFoundError(error)

        self._config_file = config_file
        with open(config_file, "r", encoding="utf-8") as f:
            self._yaml = yaml.safe_load(f)
#           self._local_config = LocalConfig(config_file)

        self._filesystem = Filesystem(package.split('.')[-1])
        self.logs.info(f"Primitive filesystem: {self.filesystem}")

    @property
    def yaml(self):
        """ yaml property """
        return self._yaml

    @property
    def lc(self):
        """ local config property, to replace yaml property as LocalConfig property """
        return self._yaml
#        return self._local_config

    @property
    def filesystem(self):
        """ Filesystem property """
        return self._filesystem

class Payload(BaseModel):
    """
    Represents a payload for communication between modules in the Headspace system.

    This model defines the structure of data that can be sent between different
    parts of the application, including information about the sending module,
    GUI reload flags, new frames to be loaded, and their placement.

    Attributes:
        module (str): The name of the module sending the payload.
        gui_reload (bool): Flag indicating whether the GUI should be reloaded.
        new_frame (Optional[Frame]): A new tkinter Frame object to be loaded to the GUI, if any.
        frame_placement (Optional[Tuple[int, int]]): The placement coordinates for the new frame.
    """
    module: str = Field(description="Module/Headspace is required")
    gui_reload: bool = Field(False, description="Reload flag for the modules")
    new_frame: Optional[Frame] = Field(None, description="tkinter.Frame object to be loaded to the GUI")
    frame_placement: Optional[Tuple[int, int]] = Field(None, description="Placement for the frame uf passed in this Payload. (x, y, anchor)")

    class Config:
        arbitrary_types_allowed=True

    @classmethod
    def reload(cls, module_name: str):
        """ Return a Payload only intended to reload the GUI associated with the Headspace """
        return cls(module=module_name, gui_reload=True)

class SharedTool(Base):
    _instance = None

    def __new__(cls, *args, **kwargs):
        """ This Singleton pattern class is only inheritable, cannot be instantiated alone """
        if cls is SharedTool:
            raise TypeError("Base class cannot be instantiated directly.")
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            return cls._instance
        else:
            return cls._instance
    def __init__(self, *args, **kwargs):
        super().__init__()
