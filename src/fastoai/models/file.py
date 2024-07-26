from datetime import datetime
from typing import Literal, get_args

from pydantic import computed_field, field_serializer
from sqlalchemy import Enum as sa_Enum
from sqlmodel import Field, SQLModel

from ._utils import now, random_id_with_prefix

FilePurpose = Literal[
    "assistants",
    "assistants_output",
    "batch",
    "batch_output",
    "fine-tune",
    "fine-tune-results",
    "vision",
]

FilePurposeEnum = sa_Enum(*get_args(FilePurpose))

FileStatus = Literal["uploaded", "processed", "error"]

FileStatusEnum = sa_Enum(*get_args(FileStatus))


class File(SQLModel, table=True):
    id: str = Field(primary_key=True, default_factory=random_id_with_prefix("file-"))
    bytes: int
    created_at: datetime = Field(default_factory=now)
    filename: str
    purpose: FilePurpose = Field(sa_type=FilePurposeEnum)  # type: ignore[call-overload]
    status: FileStatus = Field(
        "uploaded", sa_type=FileStatusEnum, schema_extra={"deprecated": True}
    )  # type: ignore[call-overload]
    status_details: str | None = Field(default=None, schema_extra={"deprecated": True})

    @computed_field
    def object(self) -> str:
        return "file"

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> int:
        return int(value.timestamp())
