import inspect
from typing import Any, Dict, Iterable, List, Literal, Optional, Union  # noqa: F401

from openai import NotGiven  # noqa: F401
from openai.resources.beta.assistants import Assistants
from openai.resources.beta.threads import Threads
from openai.resources.beta.threads.messages import Messages
from openai.resources.beta.threads.runs import Runs
from openai.resources.chat import Completions
from openai.types.beta import (
    assistant_create_params,  # noqa: F401
    assistant_update_params,  # noqa: F401
    thread_create_and_run_params,  # noqa: F401
    thread_create_params,  # noqa: F401
)
from openai.types.beta.assistant_response_format_option_param import (
    AssistantResponseFormatOptionParam,  # noqa: F401
)
from openai.types.beta.assistant_tool_choice_option_param import (
    AssistantToolChoiceOptionParam,  # noqa: F401
)
from openai.types.beta.assistant_tool_param import AssistantToolParam  # noqa: F401
from openai.types.beta.threads import (
    message_create_params,  # noqa: F401
    run_create_params,  # noqa: F401
)
from openai.types.beta.threads.message_content_part_param import (
    MessageContentPartParam,  # noqa: F401
)
from openai.types.chat import completion_create_params  # noqa: F401
from openai.types.chat.chat_completion_message_param import (
    ChatCompletionMessageParam,  # noqa: F401
)
from openai.types.chat.chat_completion_stream_options_param import (
    ChatCompletionStreamOptionsParam,  # noqa: F401
)
from openai.types.chat.chat_completion_tool_choice_option_param import (
    ChatCompletionToolChoiceOptionParam,  # noqa: F401
)
from openai.types.chat.chat_completion_tool_param import (
    ChatCompletionToolParam,  # noqa: F401
)
from openai.types.chat_model import ChatModel  # noqa: F401
from pydantic import BaseModel, ConfigDict, create_model

signature = inspect.signature(Completions.create)


EXCLUDED_PARAMS = ["self", "extra_headers", "extra_query", "extra_body", "timeout"]


def get_field_definitions(signature: inspect.Signature) -> Any:
    def process_parameter(parameter: inspect.Parameter):
        annotation = parameter.annotation
        default = parameter.default
        if default == inspect._empty:
            default = ...
        return annotation, default

    return {
        name: process_parameter(parameter)
        for name, parameter in signature.parameters.items()
        if parameter.kind == parameter.KEYWORD_ONLY and name not in EXCLUDED_PARAMS
    }


def create_pydantic_model(model_name: str, func) -> Any:
    signature = inspect.signature(func)
    field_definitions = get_field_definitions(signature)
    return create_model(
        model_name,
        __config__=ConfigDict(arbitrary_types_allowed=True),
        **field_definitions,
    )


CompletionCreateParams: type[BaseModel] = create_pydantic_model(
    "CompletionCreateParams", Completions.create
)
AssistantCreateParams: type[BaseModel] = create_pydantic_model(
    "AssistantCreateParams", Assistants.create
)
AssistantUpdateParams: type[BaseModel] = create_pydantic_model(
    "AssistantUpdateParams", Assistants.update
)
ThreadCreateParams: type[BaseModel] = create_pydantic_model(
    "ThreadCreateParams", Threads.create
)
ThreadCreateAndRunParams: type[BaseModel] = create_pydantic_model(
    "ThreadCreateAndRunParams", Threads.create_and_run
)
MessageCreateParams: type[BaseModel] = create_pydantic_model(
    "MessageCreateParams", Messages.create
)
RunCreateParams: type[BaseModel] = create_pydantic_model("RunCreateParams", Runs.create)

if __name__ == "__main__":
    import json

    # print(CompletionCreateParams.model_json_schema())
    # print(ThreadCreateParams.model_json_schema())
    # print(ThreadCreateAndRunParams.model_json_schema())
    # print(json.dumps(MessageCreateParams.model_json_schema()))
    print(json.dumps(RunCreateParams.model_json_schema()))
