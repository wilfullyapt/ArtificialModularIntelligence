""" Logging for AMI """

import logging
from pathlib import Path
from typing import Optional, Literal
from pydantic import BaseModel, field_validator

class LoggerConfig(BaseModel):
    """ Logging Configuration as a Pydantic dataclass """
    stdout: bool = False
    save_dir: Optional[Path|str] = None
    log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = 'INFO'
    log_to_console_format: str = "\033[96m[{name}:%(levelname)s]\033[0m %(message)s"
    log_to_file_format: str = '[%(asctime)s] %(levelname)s ::> %(message)s'

    @field_validator('save_dir')
    def validate_save_dir(cls, value):
        """ Validation for the `save_dir` """
        if value:
            value = Path(value)
            if not value.exists():
                value.mkdir(parents=True)
        return value

    def __repr__(self):
        """ __repr__ """
        return f"LoggerConfig(stdout={self.stdout}, save_dir={self.save_dir}, log_level={self.log_level})"

    def __str__(self):
        """ __str__ """
        return str(self.__repr__())

class Logger:
    """ Logger; specific for AMI """

    def __init__(self, config: LoggerConfig):
        """ Create a new instance with config arguement """
        self._config = config
        self._logger: logging.Logger|None = None
        self.name: str|None = None

    def __call__(self, name: Optional[str] = None):
        """
            Logger.call is designed to update the handlers attached to self._logger
            Expected usage by a module is LoggerObj(__file__) or LoggerObj(custom.name)
            see self.assign_logger and self.clear_root_log_handlers

            Note: logger.getLogger({name}) returns a new logger with {name}
        """
        if bool(name) and self._logger is None:
            self.assign_logger(logging.getLogger(name))

        self.clear_root_log_handlers()

        return self

    def __repr__(self):
        """ __repr__ """
        return f"Logger(name={self.name}, config={self._config}, logger={self._logger})"

    @property
    def config(self) -> LoggerConfig:
        """ config member """
        return self._config
    @property
    def logger(self) -> logging.Logger|None:
        """ logger member """
        return self._logger
    @property
    def verbose(self) -> bool:
        """ verbose member """
        return self.config.stdout

    def assign_logger(self, logging_logger: logging.Logger) -> None:
        """ Core Logger(logging and self) setup function """
        self.name = Path(logging_logger.name).name

        self._logger = logging_logger
        self._logger.setLevel(getattr(logging, self._config.log_level))

        # Enable streaming to stdout if flagged
        if self._config.stdout:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, self._config.log_level))
            console_format = self._config.log_to_console_format.format(name=self.name)
            console_handler.setFormatter(logging.Formatter(console_format))
            self._logger.addHandler(console_handler)

        log_filer = lambda name : (name[0] if name[-1] == "py" else '.'.join(name)) + ".log"
        # Configure the save file destination if save_dir is set and exists as a directory
        if self._config.save_dir:
            save_path = Path(self._config.save_dir)
            if save_path.exists() and save_path.is_dir():
                log_file = log_filer(self.name.split('.'))
#                 log_file = self.name.split(".")[0] + ".log"
                file_handler = logging.FileHandler(save_path / log_file)
                file_handler.setLevel(getattr(logging, self._config.log_level))
                file_handler.setFormatter(logging.Formatter(self._config.log_to_file_format))
                self._logger.addHandler(file_handler)

    def clear_root_log_handlers(self):
        """ Get the root Logger and clear all handlers, custom logging only """
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)

    def debug(self, message) -> None:
        """ Debug log access """
        self._log(logging.DEBUG, message)

    def info(self, message) -> None:
        """ Info log Access """
        self._log(logging.INFO, message)

    def warn(self, message) -> None:
        """ warn log access """
        self._log(logging.WARNING, message)

    def error(self, message) -> None:
        """ Error log access """
        self._log(logging.ERROR, message)

    def critical(self, message) -> None:
        """ Critical log access """
        self._log(logging.CRITICAL, message)

    def _log(self, level, message):
        """ Inner log access """
        self._logger.log(level, message)
