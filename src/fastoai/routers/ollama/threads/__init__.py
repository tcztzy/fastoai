from fastapi import Depends
from openai.types.beta.thread import Thread as OpenAIThread
from sqlmodel import select

from ....models.thread import Thread
from ....models.user import User, get_current_active_user
from ....requests import MessageCreateParams, ThreadCreateParams
from ....schema import ListObject
from ....settings import Settings, get_settings
from .messages import create_message
from .runs import create_thread_and_run

__all__ = ["create_thread_and_run"]


async def create_thread(
    params: ThreadCreateParams | None = None,
    user: User = Depends(get_current_active_user),
    settings: Settings = Depends(get_settings),
) -> OpenAIThread:
    openai_thread = OpenAIThread(id="dummy", created_at=0, object="thread")
    if params is not None:
        if params.tool_resources:
            openai_thread.tool_resources = params.tool_resources
        if params.metadata:
            openai_thread.metadata = params.metadata
    thread = Thread(data=openai_thread)
    settings.session.add(thread)
    settings.session.commit()
    for message in params.messages or []:
        await create_message(
            thread_id=thread.id,
            params=MessageCreateParams.model_validate(message),
            user=user,
            settings=settings,
        )
    settings.session.refresh(thread)
    return thread.data


async def list_threads(
    settings: Settings = Depends(get_settings),
    user: User = Depends(get_current_active_user),
) -> ListObject[OpenAIThread]:
    threads = settings.session.exec(select(Thread)).all()
    return ListObject[OpenAIThread](data=[thread.data for thread in threads])
