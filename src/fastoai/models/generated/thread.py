from datetime import datetime
from typing import TYPE_CHECKING, Annotated

from openai.types.beta.thread import Thread as _Thread
from openai.types.beta.thread import ToolResources
from pydantic import field_serializer
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlmodel import Field, Relationship

from .._metadata import WithMetadata
from .._types import as_sa_type
from .._utils import now, random_id_with_prefix

if TYPE_CHECKING:
    from .message import Message
    from .run import Run
    from .run_step import RunStep

class Thread(AsyncAttrs, WithMetadata, table=True):
    id: Annotated[str, Field(primary_key=True, default_factory=random_id_with_prefix('thread_'))]
    created_at: Annotated[datetime, Field(default_factory=now)]
    tool_resources: Annotated[ToolResources | None, Field(sa_type=as_sa_type(ToolResources), nullable=True)] = None

    async def to_openai_model(self) -> _Thread:
        value = self.model_dump(by_alias=True)
        value['object'] = 'thread'
        return _Thread.model_validate(value)

    @field_serializer('created_at')
    def serialize_datetime(self, dt: datetime) -> int:
        return int(dt.timestamp())
    messages: list['Message'] = Relationship(back_populates='thread')
    runs: list['Run'] = Relationship(back_populates='thread')
    steps: list['RunStep'] = Relationship(back_populates='thread')