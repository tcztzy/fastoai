from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from fastoai.routers._client import get_client_class


def test_get_client():
    assert get_client_class("gpt-4o-mini") is AsyncOpenAI
    assert get_client_class("claude-3-5-sonnet-latest") is AsyncAnthropic
