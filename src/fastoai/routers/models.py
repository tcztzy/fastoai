from fastapi import Depends
from ollama import AsyncClient as AsyncOllama
from openai import AsyncOpenAI
from openai.types import Model
from openai.types.model_deleted import ModelDeleted

from ..models import User, get_current_active_user
from ..routing import OAIRouter
from ._backend import get_ollama, get_openai

router = OAIRouter(tags=["Models"])


@router.get_models
async def get_models(
    user: User = Depends(get_current_active_user),
    openai: AsyncOpenAI = Depends(get_openai),
):
    return await openai.models.list()


@router.get("/models/{model:path}")
async def retrieve_model(
    model: str,
    user: User = Depends(get_current_active_user),
    openai: AsyncOpenAI = Depends(get_openai),
) -> Model:
    return await openai.models.retrieve(model)


@router.delete("/models/{model:path}")
async def delete_model(
    model: str,
    user: User = Depends(get_current_active_user),
    ollama: AsyncOllama = Depends(get_ollama),
) -> ModelDeleted:
    """Delete a fine-tuned model."""
    result = await ollama.delete(model)
    return ModelDeleted(id=model, object="model", deleted=result["status"] == "success")
