from typing import Any, Generic, TypeVar, get_args

import orjson
from openai.types.beta.assistant_response_format_option import (
    AssistantResponseFormatOption,
)
from openai.types.beta.assistant_tool import AssistantTool
from openai.types.shared_params import (
    ResponseFormatJSONObject,
    ResponseFormatJSONSchema,
    ResponseFormatText,
)
from pydantic import BaseModel

T = TypeVar("T")
Metadata = dict[str, str]


class Object(BaseModel, Generic[T]):
    object: str
    data: T


class KnownObject(BaseModel):
    object: (
        Object[Metadata]
        | Object[list[AssistantTool]]
        | Object[AssistantResponseFormatOption]
    )


def json_serializer(model: Any) -> str | None:
    match model:
        case BaseModel():
            return model.model_dump_json()
        case dict():
            return Object[Metadata](object="metadata", data=model).model_dump_json()
        case list():
            if all(isinstance(tool, get_args(AssistantTool)) for tool in model):
                return Object[list[AssistantTool]](
                    object="list[AssistantTool]", data=model
                ).model_dump_json()
            else:
                raise ValueError(f"Invalid model type:{type(model)} value={model}")
        case (
            "auto"
            | ResponseFormatText()
            | ResponseFormatJSONObject()
            | ResponseFormatJSONSchema()
        ):
            return Object[AssistantResponseFormatOption](
                object="AssistantResponseFormatOption", data=model
            ).model_dump_json()
        case None:
            return None
        case _:
            raise ValueError(f"Invalid model type:{type(model)} value={model}")


def json_deserializer(data: str) -> Any:
    # Try deserializing with each model until one works.
    # This is a pretty ugly solution but the deserialization seems to only be possible and reliable at an engine level
    # and we need to know the model to deserialize it properly
    # We would need to keep adding more of these if we add more models with JSON fields.
    json_data = orjson.loads(data)
    match json_data.get("object"):
        case "metadata" | "list[AssistantTool]" | "AssistantResponseFormatOption":
            return KnownObject.model_validate({"object": json_data}).object.data
        case None:
            return json_data
