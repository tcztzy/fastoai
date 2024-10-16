import json
from typing import AsyncIterable, cast

from fastapi import Depends
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import (
    ChatCompletionChunk,
    ChoiceDeltaToolCall,
    ChoiceDeltaToolCallFunction,
)

from ...models import User, get_current_active_user
from ...requests import (
    CompletionCreateParams,
)
from ...routing import OAIRouter
from ...utils import random_id_with_prefix
from ._backend import get_openai
from .assistants import router as assistants_router
from .files import router as files_router
from .models import router as models_router
from .threads import router as threads_router
from .threads.messages import router as messages_router
from .threads.runs import router as runs_router

router = OAIRouter()

chat_router = OAIRouter(tags=["Chat"])


@chat_router.post_chat_completions
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
                # Hijack the response to add the tool choice because Ollama doesn't support it
                if (
                    len(params.tools) > 0
                    and params.tool_choice != "none"
                    and params.model.startswith("qwen2.5")
                    and chunk.choices[0].delta.content == "<tool_call>"
                ):
                    new_chunk = chunk.model_copy()
                    choice = new_chunk.choices[0].model_copy()
                    choice.finish_reason = "tool_calls"
                    choice.delta.content = None
                    tool_call = ""
                    choice.delta.tool_calls = []
                    current_index = 0
                    async for _chunk in chunks:
                        if _chunk.choices[0].delta.content == "<tool_call>":
                            tool_call = ""
                            current_index += 1
                            continue
                        if _chunk.choices[0].delta.content == "</tool_call>":
                            tool_call_json = json.loads(tool_call)
                            tool_call_json["arguments"] = json.dumps(
                                tool_call_json["arguments"]
                            )
                            choice.delta.tool_calls.append(
                                ChoiceDeltaToolCall(
                                    index=current_index,
                                    id=random_id_with_prefix("call_")(),
                                    function=ChoiceDeltaToolCallFunction.model_validate(
                                        tool_call_json
                                    ),
                                    type="function",
                                )
                            )
                            continue
                        tool_call += _chunk.choices[0].delta.content
                    new_chunk.choices = [choice]
                    yield f"data: {new_chunk.model_dump_json()}\n\n"
                    break
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
