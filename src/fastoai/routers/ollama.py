from typing import AsyncIterable, cast

from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk

from ..requests import CompletionCreateParams
from ..routing import OAIRouter

router = OAIRouter()


@router.post_chat_completions
async def create_chat_completions(params: CompletionCreateParams):
    client = AsyncOpenAI(api_key="ollama", base_url="http://localhost:11434/v1")
    response = await client.chat.completions.create(**params.model_dump())
    if params.stream:

        async def _stream():
            async for chunk in cast(AsyncIterable[ChatCompletionChunk], response):
                yield f"data: {chunk.model_dump_json()}\n\n"
            else:
                yield "data: [DONE]\n\n"

        return StreamingResponse(_stream())
    return cast(ChatCompletion, response)
