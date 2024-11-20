# Generated by FastOAI, DON'T EDIT
from datetime import datetime
from typing import Annotated, Literal, Optional

from openai._models import BaseModel
from openai.types.beta.threads.runs.run_step import LastError, StepDetails, Usage
from pydantic import field_serializer
from sqlmodel import Enum, Field, SQLModel

from .._types import as_sa_type


class RunStepBase(BaseModel):
    assistant_id: str
    """
    The ID of the
    [assistant](https://platform.openai.com/docs/api-reference/assistants)
    associated with the run step.
    """

    cancelled_at: Optional[datetime] = None
    """The Unix timestamp (in seconds) for when the run step was cancelled."""

    completed_at: Optional[datetime] = None
    """The Unix timestamp (in seconds) for when the run step completed."""

    created_at: datetime
    """The Unix timestamp (in seconds) for when the run step was created."""

    expired_at: Optional[datetime] = None
    """The Unix timestamp (in seconds) for when the run step expired.

    A step is considered expired if the parent run is expired.
    """

    failed_at: Optional[datetime] = None
    """The Unix timestamp (in seconds) for when the run step failed."""

    last_error: Annotated[Optional[LastError], Field(sa_type=as_sa_type(LastError), nullable=True)] = None
    """The last error associated with this run step.

    Will be `null` if there are no errors.
    """

    run_id: str
    """
    The ID of the [run](https://platform.openai.com/docs/api-reference/runs) that
    this run step is a part of.
    """

    status: Annotated[Literal["in_progress", "cancelled", "failed", "completed", "expired"], Field(sa_type=Enum("in_progress", "cancelled", "failed", "completed", "expired"))]
    """
    The status of the run step, which can be either `in_progress`, `cancelled`,
    `failed`, `completed`, or `expired`.
    """
    step_details: Annotated[StepDetails, Field(sa_type=as_sa_type(StepDetails))]
    """The details of the run step."""

    thread_id: str
    """
    The ID of the [thread](https://platform.openai.com/docs/api-reference/threads)
    that was run.
    """

    type: Annotated[Literal["message_creation", "tool_calls"], Field(sa_type=Enum("message_creation", "tool_calls"))]
    """The type of run step, which can be either `message_creation` or `tool_calls`."""
    usage: Annotated[Optional[Usage], Field(sa_type=as_sa_type(Usage), nullable=True)] = None
    """Usage statistics related to the run step.

    This value will be `null` while the run step's status is `in_progress`.
    """


class RunStep(RunStepBase, SQLModel, table=True):
    id: Annotated[str, Field(primary_key=True)]
    """The identifier of the run step, which can be referenced in API endpoints."""


class RunStepPublic(RunStepBase):
    id: str
    """The identifier of the run step, which can be referenced in API endpoints."""

    metadata: Optional[object] = None
    """Set of 16 key-value pairs that can be attached to an object.

    This can be useful for storing additional information about the object in a
    structured format. Keys can be a maximum of 64 characters long and values can be
    a maximum of 512 characters long.
    """

    object: Literal["thread.run.step"]
    """The object type, which is always `thread.run.step`."""

    @field_serializer("cancelled_at", "completed_at", "created_at", "expired_at", "failed_at")
    def serialize_datetime(self, dt: Optional[datetime], _):
        if dt is None:
            return None
        return int(dt.timestamp())
