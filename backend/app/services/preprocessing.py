"""Check an uploaded file and turn it into a clean RGB image."""
import io
from typing import Optional

from PIL import Image, ImageOps, UnidentifiedImageError

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp"}


class ImageValidationError(Exception):
    """Raised when an upload cannot be used. `status_code` is the HTTP status to return."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def load_image(data: bytes, content_type: Optional[str], max_bytes: int, max_pixels: int) -> Image.Image:
    """Validate the upload and return an RGB PIL image. Raises ImageValidationError."""
    if not data:
        raise ImageValidationError("The uploaded file is empty.", 400)
    if len(data) > max_bytes:
        raise ImageValidationError(f"File is larger than the {max_bytes // (1024 * 1024)} MB limit.", 413)
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ImageValidationError(
            f"Unsupported file type '{content_type}'. Use JPEG, PNG, WEBP or BMP.", 415
        )

    try:
        with Image.open(io.BytesIO(data)) as probe:
            width, height = probe.size
            if width * height > max_pixels:
                raise ImageValidationError("Image has too many pixels.", 413)
            probe.verify()                       # cheap integrity check
        image = Image.open(io.BytesIO(data))
        image.load()                             # fully decode: catches truncated files
    except ImageValidationError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        raise ImageValidationError("The file is not a valid, readable image.", 400)

    image = ImageOps.exif_transpose(image)        # respect phone camera rotation
    return image.convert("RGB")
