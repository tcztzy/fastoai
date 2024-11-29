# Generated by FastOAI, DON'T EDIT
from datetime import datetime
from typing import TYPE_CHECKING, Annotated

from openai.types.beta.thread import Thread as _Thread
from openai.types.beta.thread import ToolResources
from pydantic import field_serializer
from sqlmodel import Field, Relationship

from .._metadata import WithMetadata
from .._types import as_sa_type
from .._utils import now, random_id_with_prefix

if TYPE_CHECKING:
    from .message import Message
    from .run import Run
    from .run_step import Step


class Thread(WithMetadata, table=True):
    id: Annotated[str, Field(primary_key=True, default_factory=random_id_with_prefix("thread_"))]
    """The identifier, which can be referenced in API endpoints."""

    created_at: Annotated[datetime, Field(default_factory=now)]
    """The Unix timestamp (in seconds) for when the thread was created."""

    tool_resources: Annotated[ToolResources | None, Field(sa_type=as_sa_type(ToolResources), nullable=True)] = None
    """
    A set of resources that are made available to the assistant's tools in this
    thread. The resources are specific to the type of tool. For example, the
    `code_interpreter` tool requires a list of file IDs, while the `file_search`
    tool requires a list of vector store IDs.
    """

    @field_serializer("created_at")
    def serialize_datetime(self, dt: datetime, _) -> int:
        return int(dt.timestamp())

    messages: list["Message"] = Relationship(back_populates="thread")
    runs: list["Run"] = Relationship(back_populates="thread")
    steps: list["Step"] = Relationship(back_populates="thread")

    def to_openai_model(self) -> _Thread:
        value = self.model_dump()
        value["object"] = "thread"
        return _Thread.model_validate(value)
