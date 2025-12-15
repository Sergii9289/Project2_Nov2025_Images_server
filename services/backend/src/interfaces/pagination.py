from typing import Any


class PaginationError(Exception):
    """Base class for pagination-related errors."""
    pass


class InvalidPageNumberError(PaginationError):
    """Raised when the page number is invalid (not a positive integer)."""

    def __init__(self, value: Any):
        self.value = value
        super().__init__(f"Invalid page number: {value}. Page number must be a positive integer.")


class InvalidPerPageError(PaginationError):
    """Raised when the per_page value is invalid (not a positive integer)."""

    def __init__(self, value: Any):
        self.value = value
        super().__init__(f"Invalid per_page value: {value}. Per page must be a positive integer.")
