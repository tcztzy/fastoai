from typing import Annotated, cast

from fastapi import APIRouter
from openai.types.beta.assistant import Assistant as _Assistant
from openai.types.beta.assistant_create_params import AssistantCreateParams
from openai.types.beta.assistant_deleted import AssistantDeleted
from openai.types.beta.assistant_update_params import AssistantUpdateParams
from pydantic import Field, RootModel
from sqlmodel import col, select

from ...dependencies import SessionDependency
from ...models import Assistant
from ...pagination import AsyncCursorPage
from .._types import Order

router = APIRouter()


@router.post("/assistants", response_model=_Assistant)
async def create_assistant(
    params: RootModel[AssistantCreateParams],
    session: SessionDependency,
) -> _Assistant:
    assistant = Assistant.model_validate(params.model_dump())
    session.add(assistant)
    await session.commit()
    await session.refresh(assistant)
    return await assistant.to_openai_model()


@router.get("/assistants", response_model=AsyncCursorPage[_Assistant])
async def list_assistants(
    *,
    limit: Annotated[int, Field(ge=1, le=100)] = 20,
    order: Order = "desc",
    after: str | None = None,
    before: str | None = None,
    session: SessionDependency,
) -> AsyncCursorPage[_Assistant]:
    statement = select(Assistant).order_by(getattr(col(Assistant.created_at), order)())
    if after is not None:
        after_assistant = await session.get_one(Assistant, after)
        statement = statement.where(
            Assistant.created_at < after_assistant.created_at
            if order == "desc"
            else Assistant.created_at > after_assistant.created_at
        )
    if before is not None:
        before_assistant = await session.get_one(Assistant, before)
        statement = statement.where(
            Assistant.created_at > before_assistant.created_at
            if order == "desc"
            else Assistant.created_at < before_assistant.created_at
        )
    assistants = list((await session.exec(statement.limit(limit))).all())
    kwargs = {}
    if len(assistants) > 0:
        kwargs["first_id"] = assistants[0].id
        kwargs["last_id"] = assistants[-1].id
    if len(assistants) == limit:
        after_assistant = await session.get_one(Assistant, assistants[-1].id)
        statement = (
            select(Assistant)
            .order_by(getattr(col(Assistant.created_at), order)())
            .where(
                Assistant.created_at < after_assistant.created_at
                if order == "desc"
                else Assistant.created_at > after_assistant.created_at
            )
        )
    return AsyncCursorPage[_Assistant](
        data=[await a.to_openai_model() for a in assistants], **kwargs
    )


@router.get("/assistants/{assistant_id}", response_model=_Assistant)
async def retrieve_assistant(
    assistant_id: str,
    session: SessionDependency,
) -> _Assistant:
    assistant = await session.get_one(Assistant, assistant_id)
    return await assistant.to_openai_model()


@router.post("/assistants/{assistant_id}", response_model=_Assistant)
async def update_assistant(
    assistant_id: str,
    params: RootModel[AssistantUpdateParams],
    session: SessionDependency,
) -> _Assistant:
    assistant = await session.get_one(Assistant, assistant_id)
    obj = cast(AssistantUpdateParams, params.model_dump(exclude_unset=True))
    for k, v in obj.items():
        setattr(assistant, k if k != "metadata" else "metadata_", v)
    await session.commit()
    return await assistant.to_openai_model()


@router.delete("/assistants/{assistant_id}", response_model=AssistantDeleted)
async def delete_assistant(
    assistant_id: str,
    session: SessionDependency,
) -> AssistantDeleted:
    assistant = await session.get_one(Assistant, assistant_id)
    await session.delete(assistant)
    await session.commit()
    return AssistantDeleted(id=assistant_id, deleted=True, object="assistant.deleted")
