from datetime import datetime
from typing import TYPE_CHECKING, Annotated

from openai.types.beta.assistant_response_format_option import (
    AssistantResponseFormatOption,
)
from openai.types.beta.assistant_tool import AssistantTool
from openai.types.beta.assistant_tool_choice_option import AssistantToolChoiceOption
from openai.types.beta.threads.run import (
    IncompleteDetails,
    LastError,
    RequiredAction,
    TruncationStrategy,
    Usage,
)
from openai.types.beta.threads.run import Run as _Run
from openai.types.beta.threads.run_status import RunStatus
from pydantic import field_serializer
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlmodel import Field, Relationship

from .._metadata import WithMetadata
from .._types import as_sa_type
from .._utils import now, random_id_with_prefix
from .assistant import Assistant
from .thread import Thread

if TYPE_CHECKING:
    from .message import Message
    from .run_step import RunStep

class Run(AsyncAttrs, WithMetadata, table=True):
    id: Annotated[str, Field(primary_key=True, default_factory=random_id_with_prefix('run_'))]
    assistant_id: Annotated[str, Field(foreign_key='assistant.id')]
    cancelled_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: Annotated[datetime, Field(default_factory=now)]
    expires_at: datetime | None = None
    failed_at: datetime | None = None
    incomplete_details: Annotated[IncompleteDetails | None, Field(sa_type=as_sa_type(IncompleteDetails), nullable=True)] = None
    instructions: str
    last_error: Annotated[LastError | None, Field(sa_type=as_sa_type(LastError), nullable=True)] = None
    max_completion_tokens: int | None = None
    max_prompt_tokens: int | None = None
    model: str
    parallel_tool_calls: bool
    required_action: Annotated[RequiredAction | None, Field(sa_type=as_sa_type(RequiredAction), nullable=True)] = None
    response_format: Annotated[AssistantResponseFormatOption | None, Field(sa_type=as_sa_type(AssistantResponseFormatOption), nullable=True)] = None
    started_at: datetime | None = None
    status: Annotated[RunStatus, Field(sa_type=as_sa_type(RunStatus))]
    thread_id: Annotated[str, Field(foreign_key='thread.id')]
    tool_choice: Annotated[AssistantToolChoiceOption | None, Field(sa_type=as_sa_type(AssistantToolChoiceOption), nullable=True)] = None
    tools: Annotated[list[AssistantTool], Field(default_factory=list, sa_type=as_sa_type(list[AssistantTool]))]
    truncation_strategy: Annotated[TruncationStrategy | None, Field(sa_type=as_sa_type(TruncationStrategy), nullable=True)] = None
    usage: Annotated[Usage | None, Field(sa_type=as_sa_type(Usage), nullable=True)] = None
    temperature: float | None = None
    top_p: float | None = None

    async def to_openai_model(self) -> _Run:
        value = self.model_dump(by_alias=True)
        value['object'] = 'thread.run'
        return _Run.model_validate(value)

    @field_serializer('cancelled_at', 'completed_at', 'created_at', 'expires_at', 'failed_at', 'started_at')
    def serialize_datetime(self, dt: datetime | None) -> int | None:
        if dt is None:
            return None
        return int(dt.timestamp())
    assistant: Assistant = Relationship(back_populates='runs')
    thread: Thread = Relationship(back_populates='runs')
    messages: list['Message'] = Relationship(back_populates='run')
    steps: list['RunStep'] = Relationship(back_populates='run')