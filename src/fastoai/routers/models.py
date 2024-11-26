from fastapi import APIRouter
from openai.types import Model

from ..dependencies import OpenAIDependency

router = APIRouter(tags=["Models"])


@router.get("/models")
async def get_models(*, openai: OpenAIDependency):
    return await openai.models.list()


@router.get("/models/{model:path}")
async def retrieve_model(*, model: str, openai: OpenAIDependency) -> Model:
    return await openai.models.retrieve(model)
