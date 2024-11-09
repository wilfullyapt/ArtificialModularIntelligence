""" Foundational to Headspace Modules """

from pathlib import Path
from sys import modules as sys_modules


from ami.logger import Logger
from ami.config import Config
from ami.base.filesystem import Filesystem

class Base:
    """
    Base class for all packages that provides logging functionality.
    All packages should inherit from this class to enable logging.
    """
    def __new__(cls, *args, **kwargs):
        """ This class is only inheritable, cannot be instantiated alone """
        if cls is Base:
            raise TypeError("Base class cannot be instantiated directly.")
        return super().__new__(cls)
    def __init__(self, *args, **kwargs):
        """
        Initializes the logger instance for the package.
        """
        self._logger: Logger = Config().load_blank_logging()
        self._logger(self.__module__)
    @property
    def logs(self) -> Logger:
        """
        Returns the logger instance for the package.
        """
        return self._logger

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

        except AttributeError as exc:
            self.logs.critical(f"Package not found. Fatality! '{self.__module__}'")
            raise ImportError(f'{self.__module__} has not been imported!') from exc

        if not config_file.is_file():
            error = f"Module '{self.__module__}' is missing its '{config_file}' file. Fatality."
            self.logs.critical(error)
            raise FileNotFoundError(error)

        self._filesystem = Filesystem(package.split('.')[-1], default_config=config_file)

        self.logs.debug(f"Primitive modules: {self.__module__}")
        self.logs.debug(f"Primitive package: {package}")
        self.logs.debug(f"Primitive filesystem: {self.filesystem}")
        self.logs.debug(f"Primitive config_file: {self.filesystem.config_file}")

    @property
    def filesystem(self):
        """ Filesystem property """
        return self._filesystem

    @property
    def yaml(self):
        """ yaml property """
        return self.filesystem.yaml
