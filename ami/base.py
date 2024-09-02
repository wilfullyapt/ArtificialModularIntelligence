""" Base module. Abstract Class that provides logging for all child classes """
from ami.logger import Logger
from ami.config import Config

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
    def __init__(self):
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
