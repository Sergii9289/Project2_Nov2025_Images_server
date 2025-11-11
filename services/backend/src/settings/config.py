from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[4]

class AppConfig(BaseSettings):
    username: str | None = None
    password: str | None = None

    # Шляхи з .env — але вони можуть бути відносними
    IMAGE_DIR: str = "images"
    LOG_DIR: str = "logs"

    MAX_FILE_SIZE: int = 5 * 1024 * 1024
    SUPPORTED_FORMATS: set[str] = {'.jpg', '.png', '.gif'}

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8"
    )

    def resolve_paths(self) -> None:
        # Якщо шлях не абсолютний — зробити його відносно BASE_DIR
        if not Path(self.IMAGE_DIR).is_absolute():
            self.IMAGE_DIR = str(BASE_DIR / self.IMAGE_DIR)
        if not Path(self.LOG_DIR).is_absolute():
            self.LOG_DIR = str(BASE_DIR / self.LOG_DIR)

config = AppConfig()
config.resolve_paths()