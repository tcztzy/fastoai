from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from openai.types.beta.threads.runs.run_step import RunStep as OpenAIRunStep
from sqlmodel import JSON, Column, Field, Relationship, SQLModel

from ._utils import now, random_id_with_prefix

if TYPE_CHECKING:
    from .run import Run


class RunStepStatus(Enum):
    in_progress = "in_progress"
    cancelled = "cancelled"
    failed = "failed"
    completed = "completed"
    expired = "expired"


class RunStep(SQLModel, table=True):
    __tablename__ = "step"

    id: str = Field(primary_key=True, default_factory=random_id_with_prefix("step_"))
    created_at: datetime = Field(default_factory=now)
    run_id: str = Field(foreign_key="run.id")
    run: "Run" = Relationship(back_populates="steps")
    assistant_id: str | None = Field(default=None, foreign_key="assistant.id")
    thread_id: str | None = Field(default=None, foreign_key="thread.id")
    status: RunStepStatus = RunStepStatus.in_progress
    data: OpenAIRunStep = Field(sa_column=Column(JSON))

    def model_post_init(self, __context):
        self.data.id = self.id
        self.data.created_at = int(self.created_at.timestamp())

    def __setattr__(self, name: str, value: Any):
        super().__setattr__(name, value)
        if name == "status":
            self.data.status = RunStepStatus(value).value
