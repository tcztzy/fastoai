from typing import AsyncIterable, cast

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.completion_create_params import CompletionCreateParams
from pydantic import RootModel

from ..dependencies import OpenAIDependency, get_user
from .beta import router as beta_router
from .files import router as files_router
from .models import router as models_router

router = APIRouter(dependencies=[Depends(get_user)])

chat_router = APIRouter(tags=["Chat"])


@chat_router.post("/chat/completions")
async def create_chat_completions(
    params: RootModel[CompletionCreateParams],
    openai: OpenAIDependency,
):
    response = await openai.chat.completions.create(**params.model_dump())
    if params.root.get("stream", False):
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
    beta_router,
]:
    router.include_router(subrouter)
