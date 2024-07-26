from datetime import datetime
from typing import TYPE_CHECKING

from openai.types.beta.assistant import Assistant as OpenAIAssistant
from sqlmodel import JSON, Column, Field, Relationship, SQLModel

from ._utils import now, random_id_with_prefix
from .run import Run

if TYPE_CHECKING:
    from .message import Message
    from .thread import Thread


class Assistant(SQLModel, table=True):
    """Assistant model."""

    id: str = Field(primary_key=True, default_factory=random_id_with_prefix("asst_"))
    created_at: datetime = Field(default_factory=now)
    data: OpenAIAssistant = Field(sa_column=Column(JSON))
    messages: list["Message"] = Relationship(back_populates="assistant")
    threads: list["Thread"] = Relationship(back_populates="assistants", link_model=Run)

    def model_post_init(self, __context):
        self.data.id = self.id
        self.data.created_at = int(self.created_at.timestamp())
