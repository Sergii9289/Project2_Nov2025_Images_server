import logging

from pathlib import Path

from config import config

import logging


# def get_logger(name: str = __name__) -> logging.Logger:
#     logger = logging.getLogger(name)
#     logger.setLevel(logging.INFO)
#     handler = logging.StreamHandler()
#     formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#     handler.setFormatter(formatter)
#     logger.addHandler(handler)
#     return logger

def get_logger(name: str = __name__) -> logging.Logger:
    logger = logging.getLogger(name)

    # - Перевіряє, чи логер ще не має обробників (handlers). інакше при повторному виклику логування буде дублюватися.
    if not logger.handlers:

        # Консольний логер
        # Створюємо обробник, який виводить логи в консоль.
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # Файловий логер, який пише логи у файл. Лише рівень WARNING і вище потрапляє у файл.
        log_file: Path = config.LOG_DIR / 'app.log'
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.WARNING)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        logger.setLevel(logging.INFO)
    return logger
