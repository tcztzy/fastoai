from datetime import datetime
from enum import Enum

from pydantic import computed_field, field_serializer
from sqlmodel import Field, SQLModel

from ._utils import now, random_id_with_prefix


class FilePurpose(Enum):
    assistants = "assistants"
    assistants_output = "assistants_output"
    batch = "batch"
    batch_output = "batch_output"
    fine_tune = "fine-tune"
    fine_tune_results = "fine-tune-results"
    vision = "vision"


class FileStatus(Enum):
    uploaded = "uploaded"
    processed = "processed"
    error = "error"


class File(SQLModel, table=True):
    id: str = Field(primary_key=True, default_factory=random_id_with_prefix("file-"))
    bytes: int
    created_at: datetime = Field(default_factory=now)
    filename: str
    purpose: FilePurpose
    status: FileStatus = Field(FileStatus.uploaded, schema_extra={"deprecated": True})
    status_details: str | None = Field(default=None, schema_extra={"deprecated": True})

    @computed_field
    def object(self) -> str:
        return "file"

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> int:
        return int(value.timestamp())
