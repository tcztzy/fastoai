from datetime import datetime
from typing import Annotated, Literal

from openai.types.file_object import FileObject as _FileObject
from pydantic import field_serializer
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlmodel import Enum, Field, SQLModel

from .._utils import now, random_id_with_prefix


class FileObject(AsyncAttrs, SQLModel, table=True):
    __tablename__ = 'file'
    id: Annotated[str, Field(primary_key=True, default_factory=random_id_with_prefix('file-'))]
    bytes: int
    created_at: Annotated[datetime, Field(default_factory=now)]
    filename: str
    purpose: Annotated[Literal['assistants', 'assistants_output', 'batch', 'batch_output', 'fine-tune', 'fine-tune-results', 'vision'], Field(sa_type=Enum('assistants', 'assistants_output', 'batch', 'batch_output', 'fine-tune', 'fine-tune-results', 'vision'))]
    status: Annotated[Literal['uploaded', 'processed', 'error'], Field(sa_type=Enum('uploaded', 'processed', 'error'))]
    status_details: str | None = None

    async def to_openai_model(self) -> _FileObject:
        value = self.model_dump(by_alias=True)
        value['object'] = 'file'
        return _FileObject.model_validate(value)

    @field_serializer('created_at')
    def serialize_datetime(self, dt: datetime) -> int:
        return int(dt.timestamp())