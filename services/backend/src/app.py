import json
# Генерація випадкового UUID (v4)
import uuid
# це стандартний модуль Python, який надає високорівневі операції з файлами та директоріями
import shutil
from multiprocessing import Process, current_process
from datetime import datetime, UTC, timezone
from typing import cast, Any
from http.server import HTTPServer, BaseHTTPRequestHandler

# Python-бібліотека для обробки multipart/form-data
from python_multipart import parse_form
from exceptions.api_errors import NotSupportedFormatError, MaxSizeExceedError
from interfaces.protocols import SupportsWrite
import os
import re
import unicodedata
import urllib
from db.dependencies import get_image_repository
from db.dto import ImageDTO
from exceptions.api_errors import APIError
from exceptions.repository_errors import RepositoryError
from interfaces.protocols import RequestHandlerFactory
from settings.config import config
from settings.logging_config import get_logger
from mixins.http import HeadersMixin, JsonResponseMixin, LoggingMixin


def sanitize_filename(name: str) -> str:
    # Перетворюємо кирилицю та інші символи у латиницю (якщо можливо)
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
    # Замінюємо все, що не букви/цифри/дефіс/підкреслення, на "_"
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    return name


logger = get_logger(__name__)


class UploadHandler(BaseHTTPRequestHandler, HeadersMixin, JsonResponseMixin, LoggingMixin):

    def do_DELETE(self):
        if self.path.startswith('/api/delete/'):
            filename = self.path.removeprefix('/api/delete/')
            file_path = os.path.join(config.IMAGE_DIR, filename)

            repository = get_image_repository()

            # Перевірка: чи є запис у БД
            try:
                image = repository.get_by_filename(filename)
                if not image:
                    logger.warning(f"✖ No DB record found for: {filename}")
                    self.send_json_error(404, "File record not found in DB")
                    return
            except RepositoryError as e:
                logger.error(f"✖ DB error while fetching record: {e.message}")
                self.send_json_error(e.status_code, e.message)
                return

            # Видалення файлу з диску
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"✓ Deleted file from disk: {filename}")
                except Exception as e:
                    logger.error(f"✖ Failed to delete file: {e}")
                    self.send_json_error(500, "Failed to delete file from disk")
                    return
            else:
                logger.warning(f"✖ File not found on disk: {filename}")
                # навіть якщо файлу немає, все одно видаляємо запис у БД

            # Видалення запису з БД
            try:
                repository.delete_by_filename(filename)
                logger.info(f"✓ Deleted DB record for: {filename}")
            except RepositoryError as e:
                logger.error(f"✖ Failed to delete DB record: {e.message}")
                self.send_json_error(e.status_code, e.message)
                return

            # Успішна відповідь
            self.set_headers(200, {"Content-Type": "application/json"})
            self.wfile.write(json.dumps({"detail": "File and DB record deleted"}).encode())
        else:
            logger.warning(f"✖ Unsupported DELETE path: {self.path}")
            self.send_json_error(404, "Not Found")

    def do_POST(self):
        logger.info("POST request received: %s", self.path)

        if self.path != '/upload/':
            logger.warning("Invalid POST path: %s", self.path)
            self.send_json_error(404, 'Not Found')
            return

        content_type = self.headers.get('Content-Type', "")
        if "multipart/form-data" not in content_type:
            logger.warning("Invalid Content-Type: %s", content_type)
            self.send_json_error(400, "Bad Request: Expected multipart/form-data.")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        logger.info("Content-Length: %d", content_length)

        headers = {
            'Content-Type': content_type,
            "Content-Length": str(content_length)
        }

        saved_file_info = {}

        def on_file(file: Any):
            logger.info("→ on_file called with: %s", file.file_name)

            filename = file.file_name.decode('utf-8') if file.file_name else "uploaded_file"
            ext = os.path.splitext(filename)[1].lower()

            if ext not in config.SUPPORTED_FORMATS:
                logger.warning("Unsupported format: %s", ext)
                raise NotSupportedFormatError(config.SUPPORTED_FORMATS)

            file.file_object.seek(0, os.SEEK_END)
            size = file.file_object.tell()
            file.file_object.seek(0)

            logger.info("File size: %d bytes", size)

            if size > config.MAX_FILE_SIZE:
                logger.warning("File too large: %d bytes", size)
                raise MaxSizeExceedError(config.MAX_FILE_SIZE)

            original_name = os.path.splitext(filename)[0].lower()
            safe_name = sanitize_filename(original_name)
            unique_name = f'{safe_name}_{uuid.uuid4()}{ext}'
            os.makedirs(config.IMAGE_DIR, exist_ok=True)

            file_path = os.path.join(config.IMAGE_DIR, unique_name)
            logger.info("Saving file to: %s", os.path.abspath(file_path))

            try:
                with open(file_path, 'wb') as f:
                    file.file_object.seek(0)
                    shutil.copyfileobj(file.file_object, cast(SupportsWrite, f))
            except Exception as e:
                logger.error("Failed to save file: %s", e)
                raise APIError(500, "Internal Server Error")

            saved_file_info['filename'] = unique_name
            saved_file_info['url'] = f'/images/{unique_name}'
            saved_file_info['size'] = size
            saved_file_info['original_name'] = filename
            saved_file_info['file_type'] = ext
            logger.info("File saved successfully: %s", unique_name)

        try:
            parse_form(headers, self.rfile, lambda _: None, on_file)
        except APIError as e:
            logger.error("APIError: %s", e.message)
            self.send_json_error(e.status_code, e.message)
            return

        # --- інтеграція з БД ---
        repository = get_image_repository()
        image_dto = ImageDTO(
            filename=saved_file_info['filename'],
            original_name=saved_file_info['original_name'],
            size=saved_file_info['size'],
            file_type=saved_file_info['file_type']
        )

        try:
            repository.create(image_dto)
        except RepositoryError as e:
            logger.error("Failed to save image metadata to DB: %s", e.message)
            self.send_json_error(e.status_code, e.message)
            return

        logger.info("Upload completed: %s", saved_file_info['filename'])
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(saved_file_info).encode())

    def do_GET(self):
        html_path = os.path.join('/usr/src/frontend', 'index.html')
        # html_path = os.path.join(BASE_DIR, 'services', 'frontend', 'index.html')

        if self.path == '/':
            try:
                with open(html_path, 'rb') as f:
                    self.set_headers(200, {"Content-Type": "text/html"})
                    self.wfile.write(f.read())
                    logger.info("→ Served index.html")
            except FileNotFoundError:
                logger.error("✖ index.html not found")
                self.send_json_error(404, "index.html not found")
            return

        if self.path.startswith('/api/files'):
            try:
                parsed_url = urllib.parse.urlparse(self.path)
                query_params = urllib.parse.parse_qs(parsed_url.query)

                limit = int(query_params.get("limit", [10])[0])
                offset = int(query_params.get("offset", [0])[0])

                repository = get_image_repository()
                files = repository.list_all(limit=limit, offset=offset)
                total_count = repository.count()

                result = {
                    "items": [
                        {
                            "filename": img.filename,
                            "display_name": (
                                "_".join(img.original_name.split("_")[:-1]) + os.path.splitext(img.original_name)[1]
                                if "_" in os.path.splitext(img.original_name)[0]
                                else img.original_name
                            )
                        }
                        for img in files
                    ],
                    "totalCount": total_count
                }

                self.set_headers(200, {"Content-Type": "application/json"})
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
                logger.info(f"→ Served files list (limit={limit}, offset={offset}, total={total_count})")

            except Exception as e:
                logger.error(f"✖ Failed to get files: {e}")
                self.send_json_error(500, "Failed to get files")
            return

        if self.path.startswith('/media/'):
            image_name = self.path.removeprefix('/media/')
            image_path = os.path.join(config.IMAGE_DIR, image_name)

            if os.path.isfile(image_path):
                ext = os.path.splitext(image_path)[1].lower()
                content_types = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }
                content_type = content_types.get(ext, 'application/octet-stream')
                try:
                    with open(image_path, 'rb') as f:
                        self.set_headers(200, {"Content-Type": content_type})
                        self.wfile.write(f.read())
                        logger.info(f"→ Served image: {image_name}")
                except Exception as e:
                    logger.error(f"✖ Failed to serve image: {e}")
                    self.send_json_error(500, "Failed to serve image.")
            else:
                logger.warning(f"✖ Image not found: {image_path}")
                self.send_json_error(404, "Image not found.")
            return

        if self.path.startswith('/frontend/'):
            static_path = os.path.join('/usr/src/frontend', self.path.removeprefix('/frontend/'))

            # static_path = os.path.join(BASE_DIR, 'services', self.path.lstrip('/'))
            if os.path.isfile(static_path):
                ext = os.path.splitext(static_path)[1].lower()
                content_types = {
                    '.css': 'text/css',
                    '.js': 'application/javascript',
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.svg': 'image/svg+xml',
                    '.gif': 'image/gif'
                }
                content_type = content_types.get(ext, 'application/octet-stream')
                try:
                    with open(static_path, 'rb') as f:
                        self.set_headers(200, {"Content-Type": content_type})
                        self.wfile.write(f.read())
                        # Не логувати успішні static-файли
                except Exception as e:
                    logger.error(f"✖ Failed to serve static file: {e}")
                    self.send_json_error(500, "Failed to serve static file.")
            else:
                logger.warning(f"✖ Static file not found: {self.path}")
                self.send_json_error(404, "Static file not found.")
            return

        if self.path == '/images/':
            # images_path = os.path.join(BASE_DIR, 'services', 'frontend', 'images.html')
            images_path = os.path.join('/usr/src/frontend', 'images.html')
            if os.path.isfile(images_path):
                try:
                    with open(images_path, 'rb') as f:
                        self.set_headers(200, {"Content-Type": "text/html"})
                        self.wfile.write(f.read())
                        logger.info("→ Served images.html")
                except Exception as e:
                    logger.error(f"✖ Failed to serve images.html: {e}")
                    self.send_json_error(500, "Failed to serve images.html")
            else:
                logger.warning("✖ images.html not found")
                self.send_json_error(404, "images.html not found")
            return

        if self.path == '/upload/':
            # upload_path = os.path.join(BASE_DIR, 'services', 'frontend', 'upload.html')
            upload_path = os.path.join('/usr/src/frontend', 'upload.html')
            if os.path.isfile(upload_path):
                try:
                    with open(upload_path, 'rb') as f:
                        self.set_headers(200, {"Content-Type": "text/html"})
                        self.wfile.write(f.read())
                        logger.info("→ Served upload.html")
                except Exception as e:
                    logger.error(f"✖ Failed to serve upload.html: {e}")
                    self.send_json_error(500, "Failed to serve upload.html")
            else:
                logger.warning("✖ upload.html not found")
                self.send_json_error(404, "upload.html not found")
            return

        logger.warning(f"✖ Unknown GET path: {self.path}")
        self.send_json_error(404, "Not Found")


