from dataclasses import dataclass
from typing import Tuple


@dataclass
class PaginationDTO:
    """Data Transfer Object for pagination parameters.

    Attributes:
        page (int): Current page number (1-based).
        per_page (int): Number of items per page.
    """
    page: int
    per_page: int

    @staticmethod
    def to_limit_offset(page: int, per_page: int) -> Tuple[int, int]:
        """Convert page and per_page to SQL limit and offset.

        Args:
            page (int): Page number (1-based).
            per_page (int): Number of items per page.

        Returns:
            Tuple[int, int]: A tuple of (limit, offset) for SQL queries.
        """
        return per_page, (page - 1) * per_page

    def to_sql_params(self) -> Tuple[int, int]:
        """Convert this DTO's page and per_page to SQL limit and offset.

        Returns:
            Tuple[int, int]: A tuple of (limit, offset) for SQL queries.
        """
        return self.to_limit_offset(self.page, self.per_page)
