from http.server import HTTPServer
from socketserver import BaseRequestHandler
from typing import Protocol, TypeVar, Any, BinaryIO

_T_contra = TypeVar("_T_contra", contravariant=True)


class SupportsWrite(Protocol[_T_contra]):

    def write(self, s: _T_contra, /) -> object: ...


class RequestHandlerFactory(Protocol):

    def __call__(self, request: Any, client_address: Any, server: HTTPServer) -> BaseRequestHandler: ...


class HandlerProtocol(Protocol):
    def send_response(self, code: int) -> None: ...

    def send_header(self, key: str, value: str) -> None: ...

    def end_headers(self) -> None: ...

    path: str
    wfile: BinaryIO
