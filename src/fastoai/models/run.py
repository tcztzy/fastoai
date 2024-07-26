from datetime import datetime
from typing import TYPE_CHECKING

from openai.types.beta.threads.run import Run as OpenAIRun
from sqlmodel import JSON, Column, Field, Relationship, SQLModel

from ._utils import now, random_id_with_prefix
from .step import RunStep
from .user import User

if TYPE_CHECKING:
    from .thread import Message


class Run(SQLModel, table=True):
    id: str = Field(primary_key=True, default_factory=random_id_with_prefix("run_"))
    created_at: datetime = Field(default_factory=now)
    assistant_id: str = Field(foreign_key="assistant.id", primary_key=True)
    thread_id: str = Field(foreign_key="thread.id", primary_key=True)
    message: "Message" = Relationship(
        sa_relationship_kwargs={"uselist": False}, back_populates="run"
    )
    steps: list[RunStep] = Relationship(back_populates="run")
    data: OpenAIRun = Field(sa_column=Column(JSON))
    user_id: str = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="runs")

    def model_post_init(self, __context):
        self.data.id = self.id
        self.data.created_at = int(self.created_at.timestamp())
