import inspect
from typing import Any, Dict, Iterable, List, Literal, Optional, Union  # noqa: F401

from openai import NotGiven  # noqa: F401
from openai.resources.chat import Completions
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
from pydantic import ConfigDict, create_model

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
        if name not in EXCLUDED_PARAMS
    }


def create_pydantic_model(model_name: str, func):
    signature = inspect.signature(func)
    field_definitions = get_field_definitions(signature)
    return create_model(
        model_name,
        __config__=ConfigDict(arbitrary_types_allowed=True),
        **field_definitions,
    )


CompletionCreateParams = create_pydantic_model(
    "CompletionCreateParams", Completions.create
)

if __name__ == "__main__":
    print(CompletionCreateParams.model_json_schema())
