from fastapi import Depends
from sqlmodel import select

from ....models import Thread, User, get_current_active_user
from ....requests import MessageCreateParams, ThreadCreateParams
from ....routing import OAIRouter
from ....schema import ListObject
from ....settings import Settings, get_settings
from .._fix import MetadataRenameRoute
from .messages import create_message

router = OAIRouter(tags=["Threads"], route_class=MetadataRenameRoute)


@router.post("/threads")
async def create_thread(
    params: ThreadCreateParams | None = None,
    user: User = Depends(get_current_active_user),
    settings: Settings = Depends(get_settings),
) -> Thread:
    thread = Thread.model_validate(
        {}
        if params is None
        else params.model_dump(exclude={"messages"}, exclude_none=True)
    )
    settings.session.add(thread)
    settings.session.commit()
    for message in params.messages if params is not None else []:
        await create_message(
            thread_id=thread.id,
            params=MessageCreateParams.model_validate(message),
            user=user,
            settings=settings,
        )
    settings.session.refresh(thread)
    return thread


@router.get("/threads")
async def list_threads(
    settings: Settings = Depends(get_settings),
    user: User = Depends(get_current_active_user),
) -> ListObject[Thread]:
    threads = settings.session.exec(select(Thread)).all()
    return ListObject[Thread](data=threads)
