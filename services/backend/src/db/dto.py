from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class ImageDTO:
    # Data Transfer Object for image metadata

    filename: str
    original_name: str
    size: int
    file_type: str

    def as_dict(self) -> Dict[str, Any]:
        # Convert DTO to a dictionary for serialization

        return asdict(self)


@dataclass(kw_only=True)
class ImageDetailsDTO(ImageDTO):
    """Data Transfer Object for detailer image information"""

    id: int
    upload_time: str
