from fastapi import APIRouter
from openai.types.beta.thread_create_params import ThreadCreateParams
from openai.types.beta.threads.message_create_params import MessageCreateParams
from pydantic import RootModel

from ...dependencies import SessionDependency
from ...models import Thread
from .messages import create_message

router = APIRouter()


@router.post("/threads")
async def create_thread(
    *,
    params: RootModel[ThreadCreateParams] | None = None,
    session: SessionDependency,
) -> Thread:
    thread = Thread.model_validate(
        {}
        if params is None
        else params.model_dump(exclude={"messages"}, exclude_none=True)
    )
    session.add(thread)
    await session.commit()
    for message in params.root.get("messages", []) if params is not None else []:
        await create_message(
            thread_id=thread.id,
            params=RootModel[MessageCreateParams].model_validate(message),
            session=session,
        )
    await session.refresh(thread)
    return thread


@router.get("/threads/{thread_id}")
async def retrieve_thread(*, thread_id: str, session: SessionDependency) -> Thread:
    thread = await session.get_one(Thread, thread_id)
    return thread
