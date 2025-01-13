from fastapi import APIRouter
from openai.pagination import AsyncPage
from openai.types import Model
from openai.types.model_deleted import ModelDeleted

from ..dependencies import ClientDependency, SettingsDependency

router = APIRouter(tags=["Models"])


@router.get("/models", response_model=AsyncPage[Model])
async def get_models(*, settings: SettingsDependency) -> AsyncPage[Model]:
    client = await settings.get_openai_client()
    return AsyncPage(
        data=[model for endpoint in client.endpoints for model in endpoint.models],
        object="list",
    )


@router.get("/models/{model:path}", response_model=Model)
async def retrieve_model(*, model: str, client: ClientDependency) -> Model:
    return await client.models.retrieve(model)


@router.delete("/models/{model:path}", response_model=ModelDeleted)
async def delete_model(*, model: str, client: ClientDependency) -> ModelDeleted:
    return await client.models.delete(model)
