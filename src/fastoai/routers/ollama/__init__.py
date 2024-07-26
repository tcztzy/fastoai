from typing import AsyncIterable, cast

from fastapi import Depends
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk

from ...models.user import User, get_current_active_user
from ...requests import (
    CompletionCreateParams,
)
from ...routing import OAIRouter
from ._backend import get_openai
from .assistants import (
    create_assistant,
    delete_assistant,
    list_assistants,
    retrieve_assistant,
    update_assistant,
)
from .file import (
    delete_file,
    list_files,
    retrieve_file,
    retrieve_file_content,
    upload_file,
)
from .models import delete_model, list_models, retrieve_model
from .threads import create_thread, list_threads
from .threads.messages import create_message, list_messages
from .threads.runs import create_thread_and_run

router = OAIRouter()


@router.post_chat_completions
async def create_chat_completions(
    params: CompletionCreateParams,
    user: User = Depends(get_current_active_user),
    openai: AsyncOpenAI = Depends(get_openai),
):
    response = await openai.chat.completions.create(**params.model_dump())
    if params.stream:

        async def _stream():
            async for chunk in cast(AsyncIterable[ChatCompletionChunk], response):
                yield f"data: {chunk.model_dump_json()}\n\n"
            else:
                yield "data: [DONE]\n\n"

        return StreamingResponse(_stream())
    return cast(ChatCompletion, response)


router.get_models(response_model_exclude_unset=True)(list_models)
router.get("/models/{model:path}")(retrieve_model)
router.delete("/models/{model:path}")(delete_model)

router.post("/files")(upload_file)
router.get("/files")(list_files)
router.get("/files/{file_id}")(retrieve_file)
router.get("/files/{file_id}/content")(retrieve_file_content)
router.delete("/files/{file_id}")(delete_file)

router.get_assistants(list_assistants)
router.post_assistants(response_model_exclude_unset=True)(create_assistant)
router.get("/assistants/{assistant_id}")(retrieve_assistant)
router.post("/assistants/{assistant_id}")(update_assistant)
router.delete("/assistants/{assistant_id}")(delete_assistant)

router.post("/threads")(create_thread)
router.get("/threads")(list_threads)

router.post("/threads/{thread_id}/messages")(create_message)
router.get("/threads/{thread_id}/messages")(list_messages)

router.post("/threads/runs")(create_thread_and_run)
