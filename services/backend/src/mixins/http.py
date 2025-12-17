import json
from typing import Any
from interfaces.protocols import HandlerProtocol

class HeadersMixin:
    def set_headers(self: HandlerProtocol, status_code: int, headers: dict):
        self.send_response(status_code)
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()

class LoggingMixin:
    def log_message(self: HandlerProtocol, format: str, *args: Any) -> None:
        if self.path.startswith('/frontend/'):
            return
        super().log_message(format, *args)

class JsonResponseMixin:
    def send_json_error(self: HandlerProtocol, status_code: int, message: str) -> None:
        self.set_headers(status_code, {"Content-Type": "application/json"})
        response = {"detail": message}
        self.wfile.write(json.dumps(response).encode())