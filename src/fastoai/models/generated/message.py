# Generated by FastOAI, DON'T EDIT
from datetime import datetime
from typing import Annotated, List, Literal, Optional

from openai._models import BaseModel
from openai.types.beta.threads.message import Attachment, IncompleteDetails
from openai.types.beta.threads.message_content import MessageContent
from pydantic import field_serializer
from sqlmodel import Enum, Field, SQLModel

from .._types import as_sa_type


class MessageBase(BaseModel):
    assistant_id: Optional[str] = None
    """
    If applicable, the ID of the
    [assistant](https://platform.openai.com/docs/api-reference/assistants) that
    authored this message.
    """

    attachments: Annotated[Optional[List[Attachment]], Field(sa_type=as_sa_type(List[Attachment]), nullable=True)] = None
    """A list of files attached to the message, and the tools they were added to."""

    completed_at: Optional[datetime] = None
    """The Unix timestamp (in seconds) for when the message was completed."""

    content: Annotated[List[MessageContent], Field(sa_type=as_sa_type(List[MessageContent]))]
    """The content of the message in array of text and/or images."""

    created_at: datetime
    """The Unix timestamp (in seconds) for when the message was created."""

    incomplete_at: Optional[datetime] = None
    """The Unix timestamp (in seconds) for when the message was marked as incomplete."""

    incomplete_details: Annotated[Optional[IncompleteDetails], Field(sa_type=as_sa_type(IncompleteDetails), nullable=True)] = None
    """On an incomplete message, details about why the message is incomplete."""

    role: Annotated[Literal["user", "assistant"], Field(sa_type=Enum("user", "assistant"))]
    """The entity that produced the message. One of `user` or `assistant`."""
    run_id: Optional[str] = None
    """
    The ID of the [run](https://platform.openai.com/docs/api-reference/runs)
    associated with the creation of this message. Value is `null` when messages are
    created manually using the create message or create thread endpoints.
    """

    status: Annotated[Literal["in_progress", "incomplete", "completed"], Field(sa_type=Enum("in_progress", "incomplete", "completed"))]
    """
    The status of the message, which can be either `in_progress`, `incomplete`, or
    `completed`.
    """
    thread_id: str
    """
    The [thread](https://platform.openai.com/docs/api-reference/threads) ID that
    this message belongs to.
    """


class Message(MessageBase, SQLModel, table=True):
    id: Annotated[str, Field(primary_key=True)]
    """The identifier, which can be referenced in API endpoints."""


class MessagePublic(MessageBase):
    id: str
    """The identifier, which can be referenced in API endpoints."""

    metadata: Optional[object] = None
    """Set of 16 key-value pairs that can be attached to an object.

    This can be useful for storing additional information about the object in a
    structured format. Keys can be a maximum of 64 characters long and values can be
    a maximum of 512 characters long.
    """

    object: Literal["thread.message"]
    """The object type, which is always `thread.message`."""

    @field_serializer("completed_at", "created_at", "incomplete_at")
    def serialize_datetime(self, dt: Optional[datetime], _):
        if dt is None:
            return None
        return int(dt.timestamp())
