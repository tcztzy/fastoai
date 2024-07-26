from datetime import datetime

from openai.types.beta.thread import Thread as OpenAIThread
from sqlmodel import JSON, Column, Field, Relationship, SQLModel

from ._utils import now, random_id_with_prefix
from .assistant import Assistant
from .message import Message
from .run import Run


class Thread(SQLModel, table=True):
    """Thread model."""

    id: str = Field(primary_key=True, default_factory=random_id_with_prefix("thread_"))
    created_at: datetime = Field(default_factory=now)
    data: OpenAIThread = Field(sa_column=Column(JSON))
    messages: list[Message] = Relationship(back_populates="thread")
    assistants: list[Assistant] = Relationship(back_populates="threads", link_model=Run)

    def model_post_init(self, __context):
        self.data.id = self.id
        self.data.created_at = int(self.created_at.timestamp())
