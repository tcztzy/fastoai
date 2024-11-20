from fastapi import Depends, HTTPException
from openai.types.beta.threads.message import Message as OpenAIMessage
from sqlmodel import select

from ...models import Message, Thread, User, get_current_active_user
from ...requests import MessageCreateParams
from ...routing import OAIRouter
from ...schema import ListObject
from ...settings import Settings, get_settings
from .._fix import MetadataRenameRoute

router = OAIRouter(tags=["Messages"], route_class=MetadataRenameRoute)


def get_thread(thread_id: str, settings: Settings = Depends(get_settings)) -> Thread:
    thread = settings.session.get(Thread, thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


@router.post("/threads/{thread_id}/messages")
async def create_message(
    thread_id: str,
    params: MessageCreateParams,
    user: User = Depends(get_current_active_user),
    settings: Settings = Depends(get_settings),
):
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
    user: User = Depends(get_current_active_user),
) -> ListObject[OpenAIMessage]:
    messages = settings.session.exec(
        select(Message).where(Message.thread_id == thread_id)
    ).all()
    return ListObject[OpenAIMessage](data=[message.data for message in messages])
