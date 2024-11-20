# Generated by FastOAI, DON'T EDIT
from typing import Annotated, List, Literal, Optional

from openai._models import BaseModel
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
from openai.types.beta.threads.run_status import RunStatus
from sqlmodel import Field, SQLModel

from .._types import as_sa_type


class RunBase(BaseModel):
    assistant_id: str
    """
    The ID of the
    [assistant](https://platform.openai.com/docs/api-reference/assistants) used for
    execution of this run.
    """

    cancelled_at: Optional[int] = None
    """The Unix timestamp (in seconds) for when the run was cancelled."""

    completed_at: Optional[int] = None
    """The Unix timestamp (in seconds) for when the run was completed."""

    created_at: int
    """The Unix timestamp (in seconds) for when the run was created."""

    expires_at: Optional[int] = None
    """The Unix timestamp (in seconds) for when the run will expire."""

    failed_at: Optional[int] = None
    """The Unix timestamp (in seconds) for when the run failed."""

    incomplete_details: Annotated[Optional[IncompleteDetails], Field(sa_type=as_sa_type(IncompleteDetails), nullable=True)] = None
    """Details on why the run is incomplete.

    Will be `null` if the run is not incomplete.
    """

    instructions: str
    """
    The instructions that the
    [assistant](https://platform.openai.com/docs/api-reference/assistants) used for
    this run.
    """

    last_error: Annotated[Optional[LastError], Field(sa_type=as_sa_type(LastError), nullable=True)] = None
    """The last error associated with this run. Will be `null` if there are no errors."""

    max_completion_tokens: Optional[int] = None
    """
    The maximum number of completion tokens specified to have been used over the
    course of the run.
    """

    max_prompt_tokens: Optional[int] = None
    """
    The maximum number of prompt tokens specified to have been used over the course
    of the run.
    """

    model: str
    """
    The model that the
    [assistant](https://platform.openai.com/docs/api-reference/assistants) used for
    this run.
    """

    parallel_tool_calls: bool
    """
    Whether to enable
    [parallel function calling](https://platform.openai.com/docs/guides/function-calling#configuring-parallel-function-calling)
    during tool use.
    """

    required_action: Annotated[Optional[RequiredAction], Field(sa_type=as_sa_type(RequiredAction), nullable=True)] = None
    """Details on the action required to continue the run.

    Will be `null` if no action is required.
    """

    response_format: Annotated[Optional[AssistantResponseFormatOption], Field(sa_type=as_sa_type(AssistantResponseFormatOption), nullable=True)] = None
    """Specifies the format that the model must output.

    Compatible with [GPT-4o](https://platform.openai.com/docs/models#gpt-4o),
    [GPT-4 Turbo](https://platform.openai.com/docs/models#gpt-4-turbo-and-gpt-4),
    and all GPT-3.5 Turbo models since `gpt-3.5-turbo-1106`.

    Setting to `{ "type": "json_schema", "json_schema": {...} }` enables Structured
    Outputs which ensures the model will match your supplied JSON schema. Learn more
    in the
    [Structured Outputs guide](https://platform.openai.com/docs/guides/structured-outputs).

    Setting to `{ "type": "json_object" }` enables JSON mode, which ensures the
    message the model generates is valid JSON.

    **Important:** when using JSON mode, you **must** also instruct the model to
    produce JSON yourself via a system or user message. Without this, the model may
    generate an unending stream of whitespace until the generation reaches the token
    limit, resulting in a long-running and seemingly "stuck" request. Also note that
    the message content may be partially cut off if `finish_reason="length"`, which
    indicates the generation exceeded `max_tokens` or the conversation exceeded the
    max context length.
    """

    started_at: Optional[int] = None
    """The Unix timestamp (in seconds) for when the run was started."""

    status: Annotated[RunStatus, Field(sa_type=as_sa_type(RunStatus))]
    """
    The status of the run, which can be either `queued`, `in_progress`,
    `requires_action`, `cancelling`, `cancelled`, `failed`, `completed`,
    `incomplete`, or `expired`.
    """

    thread_id: str
    """
    The ID of the [thread](https://platform.openai.com/docs/api-reference/threads)
    that was executed on as a part of this run.
    """

    tool_choice: Annotated[Optional[AssistantToolChoiceOption], Field(sa_type=as_sa_type(AssistantToolChoiceOption), nullable=True)] = None
    """
    Controls which (if any) tool is called by the model. `none` means the model will
    not call any tools and instead generates a message. `auto` is the default value
    and means the model can pick between generating a message or calling one or more
    tools. `required` means the model must call one or more tools before responding
    to the user. Specifying a particular tool like `{"type": "file_search"}` or
    `{"type": "function", "function": {"name": "my_function"}}` forces the model to
    call that tool.
    """

    tools: Annotated[List[AssistantTool], Field(sa_type=as_sa_type(List[AssistantTool]))]
    """
    The list of tools that the
    [assistant](https://platform.openai.com/docs/api-reference/assistants) used for
    this run.
    """

    truncation_strategy: Annotated[Optional[TruncationStrategy], Field(sa_type=as_sa_type(TruncationStrategy), nullable=True)] = None
    """Controls for how a thread will be truncated prior to the run.

    Use this to control the intial context window of the run.
    """

    usage: Annotated[Optional[Usage], Field(sa_type=as_sa_type(Usage), nullable=True)] = None
    """Usage statistics related to the run.

    This value will be `null` if the run is not in a terminal state (i.e.
    `in_progress`, `queued`, etc.).
    """

    temperature: Optional[float] = None
    """The sampling temperature used for this run. If not set, defaults to 1."""

    top_p: Optional[float] = None
    """The nucleus sampling value used for this run. If not set, defaults to 1."""


class Run(RunBase, SQLModel, table=True):
    id: Annotated[str, Field(primary_key=True)]
    """The identifier, which can be referenced in API endpoints."""


class RunPublic(RunBase):
    id: str
    """The identifier, which can be referenced in API endpoints."""
    metadata: Optional[object] = None
    """Set of 16 key-value pairs that can be attached to an object.

    This can be useful for storing additional information about the object in a
    structured format. Keys can be a maximum of 64 characters long and values can be
    a maximum of 512 characters long.
    """
    object: Literal["thread.run"]
    """The object type, which is always `thread.run`."""