from typing import Generic, Literal, TypeVar, cast

from openai.pagination import AsyncCursorPage, CursorPageItem
from pydantic import computed_field

_T = TypeVar("_T")


class AsyncCursorPage(AsyncCursorPage[_T], Generic[_T]):
    object: Literal["list"] = "list"

    @computed_field
    def has_more(self) -> bool:
        return self.has_next_page()

    @computed_field
    def first_id(self) -> str | None:
        if not self.data:
            return None
        return cast(CursorPageItem, self.data[0]).id

    @computed_field
    def last_id(self) -> str | None:
        if not self.data:
            return None
        return cast(CursorPageItem, self.data[-1]).id
