from datetime import datetime
from typing import TYPE_CHECKING, Annotated

from openai.types.beta.assistant import Assistant as _Assistant
from openai.types.beta.assistant import ToolResources
from openai.types.beta.assistant_response_format_option import (
    AssistantResponseFormatOption,
)
from openai.types.beta.assistant_tool import AssistantTool
from pydantic import field_serializer
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlmodel import Field, Relationship

from .._metadata import WithMetadata
from .._types import as_sa_type
from .._utils import now, random_id_with_prefix

if TYPE_CHECKING:
    from .message import Message
    from .run import Run
    from .run_step import RunStep

class Assistant(AsyncAttrs, WithMetadata, table=True):
    id: Annotated[str, Field(primary_key=True, default_factory=random_id_with_prefix('asst_'))]
    created_at: Annotated[datetime, Field(default_factory=now)]
    description: str | None = None
    instructions: str | None = None
    model: str
    name: str | None = None
    tools: Annotated[list[AssistantTool], Field(default_factory=list, sa_type=as_sa_type(list[AssistantTool]))]
    response_format: Annotated[AssistantResponseFormatOption | None, Field(sa_type=as_sa_type(AssistantResponseFormatOption), nullable=True)] = None
    temperature: float | None = None
    tool_resources: Annotated[ToolResources | None, Field(sa_type=as_sa_type(ToolResources), nullable=True)] = None
    top_p: float | None = None

    async def to_openai_model(self) -> _Assistant:
        value = self.model_dump(by_alias=True)
        value['object'] = 'assistant'
        return _Assistant.model_validate(value)

    @field_serializer('created_at')
    def serialize_datetime(self, dt: datetime) -> int:
        return int(dt.timestamp())
    messages: list['Message'] = Relationship(back_populates='assistant')
    runs: list['Run'] = Relationship(back_populates='assistant')
    steps: list['RunStep'] = Relationship(back_populates='assistant')