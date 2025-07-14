""" Enhanced logging module for AMI with script-specific log files using loguru """

from pathlib import Path
from typing import Optional, Literal, Dict, Any

from pydantic import BaseModel, field_validator
from rich.console import Console
from rich.theme import Theme
from loguru import logger

from ..core.config import Config

class LoggerConfig(BaseModel):
    """Enhanced Logging Configuration as a Pydantic dataclass"""
    stdout: bool = True
    save_dir: Optional[Path | str] = None
    log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = 'INFO'
    rotation: str = "1 day"     # Rotation period for log files
    retention: str = "30 days"  # How long to keep log files
    compression: str = "gz"     # Compression format for rotated logs

    @field_validator('save_dir')
    def validate_save_dir(cls, value):
        """Validation for the `save_dir`"""
        if value:
            value = Path(value)
            if not value.exists():
                value.mkdir(parents=True)
        return value

    def __repr__(self):
        return f"LoggerConfig(stdout={self.stdout}, save_dir={self.save_dir}, log_level={self.log_level})"

class Logger:
    """Enhanced Logger specific for AMI using loguru with rich console output and script-specific log files"""

    CONSOLE_THEME = Theme({
        "info": "chartreuse2",
        "warning": "yellow",
        "error": "red",
        "critical": "red bold",
        "debug": "misty_rose3",
    })

    def __init__(self, config_dict: Dict[str, Any]):
        """Create a new instance with config dictionary"""
        self._config = LoggerConfig(**config_dict)
        self.name = None
        self.console = Console(theme=self.CONSOLE_THEME)
        logger.remove()


    def __call__(self, name: Optional[str] = None):
        """
        Configure logger for a specific module/script
        Expected usage: LoggerObj(__file__) or LoggerObj(custom_name)
        """
        if name:
            self.name = Path(name)
            self._setup_logger()
        return self

    def _setup_logger(self):
        """Set up file logging if save_dir is specified"""
        if self._config.save_dir:
            log_path = Path(self._config.save_dir) / f"{self.name}.log"
            logger.add(
                str(log_path),
                rotation=self._config.rotation,
                retention=self._config.retention,
                compression=self._config.compression,
                level=self._config.log_level,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                filter=lambda record: record["extra"].get("name") == self.name
            )

    def _log(self, level: str, message: str, **kwargs):
        """Internal logging method using loguru and rich console"""
        # First log through loguru for file logging
        logger.bind(name=self.name).log(level, message, **kwargs)

        if self._config.stdout:
            style = level.lower()
            self.console.print(f"[{style}]{level: <8}[/{style}] | {self.name} - {message}")

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message"""
        self._log("ERROR", message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self._log("CRITICAL", message, **kwargs)

    def exception(self, message: str, **kwargs):
        """Log an exception with traceback"""
        self._log("ERROR", message, **kwargs)
        if "exception" in kwargs:
            self.console.print_exception(show_locals=True)

    @property
    def level(self):
        """Return the current log level"""
        return self._config.log_level

    @property
    def _logger(self):
        return logger

from functools import cached_property

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

    @cached_property
    def logs(self) -> Logger:
        """
        Returns the logger instance for the package.
        Lazily creates the logger on first access and caches it.
        """
        log_name = f"{self.__module__}.{self.__class__.__name__}"
        return Logger(Config().log_config)(log_name)
