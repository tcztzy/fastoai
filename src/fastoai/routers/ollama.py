from datetime import datetime
from typing import AsyncIterable, Generic, Literal, TypeVar, cast

from fastapi.responses import StreamingResponse
from ollama import AsyncClient as AsyncOllama
from openai import AsyncOpenAI
from openai.types import Model
from openai.types.beta.assistant import Assistant
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from pydantic import BaseModel

from ..requests import CompletionCreateParams
from ..routing import OAIRouter

T = TypeVar("T")

router = OAIRouter()


_ollama = AsyncOllama("http://localhost:11434/v1")

class OllamaModel(BaseModel):
    """Ollama model."""

    class Details(BaseModel):
        """Model details."""

        parent_model: str
        format: str
        family: str
        families: list[str] | None
        parameter_size: str
        quantization_level: str

    name: str
    model: str
    modified_at: datetime
    size: int
    digest: str
    details: Details



class ListObject(BaseModel, Generic[T]):
    """List container."""

    data: list[T]
    object: Literal["list"]
    first_id: str | None = None
    last_id: str | None = None
    has_more: bool = False


class OllamaTags(BaseModel):
    """Ollama tags."""

    models: list[OllamaModel]

    def to_openai_models(self) -> ListObject[Model]:
        """Convert to OpenAI models."""
        return ListObject[Model](
            object="list",
            data=[
                Model(
                    id=model.model,
                    created=int(model.modified_at.timestamp()),
                    object="model",
                    owned_by="ollama",
                )
                for model in self.models
            ],
        )

    def to_openai_assistants(self, reverse=True) -> ListObject[Assistant]:
        """Convert to OpenAI assistants."""
        sorted_assistants = sorted([
            Assistant(
                id=model.model,
                created_at=int(model.modified_at.timestamp()),
                object="assistant",
                name=model.name,
                model=model.model,
                tools=[],
            )
            for model in self.models
        ], key=lambda x: x.created_at, reverse=reverse)
        if len(sorted_assistants) > 0:
            first_id = sorted_assistants[0].id
            last_id = sorted_assistants[-1].id
        else:
            first_id = None
            last_id = None
        return ListObject[Assistant](object="list", data=sorted_assistants, first_id=first_id, last_id=last_id, has_more=False)


@router.get_models(response_model_exclude_unset=True)
async def get_models() -> ListObject[Model]:

    models = OllamaTags.model_validate(await _ollama.list())
    return models.to_openai_models()


@router.post_chat_completions
async def create_chat_completions(params: CompletionCreateParams):
    client = AsyncOpenAI(api_key="ollama", base_url="http://localhost:11434/v1")
    response = await client.chat.completions.create(**params.model_dump())
    if params.stream:

        async def _stream():
            async for chunk in cast(AsyncIterable[ChatCompletionChunk], response):
                yield f"data: {chunk.model_dump_json()}\n\n"
            else:
                yield "data: [DONE]\n\n"

        return StreamingResponse(_stream())
    return cast(ChatCompletion, response)


@router.get_assistants(response_model_exclude_unset=True)
async def get_assistants() -> ListObject[Assistant]:
    models = OllamaTags.model_validate(await _ollama.list())
    return models.to_openai_assistants()
