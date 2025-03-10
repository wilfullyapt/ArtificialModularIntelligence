"""
Enhanced logging module for AMI with script-specific log files and rich console output
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel, field_validator
import rich.logging
from rich.console import Console
from rich.theme import Theme
from loguru import logger
from datetime import datetime

class LoggerConfig(BaseModel):
    """Enhanced Logging Configuration as a Pydantic dataclass"""
    stdout: bool = True
    save_dir: Optional[Path | str] = None
    log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = 'INFO'
    rotation: str = "1 day"  # Rotation period for log files
    retention: str = "30 days"  # How long to keep log files
    compression: str = "gz"  # Compression format for rotated logs

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
    """Enhanced Logger specific for AMI with rich console output and script-specific log files"""

    CONSOLE_THEME = Theme({
        "info": "cyan",
        "warning": "yellow",
        "error": "red",
        "critical": "red bold",
        "debug": "purple",
    })

    def __init__(self, config_dict: Dict[str, Any]):
        """Create a new instance with config dictionary"""
        self._config = LoggerConfig(**config_dict)
        self._logger = None
        self.name = None
        self.console = Console(theme=self.CONSOLE_THEME)
        
        # Configure loguru for file logging
        logger.configure(handlers=[])

    def __call__(self, name: Optional[str] = None):
        """
        Configure logger for a specific module/script
        Expected usage: LoggerObj(__file__) or LoggerObj(custom_name)
        """
        if name:
            self.name = Path(name).stem
            self._setup_logger()
        return self

    def _setup_logger(self):
        """Set up both console and file logging"""
        if self._config.stdout:
            # Configure rich console handler
            console_handler = rich.logging.RichHandler(
                console=self.console,
                show_time=True,
                show_path=False,
                markup=True,
                rich_tracebacks=True
            )
            console_format = "%(message)s"
            console_handler.setFormatter(logging.Formatter(console_format))
            
            # Create standard logger for console output
            self._logger = logging.getLogger(self.name)
            self._logger.setLevel(self._config.log_level)
            self._logger.addHandler(console_handler)

        # Configure file logging with loguru if save_dir is specified
        if self._config.save_dir:
            log_path = Path(self._config.save_dir) / f"{self.name}.log"
            logger.add(
                str(log_path),
                rotation=self._config.rotation,
                retention=self._config.retention,
                compression=self._config.compression,
                level=self._config.log_level,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
            )

    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method that handles both console and file logging"""
        if self._logger:
            self._logger.log(level, message, **kwargs)
        
        # Map logging levels to loguru levels
        level_map = {
            logging.DEBUG: "DEBUG",
            logging.INFO: "INFO",
            logging.WARNING: "WARNING",
            logging.ERROR: "ERROR",
            logging.CRITICAL: "CRITICAL"
        }
        
        # Log to file using loguru
        logger.log(level_map[level], message, **kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message"""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self._log(logging.CRITICAL, message, **kwargs)

    def exception(self, message: str, exc_info=True, **kwargs):
        """Log an exception with traceback"""
        self._log(logging.ERROR, message, exc_info=exc_info, **kwargs)

    @property
    def level(self):
        """Return the current log level"""
        return self._config.log_level