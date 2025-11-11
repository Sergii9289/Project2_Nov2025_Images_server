import logging
from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parents[4]

load_dotenv()  # Завантажує змінні з .env

def get_logger(name: str = __name__) -> logging.Logger:
    logger = logging.getLogger(name)

    if not logger.handlers:
        # Консольний логер
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # Файловий логер
        log_dir = BASE_DIR / os.getenv("LOG_DIR", "logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "app.log"

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)  # було WARNING
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        logger.setLevel(logging.INFO)

    return logger