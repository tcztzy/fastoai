# Generated by FastOAI, DON'T EDIT
from typing import Annotated, Literal, Optional

from openai._models import BaseModel
from sqlmodel import Enum, Field, SQLModel


class FileObjectBase(BaseModel):
    bytes: int
    """The size of the file, in bytes."""

    created_at: int
    """The Unix timestamp (in seconds) for when the file was created."""

    filename: str
    """The name of the file."""

    purpose: Annotated[Literal[
        "assistants", "assistants_output", "batch", "batch_output", "fine-tune", "fine-tune-results", "vision"
    ], Field(sa_type=Enum("assistants", "assistants_output", "batch", "batch_output", "fine-tune", "fine-tune-results", "vision"))]
    """The intended purpose of the file.

    Supported values are `assistants`, `assistants_output`, `batch`, `batch_output`,
    `fine-tune`, `fine-tune-results` and `vision`.
    """
    status: Annotated[Literal["uploaded", "processed", "error"], Field(sa_type=Enum("uploaded", "processed", "error"))]
    """Deprecated.

    The current status of the file, which can be either `uploaded`, `processed`, or
    `error`.
    """
    status_details: Optional[str] = None
    """Deprecated.

    For details on why a fine-tuning training file failed validation, see the
    `error` field on `fine_tuning.job`.
    """


class FileObject(FileObjectBase, SQLModel, table=True):
    id: Annotated[str, Field(primary_key=True)]
    """The file identifier, which can be referenced in the API endpoints."""


class FileObjectPublic(FileObjectBase):
    id: str
    """The file identifier, which can be referenced in the API endpoints."""
    object: Literal["file"]
    """The object type, which is always `file`."""