from typing import Annotated, Literal

from fastapi import Depends, HTTPException
from openai.types.beta.assistant import Assistant
from openai.types.beta.assistant_deleted import AssistantDeleted
from pydantic import Field
from sqlmodel import col, select

from ...models.assistant import Assistant as AssistantModel
from ...models.user import User, get_current_active_user
from ...requests import AssistantCreateParams, AssistantUpdateParams
from ...routing import OAIRouter
from ...schema import ListObject
from ...settings import Settings, get_settings

router = OAIRouter(tags=["Assistants"])


@router.post_assistants(response_model_exclude_unset=True)
async def create_assistant(
    params: AssistantCreateParams,
    settings: Settings = Depends(get_settings),
    user: User = Depends(get_current_active_user),
) -> Assistant:
    assistant_model = AssistantModel(
        creator=user,
        data=Assistant(
            id="dummy",
            created_at=0,
            object="assistant",
            **params.model_dump(exclude_unset=True),
        ),
    )
    settings.session.add(assistant_model)
    settings.session.commit()
    return assistant_model.data


@router.get_assistants
async def list_assistants(
    limit: Annotated[int, Field(ge=1, le=100)] = 20,
    order: Literal["asc", "desc"] = "desc",
    after: str | None = None,
    before: str | None = None,
    settings: Settings = Depends(get_settings),
    user: User = Depends(get_current_active_user),
) -> ListObject[Assistant]:
    statement = select(AssistantModel).order_by(
        getattr(col(AssistantModel.created_at), order)()
    )
    if after is not None:
        after_assistant = settings.session.get(AssistantModel, after)
        statement = statement.where(
            AssistantModel.created_at < after_assistant.created_at
            if order == "desc"
            else AssistantModel.created_at > after_assistant.created_at
        )
    if before is not None:
        before_assistant = settings.session.get(AssistantModel, before)
        statement = statement.where(
            AssistantModel.created_at > before_assistant.created_at
            if order == "desc"
            else AssistantModel.created_at < before_assistant.created_at
        )
    assistants = [a.data for a in settings.session.exec(statement.limit(limit)).all()]
    kwargs = {}
    if len(assistants) > 0:
        kwargs["first_id"] = assistants[0].id
        kwargs["last_id"] = assistants[-1].id
    if len(assistants) == limit:
        after_assistant = settings.session.get(AssistantModel, assistants[-1].id)
        statement = (
            select(AssistantModel)
            .order_by(getattr(col(AssistantModel.created_at), order)())
            .where(
                AssistantModel.created_at < after_assistant.created_at
                if order == "desc"
                else AssistantModel.created_at > after_assistant.created_at
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
    assistant = settings.session.get(AssistantModel, assistant_id)
    if assistant is None:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return assistant.data


@router.post("/assistants/{assistant_id}")
async def update_assistant(
    assistant_id: str,
    params: AssistantUpdateParams,
    settings: Settings = Depends(get_settings),
    user: User = Depends(get_current_active_user),
) -> Assistant:
    assistant = settings.session.get(AssistantModel, assistant_id)
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
    assistant = settings.session.get(AssistantModel, assistant_id)
    if assistant is None:
        raise HTTPException(status_code=404, detail="Assistant not found")
    if assistant.created_by != user.id:
        return AssistantDeleted(
            id=assistant_id, deleted=False, object="assistant.deleted"
        )
    settings.session.delete(assistant)
    settings.session.commit()
    return AssistantDeleted(id=assistant_id, deleted=True, object="assistant.deleted")
