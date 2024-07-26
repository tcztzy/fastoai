from datetime import datetime
from typing import TYPE_CHECKING

from openai.types.beta.threads.message import Message as OpenAIMessage
from sqlmodel import JSON, Column, Field, Relationship, SQLModel

from ._utils import now, random_id_with_prefix
from .assistant import Assistant
from .run import Run

if TYPE_CHECKING:
    from .thread import Thread


class Message(SQLModel, table=True):
    id: str = Field(primary_key=True, default_factory=random_id_with_prefix("msg_"))
    created_at: datetime = Field(default_factory=now)
    thread_id: str = Field(foreign_key="thread.id", primary_key=True)
    thread: "Thread" = Relationship(back_populates="messages")
    assistant_id: str | None = Field(None, foreign_key="assistant.id")
    assistant: Assistant | None = Relationship(back_populates="messages")
    run_id: str | None = Field(None, foreign_key="run.id")
    run: Run | None = Relationship(back_populates="message")
    data: OpenAIMessage = Field(sa_column=Column(JSON))

    def model_post_init(self, __context):
        self.data.id = self.id
        self.data.created_at = int(self.created_at.timestamp())
