from functools import lru_cache

from ollama import AsyncClient as AsyncOllama
from openai import AsyncOpenAI


@lru_cache
def get_ollama() -> AsyncOllama:
    return AsyncOllama("http://localhost:11434/v1")


@lru_cache
def get_openai() -> AsyncOpenAI:
    return AsyncOpenAI(api_key="ollama", base_url="http://localhost:11434/v1")
