from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, HTTPException
from openai.types.beta.assistant_create_params import AssistantCreateParams
from openai.types.beta.assistant_deleted import AssistantDeleted
from openai.types.beta.assistant_update_params import AssistantUpdateParams
from pydantic import Field, RootModel
from sqlmodel import col, select

from ...models import Assistant
from ...pagination import AsyncCursorPage
from ...settings import Settings, get_settings

router = APIRouter()


@router.post("/assistants")
async def create_assistant(
    params: RootModel[AssistantCreateParams],
    settings: Settings = Depends(get_settings),
) -> Assistant:
    assistant = Assistant.model_validate(params.model_dump())
    settings.session.add(assistant)
    await settings.session.commit()
    await settings.session.refresh(assistant)
    return assistant


@router.get("/assistants")
async def list_assistants(
    limit: Annotated[int, Field(ge=1, le=100)] = 20,
    order: Literal["asc", "desc"] = "desc",
    after: str | None = None,
    before: str | None = None,
    settings: Settings = Depends(get_settings),
) -> AsyncCursorPage[Assistant]:
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
    assistants = (await settings.session.exec(statement.limit(limit))).all()
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
    return AsyncCursorPage[Assistant](data=assistants, **kwargs)


@router.get("/assistants/{assistant_id}")
async def retrieve_assistant(
    assistant_id: str,
    settings: Settings = Depends(get_settings),
) -> Assistant:
    assistant = settings.session.get(Assistant, assistant_id)
    if assistant is None:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return assistant


@router.post("/assistants/{assistant_id}")
async def update_assistant(
    assistant_id: str,
    params: RootModel[AssistantUpdateParams],
    settings: Settings = Depends(get_settings),
) -> Assistant:
    assistant = await settings.session.get(Assistant, assistant_id)
    if assistant is None:
        raise HTTPException(status_code=404, detail="Assistant not found")
    obj = cast(AssistantUpdateParams, params.model_dump(exclude_unset=True))
    assistant = Assistant.model_validate(assistant.model_dump() | obj)
    await settings.session.commit()
    return assistant


@router.delete("/assistants/{assistant_id}")
async def delete_assistant(
    assistant_id: str,
    settings: Settings = Depends(get_settings),
) -> AssistantDeleted:
    assistant = settings.session.get(Assistant, assistant_id)
    if assistant is None:
        raise HTTPException(status_code=404, detail="Assistant not found")
    settings.session.delete(assistant)
    settings.session.commit()
    return AssistantDeleted(id=assistant_id, deleted=True, object="assistant.deleted")
