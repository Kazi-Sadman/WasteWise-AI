"""Application settings, read from environment variables or a .env file."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ folder. Paths are resolved from here, never from the current working directory.
BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    model_path: Path = Path("models/best.pt")
    metadata_path: Path = Path("models/model_metadata.json")
    confidence_threshold: float = 0.25
    iou_threshold: float = 0.7
    image_size: int = 640
    max_upload_mb: int = 10
    max_image_pixels: int = 50_000_000
    device: str = "cpu"

    @staticmethod
    def resolve(path: Path) -> Path:
        """Turn a relative path from the settings into an absolute path under backend/."""
        return path if path.is_absolute() else (BASE_DIR / path).resolve()

    @property
    def model_file(self) -> Path:
        return self.resolve(self.model_path)

    @property
    def metadata_file(self) -> Path:
        return self.resolve(self.metadata_path)

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


def get_settings() -> Settings:
    return Settings()
