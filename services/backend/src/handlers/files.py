import os
from datetime import datetime, UTC

from settings.config import config
from interfaces.handlers import FileHandlerInterface

def list_uploaded_images() -> list[dict[str, str | int]]:
    """Повертає список метаданих зображення (name, size, created_at) з папки з завантаженнями."""
    files = []

    try:
        filenames = os.listdir(config.IMAGE_DIR)
    except FileNotFoundError:
        raise FileNotFoundError('Images directory not found.')
    except PermissionError:
        raise PermissionError('Permission denied to access images directory.')

    for filename in filenames:
        filepath = os.path.join(config.IMAGE_DIR, filename)
        ext = os.path.splitext(filename)[1].lower()

        if ext in config.SUPPORTED_FORMATS and os.path.isfile(filepath):
            created_at = datetime.fromtimestamp(os.path.getctime(filepath), tz=UTC).isoformat()
            size = os.path.getsize(filepath)
            files.append({
                "filename": filename,
                "size": size,
                "created_at": created_at
            })
    return files

class FileHandler(FileHandlerInterface):
    pass


# print(list_uploaded_images())