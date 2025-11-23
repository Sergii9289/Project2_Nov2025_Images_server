from http.server import HTTPServer
from socketserver import BaseRequestHandler
from typing import Protocol, TypeVar, Any

_T_contra = TypeVar("_T_contra", contravariant=True)

class SupportsWrite(Protocol[_T_contra]):

    def write(self, s: _T_contra, /) -> object: ...

class RequestHandlerFactory(Protocol):

    def __call__(self, request: Any, client_address: Any, server: HTTPServer) -> BaseRequestHandler: ...