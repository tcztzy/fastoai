from typing import Annotated, Any, Self

from pydantic.json_schema import (
    DEFAULT_REF_TEMPLATE,
    GenerateJsonSchema,
    JsonSchemaMode,
    WithJsonSchema,
)
from sqlalchemy.ext.mutable import MutableDict
from sqlmodel import JSON, Field, SQLModel


class WithMetadata(SQLModel):
    metadata_: Annotated[
        dict[
            Annotated[str, Field(max_length=64)],
            Annotated[str, Field(max_length=512)] | Any,
        ]
        | None,
        Field(
            alias="metadata",
            sa_type=MutableDict.as_mutable(JSON),  # type: ignore
            sa_column_kwargs={"name": "metadata"},
        ),
        WithJsonSchema({"type": "object"}),
    ] = None
    """Set of 16 key-value pairs that can be attached to an object.

    This can be useful for storing additional information about the object in a
    structured format. Keys can be a maximum of 64 characters long and values can be
    a maximum of 512 characters long.
    """

    def __init__(self, **kwargs):
        if "metadata" in kwargs:
            kwargs["metadata_"] = kwargs.pop("metadata")
        return super().__init__(**kwargs)

    @classmethod
    def model_validate(
        cls,
        obj: Any,
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: dict[str, Any] | None = None,
        update: dict[str, Any] | None = None,
    ) -> Self:
        if "metadata" in obj:
            obj["metadata_"] = obj.pop("metadata")
        return super().model_validate(
            obj,
            strict=strict,
            from_attributes=from_attributes,
            context=context,
            update=update,
        )

    def model_dump(self, by_alias: bool = False, **kwargs) -> dict[str, Any]:
        result = super().model_dump(**kwargs)
        if by_alias and "metadata_" in result:
            result["metadata"] = result.pop("metadata_")
        return result

    def model_dump_json(self, by_alias: bool = False, **kwargs) -> str:
        result = super().model_dump_json(**kwargs)
        if by_alias and "metadata_" in result:
            result.replace("metadata_", "metadata")
        return result

    @classmethod
    def model_json_schema(
        cls,
        by_alias: bool = False,
        ref_template: str = DEFAULT_REF_TEMPLATE,
        schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
        mode: JsonSchemaMode = "validation",
    ) -> dict[str, Any]:
        schema = super().model_json_schema(
            by_alias=by_alias,
            ref_template=ref_template,
            schema_generator=schema_generator,
            mode=mode,
        )
        if by_alias and "metadata_" in schema["properties"]:
            schema["properties"]["metadata"] = schema["properties"].pop("metadata_")
        return schema
