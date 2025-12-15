from typing import Dict, Optional, Tuple

from dto.pagination import PaginationDTO
from interfaces.pagination import InvalidPageNumberError, InvalidPerPageError


class PaginationMixin:
    """Mixin that adds pagination capabilities to HTTP request handlers.

    This mixin provides methods to:
    - Parse pagination parameters from query parameters
    - Validate pagination parameters
    - Return a standardized PaginationDTO
    """

    def parse_pagination(
            self,
            query_params: Dict[str, str],
            default_page: int = 1,
            default_per_page: int = 10,
            max_per_page: Optional[int] = None
    ) -> PaginationDTO:
        """Parse and validate pagination parameters from query parameters.

        Args:
            query_params (Dict[str, str]): Dictionary of query parameters.
            default_page (int, optional): Default page number if not specified. Defaults to 1.
            default_per_page (int, optional): Default items per page if not specified. Defaults to 10.
            max_per_page (Optional[int], optional): Maximum allowed items per page. Defaults to None (no limit).

        Returns:
            PaginationDTO: Data transfer object with validated pagination parameters.

        Raises:
            InvalidPageNumberError: If page is not a positive integer.
            InvalidPerPageError: If per_page is not a positive integer or exceeds max_per_page.
        """
        page_str = query_params.get('page', str(default_page))
        try:
            page = int(page_str)
            if page <= 0:
                raise InvalidPageNumberError(page_str)
        except ValueError:
            raise InvalidPageNumberError(page_str)

        per_page_str = query_params.get('per_page', str(default_per_page))
        try:
            per_page = int(per_page_str)
            if per_page <= 0:
                raise InvalidPerPageError(per_page_str)
            if max_per_page is not None and per_page > max_per_page:
                per_page = max_per_page
        except ValueError:
            raise InvalidPerPageError(per_page_str)

        return PaginationDTO(page=page, per_page=per_page)

    @staticmethod
    def get_limit_offset(pagination: PaginationDTO) -> Tuple[int, int]:
        """Convert pagination DTO to SQL limit and offset.

        Args:
            pagination (PaginationDTO): Pagination parameters.

        Returns:
            Tuple[int, int]: A tuple of (limit, offset) for SQL queries.
        """
        return pagination.to_sql_params()
