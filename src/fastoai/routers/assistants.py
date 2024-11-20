from typing import Annotated, Literal

from fastapi import Depends, HTTPException
from openai.types.beta.assistant_deleted import AssistantDeleted
from pydantic import Field
from sqlmodel import col, select

from ..models import Assistant, User, get_current_active_user
from ..requests import AssistantCreateParams, AssistantUpdateParams
from ..routing import OAIRouter
from ..schema import ListObject
from ..settings import Settings, get_settings
from ._fix import MetadataRenameRoute

router = OAIRouter(tags=["Assistants"], route_class=MetadataRenameRoute)


@router.post_assistants(response_model_exclude_unset=True, response_model_by_alias=True)
async def create_assistant(
    params: AssistantCreateParams,
    settings: Settings = Depends(get_settings),
    user: User = Depends(get_current_active_user),
) -> Assistant:
    obj = params.model_dump(exclude_unset=True)
    obj["tools"] = list(obj["tools"])
    assistant = Assistant.model_validate(obj)
    assistant.tools = list(assistant.tools)
    settings.session.add(assistant)
    settings.session.commit()
    settings.session.refresh(assistant)
    return assistant


@router.get_assistants
async def list_assistants(
    limit: Annotated[int, Field(ge=1, le=100)] = 20,
    order: Literal["asc", "desc"] = "desc",
    after: str | None = None,
    before: str | None = None,
    settings: Settings = Depends(get_settings),
    user: User = Depends(get_current_active_user),
) -> ListObject[Assistant]:
    statement = select(Assistant).order_by(getattr(col(Assistant.created_at), order)())
    if after is not None:
        after_assistant = settings.session.get(Assistant, after)
        statement = statement.where(
            Assistant.created_at < after_assistant.created_at
            if order == "desc"
            else Assistant.created_at > after_assistant.created_at
        )
    if before is not None:
        before_assistant = settings.session.get(Assistant, before)
        statement = statement.where(
            Assistant.created_at > before_assistant.created_at
            if order == "desc"
            else Assistant.created_at < before_assistant.created_at
        )
    assistants = settings.session.exec(statement.limit(limit)).all()
    kwargs = {}
    if len(assistants) > 0:
        kwargs["first_id"] = assistants[0].id
        kwargs["last_id"] = assistants[-1].id
    if len(assistants) == limit:
        after_assistant = settings.session.get(Assistant, assistants[-1].id)
        statement = (
            select(Assistant)
            .order_by(getattr(col(Assistant.created_at), order)())
            .where(
                Assistant.created_at < after_assistant.created_at
                if order == "desc"
                else Assistant.created_at > after_assistant.created_at
            )
        )
        has_more = len(settings.session.exec(statement.limit(1)).all()) == 1
    else:
        has_more = False
    return ListObject[Assistant](data=assistants, has_more=has_more, **kwargs)


@router.get("/assistants/{assistant_id}")
async def retrieve_assistant(
    assistant_id: str,
    settings: Settings = Depends(get_settings),
    user: User = Depends(get_current_active_user),
) -> Assistant:
    assistant = settings.session.get(Assistant, assistant_id)
    if assistant is None:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return assistant


@router.post("/assistants/{assistant_id}")
async def update_assistant(
    assistant_id: str,
    params: AssistantUpdateParams,
    settings: Settings = Depends(get_settings),
    user: User = Depends(get_current_active_user),
) -> Assistant:
    assistant = settings.session.get(Assistant, assistant_id)
    assistant.data = assistant.data.model_validate(
        assistant.data.model_dump().update(params.model_dump())
    )
    settings.session.commit()
    return assistant.data


@router.delete("/assistants/{assistant_id}")
async def delete_assistant(
    assistant_id: str,
    settings: Settings = Depends(get_settings),
    user: User = Depends(get_current_active_user),
) -> AssistantDeleted:
    assistant = settings.session.get(Assistant, assistant_id)
    if assistant is None:
        raise HTTPException(status_code=404, detail="Assistant not found")
    settings.session.delete(assistant)
    settings.session.commit()
    return AssistantDeleted(id=assistant_id, deleted=True, object="assistant.deleted")
