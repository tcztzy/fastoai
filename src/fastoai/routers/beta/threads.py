from fastapi import APIRouter, Depends, HTTPException
from openai.types.beta.thread_create_params import ThreadCreateParams
from openai.types.beta.threads.message_create_params import MessageCreateParams
from pydantic import RootModel

from ...models import Thread
from ...settings import Settings, get_settings
from .messages import create_message

router = APIRouter()


@router.post("/threads")
async def create_thread(
    params: RootModel[ThreadCreateParams] | None = None,
    settings: Settings = Depends(get_settings),
) -> Thread:
    thread = Thread.model_validate(
        {}
        if params is None
        else params.model_dump(exclude={"messages"}, exclude_none=True)
    )
    settings.session.add(thread)
    await settings.session.commit()
    for message in params.root["messages"] if params is not None else []:
        await create_message(
            thread_id=thread.id,
            params=RootModel[MessageCreateParams].model_validate(message),
            settings=settings,
        )
    await settings.session.refresh(thread)
    return thread


@router.get("/threads/{thread_id}")
async def retrieve_thread(
    thread_id: str, settings: Settings = Depends(get_settings)
) -> Thread:
    thread = await settings.session.get(Thread, thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread
