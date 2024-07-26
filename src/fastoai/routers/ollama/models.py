from datetime import datetime

from fastapi import Depends
from ollama import AsyncClient as AsyncOllama
from openai.types import Model
from openai.types.beta.assistant import Assistant
from openai.types.model_deleted import ModelDeleted
from pydantic import BaseModel, Field

from ...models.user import User, get_current_active_user
from ...schema import ListObject
from ._backend import get_ollama


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
        sorted_assistants = sorted(
            [
                Assistant(
                    id=model.model,
                    created_at=int(model.modified_at.timestamp()),
                    object="assistant",
                    name=model.name,
                    model=model.model,
                    tools=[],
                )
                for model in self.models
            ],
            key=lambda x: x.created_at,
            reverse=reverse,
        )
        if len(sorted_assistants) > 0:
            first_id = sorted_assistants[0].id
            last_id = sorted_assistants[-1].id
        else:
            first_id = None
            last_id = None
        return ListObject[Assistant](
            data=sorted_assistants, first_id=first_id, last_id=last_id, has_more=False
        )


class OllamaModelInfo(BaseModel):
    """Ollama model info."""

    general_architecture: str = Field(alias="general.architecture")
    general_file_type: int = Field(alias="general.file_type")
    general_parameter_count: int = Field(alias="general.parameter_count")
    general_quantization_version: int = Field(alias="general.quantization_version")
    llama_attention_head_count: int = Field(alias="llama.attention.head_count")
    llama_attention_head_count_kv: int = Field(alias="llama.attention.head_count_kv")
    llama_attention_layer_norm_rms_epsilon: float = Field(
        alias="llama.attention.layer_norm_rms_epsilon"
    )
    llama_block_count: int = Field(alias="llama.block_count")
    llama_context_length: int = Field(alias="llama.context_length")
    llama_embedding_length: int = Field(alias="llama.embedding_length")
    llama_feed_forward_length: int = Field(alias="llama.feed_forward_length")
    llama_rope_dimension_count: int = Field(alias="llama.rope.dimension_count")
    llama_rope_freq_base: int = Field(alias="llama.rope.freq_base")
    llama_vocab_size: int = Field(alias="llama.vocab_size")
    tokenizer_ggml_bos_token_id: int = Field(alias="tokenizer.ggml.bos_token_id")
    tokenizer_ggml_eos_token_id: int = Field(alias="tokenizer.ggml.eos_token_id")
    tokenizer_ggml_merges: None = Field(default=None, alias="tokenizer.ggml.merges")
    tokenizer_ggml_model: str = Field(alias="tokenizer.ggml.model")
    tokenizer_ggml_pre: str | None = Field(None, alias="tokenizer.ggml.pre")
    tokenizer_ggml_token_type: None = Field(
        default=None, alias="tokenizer.ggml.token_type"
    )
    tokenizer_ggml_tokens: None = Field(default=None, alias="tokenizer.ggml.tokens")


class OllamaShow(BaseModel):
    """Ollama show."""

    license: str | None = None
    modelfile: str
    parameters: str | None = None
    template: str
    details: OllamaModel.Details
    model_info: OllamaModelInfo
    modified_at: datetime


async def list_models(
    user: User = Depends(get_current_active_user),
    ollama: AsyncOllama = Depends(get_ollama),
) -> ListObject[Model]:
    models = OllamaTags.model_validate(await ollama.list())
    return models.to_openai_models()


async def retrieve_model(
    model: str,
    user: User = Depends(get_current_active_user),
    ollama: AsyncOllama = Depends(get_ollama),
) -> Model:
    if ":" not in model:
        model = f"{model}:latest"
    result = OllamaShow.model_validate(await ollama.show(model))
    return Model(
        id=model,
        created=int(result.modified_at.timestamp()),
        object="model",
        owned_by="ollama",
    )


async def delete_model(
    model: str,
    user: User = Depends(get_current_active_user),
    ollama: AsyncOllama = Depends(get_ollama),
) -> ModelDeleted:
    """Delete a fine-tuned model."""
    result = await ollama.delete(model)
    return ModelDeleted(id=model, object="model", deleted=result["status"] == "success")
