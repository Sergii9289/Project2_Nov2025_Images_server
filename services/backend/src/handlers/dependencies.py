"""Handler dependency injection module.

This module provides singleton instances of handlers using the dependency injection pattern.
It ensures that only a single instance of each handler is created and reused across
the application, improving resource usage and maintaining consistent behavior.
"""

from typing import Optional

from handlers.files import FileHandler
from interfaces.handlers import FileHandlerInterface
from settings.config import config


_file_handler: Optional[FileHandlerInterface] = None


def get_file_handler() -> FileHandlerInterface:
    """Get or create a singleton instance of the file handler.

    Creates a FileHandler instance if one doesn't already exist,
    ensuring consistent handling of file operations throughout
    the application.

    Returns:
        FileHandlerInterface: A singleton instance of the file handler.

    Side effects:
        - On first call, creates a handler instance with configuration settings.
    """
    global _file_handler
    if _file_handler is None:
        _file_handler = FileHandler(
            images_dir=config.IMAGES_DIR,
            max_file_size=config.MAX_FILE_SIZE,
            supported_formats=config.SUPPORTED_FORMATS
        )
    return _file_handler