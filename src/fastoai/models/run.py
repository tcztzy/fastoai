from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from openai.types.beta.threads.run import Run as OpenAIRun
from sqlmodel import JSON, Field, Relationship, SQLModel

from ._utils import now, random_id_with_prefix
from .step import RunStep

if TYPE_CHECKING:
    from .thread import Message


class RunStatus(Enum):
    queued = "queued"
    in_progress = "in_progress"
    requires_action = "requires_action"
    cancelling = "cancelling"
    cancelled = "cancelled"
    failed = "failed"
    completed = "completed"
    incomplete = "incomplete"
    expired = "expired"


class Run(SQLModel, table=True):
    id: str = Field(primary_key=True, default_factory=random_id_with_prefix("run_"))
    created_at: datetime = Field(default_factory=now)
    assistant_id: str = Field(foreign_key="assistant.id", primary_key=True)
    thread_id: str = Field(foreign_key="thread.id", primary_key=True)
    status: RunStatus = RunStatus.queued
    message: "Message" = Relationship(
        sa_relationship_kwargs={"uselist": False}, back_populates="run"
    )
    steps: list[RunStep] = Relationship(back_populates="run")
    data: OpenAIRun = Field(sa_type=JSON)

    def model_post_init(self, __context):
        self.data.id = self.id
        self.data.created_at = int(self.created_at.timestamp())

    def __setattr__(self, name: str, value: Any):
        super().__setattr__(name, value)
        if name == "status":
            self.data.status = RunStatus(value).value
