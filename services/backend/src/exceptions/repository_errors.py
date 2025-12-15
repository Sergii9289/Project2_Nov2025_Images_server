from api_errors import APIError


class RepositoryError(APIError):
    """Base class for repository-related errors"""
    status_code = 500
    message = "Database operation failed"


class EntityNotFoundError(RepositoryError):
    """Raised when an entity can't be found in repository."""
    status_code = 404

    def __init__(self, entity_type: str, identifier):
        message = f"{entity_type} with identifier '{identifier}' not found"
        super().__init__(message)


class EntityCreationError(RepositoryError):
    """Raised when an entity can't be created in repository."""

    def __init__(self, entity_type: str, reason: str = None):
        if reason:
            message = f"Failed to create {entity_type}: {reason}"
        else:
            message = f"Failed to create {entity_type}"
        super().__init__(message)


class EntityDeletionError(RepositoryError):
    """Raised when an entity can't be deleted from repository."""

    def __init__(self, entity_type: str, identifier, reason: str = None):
        if reason:
            message = f"Failed to delete {entity_type} '{identifier}': {reason}"
        else:
            message = f"Failed to delete {entity_type} '{identifier}'"
        super().__init__(message)


class DatabaseConnectionError(RepositoryError):
    """Raised when repository can't connect to database"""
    status_code = 503
    message = "Database connection failed"


class QueryExecutionError(RepositoryError):
    """Raised when a database query fails to execute"""

    def __init__(self, query_type: str, reason: str = None):
        if reason:
            message = f"Failed to execute {query_type} query: {reason}"
        else:
            message = f"Failed to execute {query_type} query"
        super().__init__(message)