"""For 1 process"""


# def run():
#     server = HTTPServer(("0.0.0.0", 8000), cast(RequestHandlerFactory, UploadHandler))
#     print("Server running on http://localhost:8000 ...")
#     server.serve_forever()


"""Use this for 10 processes"""

def run_server_on_port(port: int):
    """Starts a single HTTP server instance on the specified port.

    Args:
        port (int): The port number to bind the HTTP server to.

    Side effects:
        - Starts blocking HTTP server loop.
        - Logs process and port information.
    """
    current_process().name = f"worker-{port}"
    logger.info(f"Starting server on http://0.0.0.0:{port}")
    server = HTTPServer(("0.0.0.0", port), cast(RequestHandlerFactory, UploadHandler))
    server.serve_forever()


def run(workers: int = 1, start_port: int = 8000):
    """Starts multiple server worker processes for concurrent handling.

    Args:
        workers (int): Number of worker processes to spawn.
        start_port (int): Starting port number for workers.

    Side effects:
        - Launches `workers` processes each listening on a unique port.
        - Logs worker startup.
    """
    for i in range(workers):
        port = start_port + i
        p = Process(target=run_server_on_port, args=(port,))
        p.start()
        logger.info(f"Worker {i + 1} started on port {port}")

if __name__ == '__main__':
    # run()
    run(workers=config.WEB_SERVER_WORKERS, start_port=config.WEB_SERVER_START_PORT)
