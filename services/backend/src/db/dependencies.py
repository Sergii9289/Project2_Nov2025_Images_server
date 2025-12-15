from typing import Optional

from session import get_connection_pool
from repositories import PostgresImageRepository
from ..interfaces.repositories import ImageRepository

_image_repository: Optional[ImageRepository] = None

def get_image_repository() -> ImageRepository:
    """
    Фабрична функція для отримання екземпляра репозиторію зображень.
    Якщо репозиторій ще не створений — створює його з пулом з'єднань.
    Якщо вже існує — повертає існуючий екземпляр.
    """
    global _image_repository  # вказуємо, що працюємо з глобальною змінною

    # Якщо репозиторій ще не створений
    if _image_repository is None:
        # Отримуємо пул з'єднань до PostgreSQL
        pool = get_connection_pool()
        # Створюємо новий репозиторій на основі пулу
        _image_repository = PostgresImageRepository(pool)

    # Повертаємо екземпляр (новий або вже існуючий)
    return _image_repository
