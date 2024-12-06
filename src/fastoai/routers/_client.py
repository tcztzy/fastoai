from typing import get_args

from anthropic import AsyncAnthropic
from anthropic.types.model_param import ModelParam
from openai import AsyncOpenAI
from openai.types.chat_model import ChatModel


def get_client_class(model: str) -> type[AsyncAnthropic] | type[AsyncOpenAI]:
    if model in get_args(ChatModel):
        return AsyncOpenAI
    if model in get_args(get_args(ModelParam)[1]):
        return AsyncAnthropic
    raise ValueError(f"Can't recognize model {model}.")
