from typing import AsyncIterable, cast

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.completion_create_params import CompletionCreateParams
from pydantic import RootModel

from ..dependencies import ClientDependency, get_user
from .beta import router as beta_router
from .files import router as files_router
from .models import router as models_router

router = APIRouter(dependencies=[Depends(get_user)])

chat_router = APIRouter(tags=["Chat"])


@chat_router.post("/chat/completions")
async def create_chat_completions(
    params: RootModel[CompletionCreateParams],
    client: ClientDependency,
):
    response = await client.chat.completions.create(**params.model_dump())
    if params.root.get("stream", False):
        response = cast(AsyncIterable[ChatCompletionChunk], response)

        async def _stream(chunks: AsyncIterable[ChatCompletionChunk]):
            # deepseek reasoner has a extra field "reasoning_content" and this will not
            # present when "content" is present, so we need to add it in <think></think>
            thinking = False
            async for chunk in chunks:
                delta = chunk.choices[0].delta
                if hasattr(delta, "reasoning_content"):
                    content = cast(str, getattr(delta, "reasoning_content"))
                    delta.content = content
                    if not thinking:
                        delta.content = "<think>" + content
                    thinking = True
                if thinking and not hasattr(delta, "reasoning_content"):
                    delta.content = "</think>" + (delta.content or "")
                yield f"data: {chunk.model_dump_json(exclude_none=True)}\n\n"

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
