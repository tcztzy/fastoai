from fastapi import APIRouter, Depends
from openai.types.beta.threads.message import Message as OpenAIMessage
from openai.types.beta.threads.message_create_params import MessageCreateParams
from pydantic import RootModel
from sqlmodel import select

from ...models import Message
from ...pagination import AsyncCursorPage
from ...settings import Settings, get_settings

router = APIRouter()


@router.post("/threads/{thread_id}/messages")
async def create_message(
    thread_id: str,
    params: RootModel[MessageCreateParams],
    settings: Settings = Depends(get_settings),
):
    params = params.root
    if isinstance(params.content, str):
        params.content = [
            {"type": "text", "text": {"value": params.content, "annotations": []}}
        ]
    message = Message(
        thread_id=thread_id,
        data=OpenAIMessage(
            id="dummy",
            created_at=0,
            object="thread.message",
            thread_id=thread_id,
            attachments=params.attachments or None,
            status="completed",
            content=params.content,
            role=params.role,
        ),
    )
    settings.session.add(message)
    settings.session.commit()
    settings.session.refresh(message)
    return message


@router.get("/threads/{thread_id}/messages")
async def list_messages(
    thread_id: str,
    settings: Settings = Depends(get_settings),
) -> AsyncCursorPage[OpenAIMessage]:
    messages = await settings.session.exec(
        select(Message).where(Message.thread_id == thread_id)
    )
    return AsyncCursorPage[OpenAIMessage](data=messages.all())
