"""HTTP-related mixins for request handling.

This module provides mixins that can be used with HTTP request handlers
to add routing and parameter parsing functionality, separating these
concerns from the main request handling logic.

Side effects:
    - None. This module only defines classes.
"""
import json
import re
from logging import Logger
from typing import Dict, Optional, Any, BinaryIO, Tuple
from abc import abstractmethod


class JsonResponseMixin:
    """Mixin that adds JSON response capabilities to HTTP request handlers.

    This mixin provides methods to:
    - Send JSON success responses
    - Send JSON error responses with proper logging

    Implementing classes should have:
    - send_response, send_header, end_headers methods (like BaseHTTPRequestHandler)
    - wfile attribute with write method
    - command and path attributes for logging
    - logger attribute for logging errors and warnings
    """

    wfile: BinaryIO

    @abstractmethod
    def send_response(self, code: int) -> None:
        pass

    @abstractmethod
    def send_header(self, keyword: str, value: str) -> None:
        pass

    @abstractmethod
    def end_headers(self) -> None:
        pass

    @property
    def logger(self) -> Logger:
        """Return a logger for error and warning messages."""
        raise NotImplementedError("Subclasses must provide a logger property")

    def send_json_error(self, status_code: int, message: str) -> None:
        """Sends a JSON error response and logs the message.

        Args:
            status_code (int): HTTP status code to return.
            message (str): Error message to return and log.

        Side effects:
            - Logs the error or warning.
            - Writes JSON response to the client.
        """
        command = getattr(self, 'command', 'UNKNOWN')
        path = getattr(self, 'path', 'UNKNOWN')

        if status_code >= 500:
            self.logger.error(f"{command} {path} → {status_code}: {message}")
        else:
            self.logger.warning(f"{command} {path} → {status_code}: {message}")

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        response = {"detail": message}
        self.wfile.write(json.dumps(response).encode())

    def send_json_response(self, status_code: int, data: Any) -> None:
        """Sends a JSON success response.

        Args:
            status_code (int): HTTP status code to return.
            data (Any): Data to serialize as JSON.

        Side effects:
            - Writes JSON response to the client.
        """
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


class RouterMixin:
    """Mixin that adds routing capabilities to HTTP request handlers.

    This mixin provides methods to:
    - Register routes for different HTTP methods with dynamic parameters
    - Parse path and query parameters
    - Dispatch requests to appropriate handler methods

    Implementing classes should define:
    - route dictionaries for each HTTP method
    - handler methods referenced in routes
    - _send_json_error method for error reporting
    """

    routes_get: Dict[str, str] = {}
    routes_post: Dict[str, str] = {}
    routes_delete: Dict[str, str] = {}
    routes_put: Dict[str, str] = {}

    path: Optional[str] = None
    route_params: Dict[str, str] = {}

    @abstractmethod
    def send_json_error(self, status_code: int, message: str) -> None:
        """Abstract method that must be implemented by classes using this mixin.

        Sends an error response to the client with the given status code and message.

        Args:
            status_code (int): HTTP status code to return.
            message (str): Error message to return.

        Side effects:
            - Sends response to client.
        """
        pass

    def _route_to_regex(self, route: str) -> Tuple[re.Pattern, list]:
        """Convert route pattern to regex pattern.

        Args:
            route (str): Route pattern like '/upload/<filename>' or '/api/<path>/<id>'

        Returns:
            Tuple[re.Pattern, list]: Compiled regex pattern and list of parameter names
        """
        param_names = []
        regex_pattern = route

        import re as regex_module
        param_pattern = r'<([^>]+)>'

        for match in regex_module.finditer(param_pattern, route):
            param_name = match.group(1)
            param_names.append(param_name)
            regex_pattern = regex_pattern.replace(f'<{param_name}>', '([^/]+)')

        regex_pattern = f'^{regex_pattern}$'

        compiled_pattern = regex_module.compile(regex_pattern)
        return compiled_pattern, param_names

    def _match_route(self, path: str, routes: Dict[str, str]) -> Tuple[Optional[str], Dict[str, str]]:
        """Match path against route patterns and extract parameters.

        Args:
            path (str): Request path to match
            routes (Dict[str, str]): Route patterns mapped to handler names

        Returns:
            Tuple[Optional[str], Dict[str, str]]: Handler name and extracted parameters
        """
        if path in routes:
            return routes[path], {}

        for route_pattern, handler_name in routes.items():
            if '<' in route_pattern:
                regex_pattern, param_names = self._route_to_regex(route_pattern)
                match = regex_pattern.match(path)

                if match:
                    params = {}
                    for i, param_name in enumerate(param_names):
                        params[param_name] = match.group(i + 1)

                    return handler_name, params

        for route_prefix, handler_name in routes.items():
            if '<' not in route_prefix and path.startswith(route_prefix):
                return handler_name, {}

        return None, {}

    def handle_request(self, routes: Dict[str, str]) -> None:
        """Resolves path to appropriate handler method and calls it.

        Args:
            routes (Dict[str, str]): Mapping of path patterns to handler method names.

        Side effects:
            - Calls appropriate handler method.
            - Sends 404 or 500 response if handler is not found or not implemented.
        """
        base_path = self.path
        if base_path is None:
            self.send_json_error(500, "Path not available")
            return

        if '?' in base_path:
            base_path, _ = base_path.split('?', 1)

        handler_name, params = self._match_route(base_path, routes)

        self.route_params = params

        if not handler_name:
            self.send_json_error(404, "Not Found")
            return

        handler = getattr(self, handler_name, None)
        if not handler:
            self.send_json_error(500, "Handler not implemented.")
            return

        handler()

    def parse_query_params(self) -> Dict[str, str]:
        """Extracts query parameters from the request path.

        Returns:
            Dict[str, str]: Dictionary of query parameters.
        """
        if self.path is None:
            return {}

        query_params = {}
        if '?' in self.path:
            _, query_string = self.path.split('?', 1)
            for param in query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    query_params[key] = value

        return query_params

    def extract_path_param(self, prefix: str) -> Optional[str]:
        """Extracts a path parameter from a URL with the given prefix.

        Args:
            prefix (str): The URL prefix, including trailing slash.

        Returns:
            Optional[str]: The extracted parameter or None if not found.
        """
        if self.path is None:
            return None

        if not self.path.startswith(prefix):
            return None

        param = self.path[len(prefix):]
        return param if param else None

    def get_route_param(self, param_name: str) -> Optional[str]:
        """Get parameter value from current route.

        Args:
            param_name (str): Name of the parameter to get

        Returns:
            Optional[str]: Parameter value or None if not found
        """
        return self.route_params.get(param_name)
