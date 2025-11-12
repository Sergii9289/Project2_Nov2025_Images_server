import json
import os
# Генерація випадкового UUID (v4)
import uuid
# це стандартний модуль Python, який надає високорівневі операції з файлами та директоріями
import shutil
from datetime import datetime, UTC
from typing import cast, Any, BinaryIO

from http.server import HTTPServer, BaseHTTPRequestHandler
# Python-бібліотека для обробки multipart/form-data
from python_multipart import parse_form

from exceptions.api_errors import NotSupportedFormatError, MaxSizeExceedError, APIError
from interfaces.protocols import SupportsWrite, RequestHandlerFactory
from settings.config import config as config, BASE_DIR
from settings.logging_config import get_logger

logger = get_logger(__name__)


class UploadHandler(BaseHTTPRequestHandler):

    def set_headers(self, status_code: int, headers: dict):
        self.send_response(status_code)
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        # Приглушити стандартне логування (наприклад, GET /static/...)
        if self.path.startswith('/static/'):
            return  # нічого не логувати
        super().log_message(format, *args)

    def send_json_error(self, status_code: int, message: str) -> None:
        self.set_headers(status_code, {"Content-Type": "application/json"})
        response = {"detail": message}
        self.wfile.write(json.dumps(response).encode())

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
            unique_name = f'{original_name}_{uuid.uuid4()}{ext}'
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
            logger.info("File saved successfully: %s", unique_name)

        try:
            parse_form(headers, self.rfile, lambda _: None, on_file)
        except APIError as e:
            logger.error("APIError: %s", e.message)
            self.send_json_error(e.status_code, e.message)
            return

        logger.info("Upload completed: %s", saved_file_info['filename'])
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(saved_file_info).encode())

    def do_GET(self):
        html_path = os.path.join(BASE_DIR, 'services', 'static', 'index.html')

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

        if self.path.startswith('/form/'):
            html_path = os.path.join(BASE_DIR, 'services', 'templates', self.path.lstrip('/'))
            if os.path.isfile(html_path):
                try:
                    with open(html_path, 'rb') as f:
                        self.set_headers(200, {"Content-Type": "text/html"})
                        self.wfile.write(f.read())
                        logger.info(f"→ Served HTML: {self.path}")
                except Exception as e:
                    logger.error(f"✖ Failed to serve HTML: {e}")
                    self.send_json_error(500, "Failed to serve HTML file.")
            else:
                logger.warning(f"✖ HTML not found: {self.path}")
                self.send_json_error(404, "HTML file not found.")
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

        if self.path.startswith('/static/'):
            static_path = os.path.join(BASE_DIR, 'services', self.path.lstrip('/'))
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
            images_path = os.path.join(BASE_DIR, 'services', 'static', 'form', 'images.html')
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
            try:
                filenames = os.listdir(config.IMAGE_DIR)
            except FileNotFoundError:
                logger.error("✖ Images directory not found")
                self.send_json_error(500, "Images directory not found.")
                return
            except PermissionError:
                logger.error("✖ Permission denied to access images directory")
                self.send_json_error(500, "Permission denied to access images directory.")
                return

            files = []
            for filename in filenames:
                filepath = os.path.join(config.IMAGE_DIR, filename)
                ext = os.path.splitext(filename)[1].lower()
                if ext in config.SUPPORTED_FORMATS and os.path.isfile(filepath):
                    created_at = datetime.fromtimestamp(os.path.getatime(filepath), tz=UTC).isoformat()
                    size = os.path.getsize(filepath)
                    files.append({
                        'filename': filename,
                        'created_at': created_at,
                        'size': size
                    })

            if not files:
                logger.warning("✖ No images found")
                self.send_json_error(404, "No images found.")
                return

            logger.info(f"→ Returned {len(files)} image(s)")
            self.set_headers(200, {"Content-Type": "application/json"})
            self.wfile.write(json.dumps(files).encode())
            return

        logger.warning(f"✖ Unknown GET path: {self.path}")
        self.send_json_error(404, "Not Found")

def run():
    server = HTTPServer(("0.0.0.0", 8000), cast(RequestHandlerFactory, UploadHandler))
    print("Server running on http://localhost:8000 ...")
    server.serve_forever()

if __name__ == '__main__':
    run()