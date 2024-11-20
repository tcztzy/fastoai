from typing import AsyncIterable, cast

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk

from ..models import User, get_current_active_user
from ..requests import (
    CompletionCreateParams,
)
from ._backend import get_openai
from .assistants import router as assistants_router
from .files import router as files_router
from .models import router as models_router
from .threads import router as threads_router
from .threads.messages import router as messages_router
from .threads.runs import router as runs_router

router = APIRouter()

chat_router = APIRouter(tags=["Chat"])


@chat_router.post("/chat/completions")
async def create_chat_completions(
    params: CompletionCreateParams,
    user: User = Depends(get_current_active_user),
    openai: AsyncOpenAI = Depends(get_openai),
):
    response = await openai.chat.completions.create(**params.model_dump())
    if params.stream:
        response = cast(AsyncIterable[ChatCompletionChunk], response)

        async def _stream(chunks: AsyncIterable[ChatCompletionChunk]):
            async for chunk in chunks:
                yield f"data: {chunk.model_dump_json()}\n\n"

            yield "data: [DONE]\n\n"

        return StreamingResponse(_stream(response))
    return cast(ChatCompletion, response)


for subrouter in [
    chat_router,
    models_router,
    files_router,
    assistants_router,
    threads_router,
    messages_router,
    runs_router,
]:
    router.include_router(subrouter)
