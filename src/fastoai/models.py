# Generated by fastoai, DO NOT EDIT
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Literal, Self

from fastapi import Depends, HTTPException, status
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer
from openai.types.beta.assistant import ToolResources as AssistantToolResources
from openai.types.beta.assistant_response_format_option import (
    AssistantResponseFormatOption,
)
from openai.types.beta.assistant_tool import AssistantTool
from openai.types.beta.assistant_tool_choice_option import AssistantToolChoiceOption
from openai.types.beta.thread import ToolResources as ThreadToolResources
from openai.types.beta.threads.message import Attachment
from openai.types.beta.threads.message import (
    IncompleteDetails as MessageIncompleteDetails,
)
from openai.types.beta.threads.message_content import MessageContent
from openai.types.beta.threads.run import (
    IncompleteDetails as RunIncompleteDetails,
)
from openai.types.beta.threads.run import (
    LastError as RunLastError,
)
from openai.types.beta.threads.run import (
    RequiredAction,
    TruncationStrategy,
    Usage,
)
from openai.types.beta.threads.runs.run_step import LastError as RunStepLastError
from openai.types.beta.threads.runs.run_step import StepDetails
from pydantic import BaseModel, EmailStr, computed_field, field_serializer
from sqlalchemy.exc import NoResultFound
from sqlmodel import JSON, Column, Field, Relationship, SQLModel

from fastoai.settings import settings
from fastoai.utils import now, random_id_with_prefix

security = HTTPBearer()


class MetadataMixin(SQLModel):
    metadata_: dict[str, str] | None = Field(
        None, alias="metadata", sa_type=JSON, sa_column_kwargs={"name": "metadata"}
    )
    """Set of 16 key-value pairs that can be attached to an object.

    This can be useful for storing additional information about the object in a
    structured format. Keys can be a maximum of 64 characters long and values can be
    a maxium of 512 characters long.
    """

    @classmethod
    def model_validate(
        cls,
        obj: Any,
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: dict[str, Any] | None = None,
        update: dict[str, Any] | None = None,
    ) -> Self:
        if "metadata" in obj:
            obj["metadata_"] = obj.pop("metadata")
        return super().model_validate(
            obj,
            strict=strict,
            from_attributes=from_attributes,
            context=context,
            update=update,
        )

    def model_dump(self, **kwargs):
        result = super().model_dump(**kwargs)
        if "metadata_" in result:
            result["metadata"] = result.pop("metadata_")
        return result

    def model_dump_json(self, **kwargs):
        result = super().model_dump_json(**kwargs)
        if "metadata_" in result:
            result.replace("metadata_", "metadata")
        return result

    def __init__(self, **kwargs):
        if "metadata" in kwargs:
            kwargs["metadata_"] = kwargs.pop("metadata")
        return super().__init__(**kwargs)


class Base(SQLModel):
    created_at: datetime = Field(default_factory=now)
    """The Unix timestamp (in seconds) for when the object was created."""

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> int:
        return int(value.timestamp())


