from typing import Optional, List
from psycopg_pool import ConnectionPool
from psycopg.errors import Error as PsycopgError

from interfaces.repositories import (
    ImageRepository,
    ImageDTO,
    ImageDetailsDTO
)
from exceptions.repository_errors import (
    EntityCreationError,
    EntityDeletionError,
    QueryExecutionError
)


class PostgresImageRepository(ImageRepository):
    """Postgres implementation of the ImageRepository interface."""

    def __init__(self, pool: ConnectionPool):
        """Initialization of repository"""
        self._pool = pool

    def create(self, image: ImageDTO) -> ImageDetailsDTO:
        """Create new image record in DB"""
        query = """
            INSERT INTO images (filename, original_name, size, file_type)
            VALUES (%s, %s, %s, %s)
            RETURNING id, upload_time
        """
        try:
            with self._pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        query,
                        (image.filename, image.original_name, image.size, image.file_type),
                    )
                    db_id, upload_time = cur.fetchone() # повертає ОДИН об'єкт
                    conn.commit()

                    return ImageDetailsDTO(
                        id=db_id,
                        filename=image.filename,
                        original_name=image.original_name,
                        size=image.size,
                        file_type=image.file_type,
                        upload_time=upload_time.isoformat() if upload_time else None
                    )
        except PsycopgError as e:
            raise EntityCreationError("image", str(e))
        except Exception as e:
            raise EntityCreationError("image", str(e))

    def delete(self, image_id: int) -> bool:
        """Delete image record by ID"""
        query = "DELETE FROM images WHERE id = %s RETURNING id"
        try:
            with self._pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (image_id,))
                    result = cur.fetchone() # повертає ОДИН об'єкт
                    conn.commit()
                    return result is not None
        except PsycopgError as e:
            raise EntityDeletionError("image", str(e))

    def get_by_id(self, image_id: int) -> Optional[ImageDetailsDTO]:
        """Retrieve image record by ID"""
        query = """
            SELECT id, filename, original_name, size, upload_time, file_type::text
            FROM images
            WHERE id = %s
        """
        try:
            with self._pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (image_id,))
                    row = cur.fetchone() # повертає ОДИН об'єкт
                    if not row:
                        return None

                    db_id, filename, original_name, size, upload_time, file_type = row
                    return ImageDetailsDTO(
                        id=db_id,
                        filename=filename,
                        original_name=original_name,
                        size=size,
                        file_type=file_type,
                        upload_time=upload_time.isoformat() if upload_time else None
                    )
        except PsycopgError as e:
            raise QueryExecutionError("get_by_id", str(e))
        except Exception as e:
            raise QueryExecutionError("get_by_id", str(e))

    def get_by_filename(self, filename: str) -> Optional[ImageDetailsDTO]:
        """Retrieve image record by filename"""
        query = """
            SELECT id, filename, original_name, size, upload_time, file_type::text
            FROM images
            WHERE filename = %s
        """
        try:
            with self._pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (filename,))
                    row = cur.fetchone()
                    if not row:
                        return None

                    db_id, filename, original_name, size, upload_time, file_type = row
                    return ImageDetailsDTO(
                        id=db_id,
                        filename=filename,
                        original_name=original_name,
                        size=size,
                        file_type=file_type,
                        upload_time=upload_time.isoformat() if upload_time else None
                    )
        except PsycopgError as e:
            raise QueryExecutionError("get_by_filename", str(e))
        except Exception as e:
            raise QueryExecutionError("get_by_filename", str(e))

    def delete_by_filename(self, filename: str) -> bool:
        """Delete image record by filename"""
        query = "DELETE FROM images WHERE filename = %s RETURNING id"
        try:
            with self._pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (filename,))
                    result = cur.fetchone()
                    conn.commit()
                    return result is not None
        except PsycopgError as e:
            raise EntityDeletionError("image", str(e))

    def list_all(self, limit: int = 10, offset: int = 0) -> List[ImageDetailsDTO]:
        """List images with pagination.
        limit: maximum number of images to return
        offset: Number of images to skip."""
        query = """
            SELECT id, filename, original_name, size, upload_time, file_type::text
            FROM images
            ORDER BY upload_time DESC
            LIMIT %s OFFSET %s
        """
        try:
            with self._pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (limit, offset))
                    results = cur.fetchall()
                    return [
                        ImageDetailsDTO(
                            id=row[0],
                            filename=row[1],
                            original_name=row[2],
                            size=row[3],
                            upload_time=row[4].isoformat() if row[4] else None,
                            file_type=row[5],
                        )
                        for row in results
                    ]
        except PsycopgError as e:
            raise QueryExecutionError("list_all", str(e))


    def count(self) -> int:
        """Count of total number of imsges"""
        query = "SELECT COUNT(*) FROM images"
        try:
            with self._pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    result = cur.fetchone()
                    return result[0]
        except PsycopgError as e:
            raise QueryExecutionError("count", str(e))

