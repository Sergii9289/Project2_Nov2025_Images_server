"""DTOs for file operations.

This module contains Data Transfer Objects for passing file-related data
between layers of the application.
"""

from dataclasses import dataclass, field
from typing import Optional
import datetime


@dataclass
class UploadedFileDTO:
    """Data Transfer Object for representing an uploaded file.

    This DTO encapsulates all the metadata about a file that has been
    successfully uploaded and processed by the system.

    Attributes:
        filename: The unique filename stored in the system.
        original_name: The original name of the uploaded file.
        size: The size of the file in bytes.
        extension: The file extension (e.g., .jpg, .png).
        url: The URL path to access the file.
        upload_time: The timestamp when the file was uploaded.
    """
    filename: str
    original_name: str
    size: int
    extension: str
    url: str
    upload_time: datetime.datetime = field(default_factory=datetime.datetime.now)

    def as_dict(self) -> dict:
        """Convert the DTO to a dictionary for JSON serialization.

        Returns:
            A dictionary representation of the uploaded file.
        """
        return {
            "filename": self.filename,
            "original_name": self.original_name,
            "size": self.size,
            "extension": self.extension,
            "url": self.url,
            "upload_time": self.upload_time.isoformat()
        }

