from typing import Literal, Protocol, TypeAlias

from openai import BaseModel

Order: TypeAlias = Literal["asc", "desc"]


class ToOpenaiModel(Protocol):
    async def to_openai_model(self) -> BaseModel: ...
