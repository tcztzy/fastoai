from typing import Literal, Protocol

from openai import BaseModel

type Order = Literal["asc", "desc"]


class ToOpenaiModel(Protocol):
    async def to_openai_model(self) -> BaseModel: ...
