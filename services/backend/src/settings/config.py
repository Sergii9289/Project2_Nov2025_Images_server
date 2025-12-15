from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[4]

class AppConfig(BaseSettings):
    username: str | None = None
    password: str | None = None

    # Шляхи з .env — але вони можуть бути відносними
    IMAGE_DIR: str = "images"
    LOG_DIR: str = "logs"

    WEB_SERVER_WORKERS: int
    WEB_SERVER_START_PORT: int

    MAX_FILE_SIZE: int = 5 * 1024 * 1024
    SUPPORTED_FORMATS: set[str] = {'.jpg', '.png', '.gif'}

    POSTGRES_DB: str
    POSTGRES_DB_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str

    PGBOUNCER_USER: str
    PGBOUNCER_PASSWORD: str
    PGBOUNCER_HOST: str
    PGBOUNCER_PORT: int
    USE_PGBOUNCER: bool = True

    @property
    def database_url(self) -> str:
        """Construct PostgreSQL connection string.

        Returns:
            str: Database connection URL in format suitable for psycopg.
        """
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_DB_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def pgbouncer_url(self) -> str:
        """Construct PgBouncer connection string.

        Returns:
            str: PgBouncer connection URL in format suitable for psycopg.
        """
        return (
            f"postgresql://{self.PGBOUNCER_USER}:{self.PGBOUNCER_PASSWORD}@"
            f"{self.PGBOUNCER_HOST}:{self.PGBOUNCER_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def db_url(self) -> str:
        """Return the active database connection URL.

        Uses PgBouncer if USE_PGBOUNCER is set to True, otherwise
        uses direct PostgreSQL connection.

        Returns:
            str: Active database connection URL.
        """
        return self.pgbouncer_url if self.USE_PGBOUNCER else self.database_url


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