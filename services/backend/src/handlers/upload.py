import os
import uuid
import shutil
from typing import cast

from PIL import  Image, UnidentifiedImageError

from services.backend.src.settings.config import config
from services.backend.src.exceptions.api_errors import NotSupportedFormatError, MaxSizeExceedError
from services.backend.src.interfaces.protocols import SupportsWrite

def handle_uploaded_file(file) -> dict[str, str]:
    filename = file.file_name.decode("utf-8") if file.file_name else "uploaded_file"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in config.SUPPORTED_FORMATS:
        raise NotSupportedFormatError(config.SUPPORTED_FORMATS)

    file.file_object.seek(0, os.SEEK_END)
    size = file.file_object.tell()
    file.file_object.seek(0)

    if size > config.MAX_FILE_SIZE:
        raise MaxSizeExceedError(config.MAX_FILE_SIZE)

    try:
        image = Image.open(file.file_object)
        image.verify()
        file.file_object.seek(0)
    except (UnidentifiedImageError, OSError):
        raise NotSupportedFormatError(config.SUPPORTED_FORMATS)

    original_name = os.path.splitext(filename)[0].lower()
    unique_name = f"{original_name}_{uuid.uuid4()}{ext}"
    os.makedirs(config.IMAGE_DIR, exist_ok=True)
    file_path = os.path.join(config.IMAGE_DIR, unique_name)

    with open(file_path, 'wb') as f:
        file.file_object.seek(0)
        shutil.copyfileobj(file.file_object, cast(SupportsWrite, f))

    return {
        "filename": unique_name,
        "url": f'/images/{unique_name}'
    }