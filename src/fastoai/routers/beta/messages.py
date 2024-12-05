from typing import cast

from fastapi import APIRouter
from openai.types.beta.threads.message import Message as OpenAIMessage
from openai.types.beta.threads.message_create_params import MessageCreateParams
from pydantic import RootModel

from ...dependencies import SessionDependency
from ...models import Message, Thread
from ...pagination import AsyncCursorPage

router = APIRouter()


@router.post("/threads/{thread_id}/messages")
async def create_message(
    thread_id: str,
    params: RootModel[MessageCreateParams],
    session: SessionDependency,
):
    if isinstance(params.root["content"], str):
        content = [
            {
                "type": "text",
                "text": {"value": params.root["content"], "annotations": []},
            }
        ]
    else:
        content = params.root["content"]
    message = Message(  # type: ignore
        thread_id=thread_id,
        attachments=params.root.get("attachments"),
        status="completed",
        content=content,
        role=params.root["role"],
    )
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message


@router.get("/threads/{thread_id}/messages")
async def list_messages(
    thread_id: str,
    session: SessionDependency,
) -> AsyncCursorPage[OpenAIMessage]:
    thread = await session.get_one(Thread, thread_id)
    messages = [
        await m.to_openai_model()
        for m in cast(list[Message], await thread.awaitable_attrs.messages)
    ]
    return AsyncCursorPage[OpenAIMessage](data=messages)
