from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


class MessageResponse(BaseModel):
    message: str


def paginate(total: int, page: int, page_size: int) -> int:
    if page_size <= 0:
        return 0
    return (total + page_size - 1) // page_size
