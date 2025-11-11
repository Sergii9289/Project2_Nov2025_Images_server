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


class UploadHandler(BaseHTTPRequestHandler):

    def send_json_error(self, status_code: int, message: str) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        response = {"detail": message}

        self.wfile.write(json.dumps(response).encode())

    def do_POST(self):
        if self.path != '/upload/':
            self.send_json_error(404, 'Not Found')
            return

        content_type = self.headers.get('Content-Type', "")
        if "multipart/form-data" not in content_type:
            self.send_json_error(400, "Bad Request: Expected multipart/form-data.")
            return

        content_length = int(self.headers.get("Content-Length", 0))

        headers = {
            'Content-Type': content_type,
            "Content-Length": str(content_length)
        }

        saved_file_info = {}

        def on_file(file: Any):
            print("→ on_file called with:", file.file_name)

            filename = file.file_name.decode('utf-8') if file.file_name else "uploaded_file"
            ext = os.path.splitext(filename)[1].lower()

            if ext not in config.SUPPORTED_FORMATS:
                raise NotSupportedFormatError(config.SUPPORTED_FORMATS)

            file.file_object.seek(0, os.SEEK_END)
            size = file.file_object.tell()
            file.file_object.seek(0)

            if size > config.MAX_FILE_SIZE:
                raise MaxSizeExceedError(config.MAX_FILE_SIZE)

            original_name = os.path.splitext(filename)[0].lower()
            unique_name = f'{original_name}_{uuid.uuid4()}{ext}'  # створюємо унікальне ім'я файлу
            os.makedirs(config.IMAGE_DIR, exist_ok=True)

            file_path = os.path.join(config.IMAGE_DIR, unique_name)  # створюємо повний шлях
            print("→ Saving to:", os.path.abspath(file_path))
            with open(file_path, 'wb') as f:  # записуємо дані в файл
                file.file_object.seek(0)  # переміщення курсору читання на початок файлу
                # - Копіює вміст з file.file_object (джерело) у f (призначення)
                shutil.copyfileobj(file.file_object, cast(SupportsWrite, f))

            # створюємо headers для нового файлу
            saved_file_info['filename'] = unique_name
            saved_file_info['url'] = f'/images/{unique_name}'

        try:
            parse_form(headers, self.rfile, lambda _: None, on_file)
        except APIError as e:
            self.send_json_error(e.status_code, e.message)
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(saved_file_info).encode())

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{}')
            return

        if self.path == '/upload/':
            files = []
            try:
                filenames = os.listdir(config.IMAGE_DIR)
            except FileNotFoundError:
                self.send_json_error(500, "Images directory not found.")
                return
            except PermissionError:
                self.send_json_error(500, "Permission denied to access images directory.")
                return

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
                self.send_json_error(404, "No images found.")
                return

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            self.wfile.write(json.dumps(files).encode())
            return

        self.send_json_error(404, "Not Found")

print("→ config.IMAGE_DIR =", config.IMAGE_DIR)
print("→ Absolute path =", os.path.abspath(config.IMAGE_DIR))
print("→ config.BASE_DIR =", BASE_DIR)

def run():
    server = HTTPServer(("0.0.0.0", 8000), cast(RequestHandlerFactory, UploadHandler))
    print("Server running on http://localhost:8000 ...")
    server.serve_forever()

if __name__ == '__main__':
    run()