from fastapi import APIRouter, Depends
from openai import AsyncOpenAI
from openai.types import Model

from ..models import get_current_active_user
from ._backend import get_openai

router = APIRouter(tags=["Models"], dependencies=[Depends(get_current_active_user)])


@router.get("/models")
async def get_models(
    openai: AsyncOpenAI = Depends(get_openai),
):
    return await openai.models.list()


@router.get("/models/{model:path}")
async def retrieve_model(
    model: str,
    openai: AsyncOpenAI = Depends(get_openai),
) -> Model:
    return await openai.models.retrieve(model)
