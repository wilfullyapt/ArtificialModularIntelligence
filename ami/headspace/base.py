""" Foundational to Headspace """

import os
import sys
from functools import cached_property
from pathlib import Path

from ami.core import LogBase, Config

class Primitive(LogBase):
    """
    Primitive is the parent class for all plugin components. Blueprint, GUI, and Headspace
    Primitive provides the following attributes so the Headspace component knows about itself
        - Headspace Name: self.name is a proxy for self._hs_name
        - self.filespace is the directory path for the Headspace to use as filestorage
    One of the features is no __init__ method, thus not requiring super() from childen classes
    """

    def __new__(cls, *args, **kwargs):
        """ This class is only inheritable, cannot be instantiated alone """
        if cls is Primitive:
            raise TypeError("Primitive class cannot be instantiated directly.")
        return super().__new__(cls, *args, **kwargs)

    def __init_subclass__(cls, **kwargs):
        """ Called when a subclass is defined. Sets the plugin_directory attribute on the subclass. """
        super().__init_subclass__(**kwargs)
        file_path = sys.modules[cls.__module__].__file__
#       cls._hs_name = os.path.dirname(file_path)
        cls._hs_name = os.path.basename(os.path.dirname(file_path))

#       self.logs.debug(f"Primitive loaded for {cls.__module__} for Headspace {self._hs_name}")

    @cached_property
    def filespace(self) -> Path:
        filespace = Config().plugin_data_dir / self.__class__._hs_name
        filespace.mkdir(parents=True, exist_ok=True)
        return filespace
