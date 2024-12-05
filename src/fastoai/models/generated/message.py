from datetime import datetime
from typing import Annotated, Literal

from openai.types.beta.threads.message import (
    Attachment,
    IncompleteDetails,
)
from openai.types.beta.threads.message import Message as _Message
from openai.types.beta.threads.message_content import MessageContent
from pydantic import field_serializer
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlmodel import Enum, Field, Relationship

from .._metadata import WithMetadata
from .._types import as_sa_type
from .._utils import now, random_id_with_prefix
from .assistant import Assistant
from .run import Run
from .thread import Thread


class Message(AsyncAttrs, WithMetadata, table=True):
    id: Annotated[str, Field(primary_key=True, default_factory=random_id_with_prefix('msg_'))]
    assistant_id: Annotated[str | None, Field(foreign_key='assistant.id', nullable=True)] = None
    attachments: Annotated[list[Attachment] | None, Field(sa_type=as_sa_type(list[Attachment]), nullable=True)] = None
    completed_at: datetime | None = None
    content: Annotated[list[MessageContent], Field(default_factory=list, sa_type=as_sa_type(list[MessageContent]))]
    created_at: Annotated[datetime, Field(default_factory=now)]
    incomplete_at: datetime | None = None
    incomplete_details: Annotated[IncompleteDetails | None, Field(sa_type=as_sa_type(IncompleteDetails), nullable=True)] = None
    role: Annotated[Literal['user', 'assistant'], Field(sa_type=Enum('user', 'assistant'))]
    run_id: Annotated[str | None, Field(foreign_key='run.id', nullable=True)] = None
    status: Annotated[Literal['in_progress', 'incomplete', 'completed'], Field(sa_type=Enum('in_progress', 'incomplete', 'completed'))]
    thread_id: Annotated[str, Field(foreign_key='thread.id')]

    async def to_openai_model(self) -> _Message:
        value = self.model_dump(by_alias=True)
        value['object'] = 'thread.message'
        return _Message.model_validate(value)

    @field_serializer('completed_at', 'created_at', 'incomplete_at')
    def serialize_datetime(self, dt: datetime | None) -> int | None:
        if dt is None:
            return None
        return int(dt.timestamp())
    assistant: Assistant | None = Relationship(back_populates='messages')
    run: Run | None = Relationship(back_populates='messages')
    thread: Thread = Relationship(back_populates='messages')