class Assistant(Base, MetadataMixin, table=True):
    id: str = Field(default_factory=random_id_with_prefix("asst_"), primary_key=True)
    """The identifier, which can be referenced in API endpoints."""

    description: str | None = None
    """The description of the assistant. The maximum length is 512 characters."""

    instructions: str | None = None
    """The system instructions that the assistant uses.

    The maximum length is 256,000 characters.
    """

    model: str
    """ID of the model to use.

    You can use the
    [List models](https://platform.openai.com/docs/api-reference/models/list) API to
    see all of your available models, or see our
    [Model overview](https://platform.openai.com/docs/models/overview) for
    descriptions of them.
    """

    name: str | None = None
    """The name of the assistant. The maximum length is 256 characters."""

    @computed_field
    def object(self) -> Literal["assistant"]:
        """The object type, which is always `assistant`."""
        return "assistant"

    tools: list[AssistantTool] = Field(default_factory=list, sa_column=Column(JSON))
    """A list of tool enabled on the assistant.

    There can be a maximum of 128 tools per assistant. Tools can be of types
    `code_interpreter`, `file_search`, or `function`.
    """

    response_format: AssistantResponseFormatOption | None = Field(None, sa_type=JSON)
    """Specifies the format that the model must output.

    Compatible with [GPT-4o](https://platform.openai.com/docs/models/gpt-4o),
    [GPT-4 Turbo](https://platform.openai.com/docs/models/gpt-4-turbo-and-gpt-4),
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

    temperature: float | None = None
    """What sampling temperature to use, between 0 and 2.

    Higher values like 0.8 will make the output more random, while lower values like
    0.2 will make it more focused and deterministic.
    """

    tool_resources: AssistantToolResources | None = Field(None, sa_type=JSON)
    """A set of resources that are used by the assistant's tools.

    The resources are specific to the type of tool. For example, the
    `code_interpreter` tool requires a list of file IDs, while the `file_search`
    tool requires a list of vector store IDs.
    """

    top_p: float | None = None
    """
    An alternative to sampling with temperature, called nucleus sampling, where the
    model considers the results of the tokens with top_p probability mass. So 0.1
    means only the tokens comprising the top 10% probability mass are considered.

    We generally recommend altering this or temperature but not both.
    """

    messages: list["Message"] = Relationship(back_populates="assistant")

    runs: list["Run"] = Relationship(back_populates="assistant")


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


class FileObject(Base, table=True):
    __tablename__ = "file"
    id: str = Field(default_factory=random_id_with_prefix("file-"), primary_key=True)
    """The file identifier, which can be referenced in the API endpoints."""

    bytes: int
    """The size of the file, in bytes."""

    filename: str
    """The name of the file."""

    @computed_field
    def object(self) -> Literal["file"]:
        """The object type, which is always `file`."""
        return "file"

    purpose: FilePurpose
    """The intended purpose of the file.

    Supported values are `assistants`, `assistants_output`, `batch`, `batch_output`,
    `fine-tune`, `fine-tune-results` and `vision`.
    """

    status: FileStatus
    """Deprecated.

    The current status of the file, which can be either `uploaded`, `processed`, or
    `error`.
    """

    status_details: str | None = None
    """Deprecated.

    For details on why a fine-tuning training file failed validation, see the
    `error` field on `fine_tuning.job`.
    """


class Thread(Base, MetadataMixin, table=True):
    id: str = Field(default_factory=random_id_with_prefix("thread_"), primary_key=True)
    """The identifier, which can be referenced in API endpoints."""

    @computed_field
    def object(self) -> Literal["thread"]:
        """The object type, which is always `thread`."""
        return "thread"

    tool_resources: ThreadToolResources | None = Field(None, sa_type=JSON)
    """
    A set of resources that are made available to the assistant's tools in this
    thread. The resources are specific to the type of tool. For example, the
    `code_interpreter` tool requires a list of file IDs, while the `file_search`
    tool requires a list of vector store IDs.
    """

    messages: list["Message"] = Relationship(back_populates="thread")

    runs: list["Run"] = Relationship(back_populates="thread")


class RunStatus(Enum):
    queued = "queued"
    in_progress = "in_progress"
    requires_action = "requires_action"
    cancelling = "cancelling"
    cancelled = "cancelled"
    failed = "failed"
    completed = "completed"
    incomplete = "incomplete"
    expired = "expired"


class Run(Base, MetadataMixin, table=True):
    id: str = Field(default_factory=random_id_with_prefix("run_"), primary_key=True)
    """The identifier, which can be referenced in API endpoints."""

    assistant_id: str = Field(foreign_key="assistant.id")
    """
    The ID of the
    [assistant](https://platform.openai.com/docs/api-reference/assistants) used for
    execution of this run.
    """

    cancelled_at: datetime | None = None
    """The Unix timestamp (in seconds) for when the run was cancelled."""

    completed_at: datetime | None = None
    """The Unix timestamp (in seconds) for when the run was completed."""

    expires_at: datetime | None = None
    """The Unix timestamp (in seconds) for when the run will expire."""

    failed_at: datetime | None = None
    """The Unix timestamp (in seconds) for when the run failed."""

    incomplete_details: RunIncompleteDetails | None = Field(None, sa_type=JSON)
    """Details on why the run is incomplete.

    Will be `null` if the run is not incomplete.
    """

    instructions: str
    """
    The instructions that the
    [assistant](https://platform.openai.com/docs/api-reference/assistants) used for
    this run.
    """

    last_error: RunLastError | None = Field(None, sa_type=JSON)
    """The last error associated with this run. Will be `null` if there are no errors."""

    max_completion_tokens: int | None = None
    """
    The maximum number of completion tokens specified to have been used over the
    course of the run.
    """

    max_prompt_tokens: int | None = None
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

    @computed_field
    def object(self) -> Literal["thread.run"]:
        """The object type, which is always `thread.run`."""
        return "thread.run"

    parallel_tool_calls: bool
    """
    Whether to enable
    [parallel function calling](https://platform.openai.com/docs/guides/function-calling/parallel-function-calling)
    during tool use.
    """

    required_action: RequiredAction | None = Field(None, sa_type=JSON)
    """Details on the action required to continue the run.

    Will be `null` if no action is required.
    """

    response_format: AssistantResponseFormatOption | None = Field(
        None, sa_column=Column(JSON)
    )
    """Specifies the format that the model must output.

    Compatible with [GPT-4o](https://platform.openai.com/docs/models/gpt-4o),
    [GPT-4 Turbo](https://platform.openai.com/docs/models/gpt-4-turbo-and-gpt-4),
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

    started_at: datetime | None = None
    """The Unix timestamp (in seconds) for when the run was started."""

    status: RunStatus
    """
    The status of the run, which can be either `queued`, `in_progress`,
    `requires_action`, `cancelling`, `cancelled`, `failed`, `completed`,
    `incomplete`, or `expired`.
    """

    thread_id: str = Field(foreign_key="thread.id")
    """
    The ID of the [thread](https://platform.openai.com/docs/api-reference/threads)
    that was executed on as a part of this run.
    """

    tool_choice: AssistantToolChoiceOption | None = Field(None, sa_column=Column(JSON))
    """
    Controls which (if any) tool is called by the model. `none` means the model will
    not call any tools and instead generates a message. `auto` is the default value
    and means the model can pick between generating a message or calling one or more
    tools. `required` means the model must call one or more tools before responding
    to the user. Specifying a particular tool like `{"type": "file_search"}` or
    `{"type": "function", "function": {"name": "my_function"}}` forces the model to
    call that tool.
    """

    tools: list[AssistantTool] = Field(default_factory=list, sa_column=Column(JSON))
    """
    The list of tools that the
    [assistant](https://platform.openai.com/docs/api-reference/assistants) used for
    this run.
    """

    truncation_strategy: TruncationStrategy | None = Field(None, sa_type=JSON)
    """Controls for how a thread will be truncated prior to the run.

    Use this to control the intial context window of the run.
    """

    usage: Usage | None = Field(None, sa_type=JSON)
    """Usage statistics related to the run.

    This value will be `null` if the run is not in a terminal state (i.e.
    `in_progress`, `queued`, etc.).
    """

    temperature: float | None = None
    """The sampling temperature used for this run. If not set, defaults to 1."""

    top_p: float | None = None
    """The nucleus sampling value used for this run. If not set, defaults to 1."""

    @field_serializer(
        "cancelled_at", "completed_at", "expires_at", "failed_at", "started_at"
    )
    def serialize_started_at(self, value: datetime | None) -> int | None:
        if value is None:
            return None
        return int(value.timestamp())

    assistant: Assistant = Relationship(back_populates="runs")

    thread: Thread = Relationship(back_populates="runs")

    message: "Message" = Relationship(
        sa_relationship_kwargs={"uselist": False}, back_populates="run"
    )

    steps: list["RunStep"] = Relationship(back_populates="run")


class MessageRole(Enum):
    user = "user"
    assistant = "assistant"


class MessageStatus(Enum):
    in_progress = "in_progress"
    incomplete = "incomplete"
    completed = "completed"


class Message(Base, MetadataMixin, table=True):
    id: str = Field(default_factory=random_id_with_prefix("msg_"), primary_key=True)
    """The identifier, which can be referenced in API endpoints."""

    assistant_id: str | None = Field(None, foreign_key="assistant.id")
    """
    If applicable, the ID of the
    [assistant](https://platform.openai.com/docs/api-reference/assistants) that
    authored this message.
    """

    attachments: list[Attachment] | None = Field(default=None, sa_column=Column(JSON))
    """A list of files attached to the message, and the tools they were added to."""

    completed_at: datetime | None = None
    """The Unix timestamp (in seconds) for when the message was completed."""

    content: list[MessageContent] = Field(default_factory=list, sa_column=Column(JSON))
    """The content of the message in array of text and/or images."""

    incomplete_at: datetime | None = None
    """The Unix timestamp (in seconds) for when the message was marked as incomplete."""

    incomplete_details: MessageIncompleteDetails | None = Field(None, sa_type=JSON)
    """On an incomplete message, details about why the message is incomplete."""

    @computed_field
    def object(self) -> Literal["thread.message"]:
        """The object type, which is always `thread.message`."""
        return "thread.message"

    role: MessageRole
    """The entity that produced the message. One of `user` or `assistant`."""

    run_id: str | None = Field(None, foreign_key="run.id")
    """
    The ID of the [run](https://platform.openai.com/docs/api-reference/runs)
    associated with the creation of this message. Value is `null` when messages are
    created manually using the create message or create thread endpoints.
    """

    status: MessageStatus
    """
    The status of the message, which can be either `in_progress`, `incomplete`, or
    `completed`.
    """

    thread_id: str = Field(foreign_key="thread.id")
    """
    The [thread](https://platform.openai.com/docs/api-reference/threads) ID that
    this message belongs to.
    """

    @field_serializer("completed_at", "incomplete_at")
    def serialize_incomplete_at(self, value: datetime | None) -> int | None:
        if value is None:
            return None
        return int(value.timestamp())

    assistant: Assistant = Relationship(back_populates="messages")

    thread: Thread = Relationship(back_populates="messages")

    run: Run | None = Relationship(back_populates="message")


class RunStepStatus(Enum):
    in_progress = "in_progress"
    cancelled = "cancelled"
    failed = "failed"
    completed = "completed"
    expired = "expired"


class RunStepType(Enum):
    message_creation = "message_creation"
    tool_calls = "tool_calls"


class RunStep(Base, MetadataMixin, table=True):
    id: str = Field(default_factory=random_id_with_prefix("step_"), primary_key=True)
    """The identifier of the run step, which can be referenced in API endpoints."""

    assistant_id: str = Field(foreign_key="assistant.id")
    """
    The ID of the
    [assistant](https://platform.openai.com/docs/api-reference/assistants)
    associated with the run step.
    """

    cancelled_at: datetime | None = None
    """The Unix timestamp (in seconds) for when the run step was cancelled."""

    completed_at: datetime | None = None
    """The Unix timestamp (in seconds) for when the run step completed."""

    expired_at: datetime | None = None
    """The Unix timestamp (in seconds) for when the run step expired.

    A step is considered expired if the parent run is expired.
    """

    failed_at: datetime | None = None
    """The Unix timestamp (in seconds) for when the run step failed."""

    last_error: RunStepLastError | None = Field(None, sa_type=JSON)
    """The last error associated with this run step.

    Will be `null` if there are no errors.
    """

    @computed_field
    def object(self) -> Literal["thread.run.step"]:
        """The object type, which is always `thread.run.step`."""
        return "thread.run.step"

    run_id: str = Field(foreign_key="run.id")
    """
    The ID of the [run](https://platform.openai.com/docs/api-reference/runs) that
    this run step is a part of.
    """

    status: RunStepStatus
    """
    The status of the run step, which can be either `in_progress`, `cancelled`,
    `failed`, `completed`, or `expired`.
    """

    step_details: StepDetails = Field(sa_column=Column(JSON))
    """The details of the run step."""

    thread_id: str = Field(foreign_key="thread.id")
    """
    The ID of the [thread](https://platform.openai.com/docs/api-reference/threads)
    that was run.
    """

    type: RunStepType
    """The type of run step, which can be either `message_creation` or `tool_calls`."""

    usage: Usage | None = Field(None, sa_type=JSON)
    """Usage statistics related to the run step.

    This value will be `null` while the run step's status is `in_progress`.
    """

    @field_serializer("cancelled_at", "completed_at", "expired_at", "failed_at")
    def serialize_failed_at(self, value: datetime | None) -> int | None:
        if value is None:
            return None
        return int(value.timestamp())

    run: Run = Relationship(back_populates="steps")


class UserSettings(BaseModel):
    """User Settings."""

    object: Literal["user.settings"] = "user.settings"


class User(SQLModel, table=True):
    """User model."""

    id: str = Field(default_factory=random_id_with_prefix("user_"), primary_key=True)
    name: str = Field(max_length=150, unique=True, regex=r"^[\w.@+-]+$")
    password: str
    email: EmailStr | None = Field(nullable=True)
    is_superuser: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(
        default_factory=now, sa_column_kwargs={"onupdate": now}
    )
    settings: UserSettings = Field(default_factory=dict, sa_column=Column(JSON))
    api_keys: list["APIKey"] = Relationship(back_populates="user")


class APIKey(SQLModel, table=True):
    """API key model.

    API key is used for authenticating the user.
    """

    __tablename__ = "api_key"

    id: str = Field(default_factory=random_id_with_prefix("sk-"), primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    user: "User" = Relationship(back_populates="api_keys")
    name: str = Field(default="New API key", max_length=255)
    created_at: datetime = Field(default_factory=now)


def get_api_key(api_key: str) -> APIKey | None:
    """Get the API key."""
    if not settings.auth_enabled:
        return APIKey(id=api_key, user=User(name="test", password="test"))
    try:
        return settings.session.get(APIKey, api_key)
    except NoResultFound:
        return None


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> User:
    """Get the current user."""
    api_key = get_api_key(credentials.credentials)
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )
    return api_key.user


def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Get the current active user."""
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return user
