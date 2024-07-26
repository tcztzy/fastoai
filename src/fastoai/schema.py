from typing import Generic, Literal, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ListObject(BaseModel, Generic[T]):
    """List container."""

    data: list[T]
    object: Literal["list"] = "list"
    first_id: str | None = None
    last_id: str | None = None
    has_more: bool = False
