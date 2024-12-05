from datetime import datetime
from typing import Annotated, Literal

from openai.types.beta.threads.runs.run_step import LastError, StepDetails, Usage
from openai.types.beta.threads.runs.run_step import RunStep as _RunStep
from pydantic import field_serializer
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlmodel import Enum, Field, Relationship

from .._metadata import WithMetadata
from .._types import as_sa_type
from .._utils import now, random_id_with_prefix
from .assistant import Assistant
from .run import Run
from .thread import Thread


class RunStep(AsyncAttrs, WithMetadata, table=True):
    __tablename__ = 'step'
    id: Annotated[str, Field(primary_key=True, default_factory=random_id_with_prefix('step_'))]
    assistant_id: Annotated[str, Field(foreign_key='assistant.id')]
    cancelled_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: Annotated[datetime, Field(default_factory=now)]
    expired_at: datetime | None = None
    failed_at: datetime | None = None
    last_error: Annotated[LastError | None, Field(sa_type=as_sa_type(LastError), nullable=True)] = None
    run_id: Annotated[str, Field(foreign_key='run.id')]
    status: Annotated[Literal['in_progress', 'cancelled', 'failed', 'completed', 'expired'], Field(sa_type=Enum('in_progress', 'cancelled', 'failed', 'completed', 'expired'))]
    step_details: Annotated[StepDetails, Field(sa_type=as_sa_type(StepDetails))]
    thread_id: Annotated[str, Field(foreign_key='thread.id')]
    type: Annotated[Literal['message_creation', 'tool_calls'], Field(sa_type=Enum('message_creation', 'tool_calls'))]
    usage: Annotated[Usage | None, Field(sa_type=as_sa_type(Usage), nullable=True)] = None

    async def to_openai_model(self) -> _RunStep:
        value = self.model_dump(by_alias=True)
        value['object'] = 'thread.run.step'
        return _RunStep.model_validate(value)

    @field_serializer('cancelled_at', 'completed_at', 'created_at', 'expired_at', 'failed_at')
    def serialize_datetime(self, dt: datetime | None) -> int | None:
        if dt is None:
            return None
        return int(dt.timestamp())
    assistant: Assistant = Relationship(back_populates='steps')
    run: Run = Relationship(back_populates='steps')
    thread: Thread = Relationship(back_populates='steps')