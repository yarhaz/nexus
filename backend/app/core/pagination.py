from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class CursorPage(BaseModel, Generic[T]):
    """Cursor-based pagination for catalog entities."""
    data: list[T]
    next_cursor: str | None = None
    has_more: bool = False
    total: int | None = None


class OffsetPage(BaseModel, Generic[T]):
    """Offset-based pagination for reports/DORA/scorecards."""
    data: list[T]
    page: int
    page_size: int
    total: int
    total_pages: int

    @classmethod
    def create(cls, data: list[T], page: int, page_size: int, total: int) -> "OffsetPage[T]":
        import math
        return cls(
            data=data,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=math.ceil(total / page_size) if page_size > 0 else 0,
        )
