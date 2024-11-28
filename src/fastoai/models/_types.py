from typing import (
    Annotated,
    Any,
    Literal,
    Self,
    Union,
    get_args,
    get_origin,
)

import sqlalchemy as sa
from pydantic import BaseModel, RootModel
from sqlalchemy.ext.mutable import Mutable, MutableList
from sqlmodel import JSON, Enum, String


class BaseModelType(sa.types.TypeDecorator[BaseModel]):
    """This is a custom SQLAlchemy field that allows easy serialization between database JSONB types and Pydantic models"""

    impl = JSON

    def __init__(
        self,
        pydantic_model_class: type[BaseModel],
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.pydantic_model_class = pydantic_model_class

    def process_bind_param(self, value: BaseModel | list[BaseModel] | None, _):  # type: ignore
        """Convert python native type to JSON string before storing in the database"""
        match value:
            case None:
                return None
            case list():
                return [v.model_dump(mode="json") for v in value]
            case BaseModel():
                return value.model_dump(mode="json")
            case _:
                return value

    def process_result_value(self, value: Any, _):  # type: ignore
        """Convert JSON string back to Python object after retrieving from the database"""
        v = None if value is None else self.pydantic_model_class.model_validate(value)
        return v.root if isinstance(v, RootModel) else v


class UnionModelType(sa.types.TypeDecorator[RootModel]):
    """This is a custom SQLAlchemy field that allows easy serialization between database JSONB types and Pydantic models"""

    impl = String

    def __init__(
        self,
        pydantic_model_class: type[RootModel],
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.pydantic_model_class = pydantic_model_class

    def process_bind_param(self, value: RootModel | list[BaseModel] | None, _):  # type: ignore
        """Convert python native type to JSON string before storing in the database"""
        match value:
            case None:
                return None
            case list():
                return [v.model_dump(mode="json") for v in value]
            case BaseModel():
                return value.model_dump(mode="json")
            case _:
                return value

    def process_result_value(self, value: Any, _):  # type: ignore
        """Convert JSON string back to Python object after retrieving from the database"""
        return (
            None
            if value is None
            else self.pydantic_model_class.model_validate(value).root
        )


class MutableBaseModel(Mutable, BaseModel):
    """This is a hack that is intended to allow SQLAlchemy detect changes in JSON field that is a pydantic model"""

    def __setattr__(self, name: str, value: Any) -> None:
        """Allows SQLAlchmey Session to track mutable behavior"""
        super().__setattr__(name, value)
        self.changed()

    @classmethod
    def coerce(cls, key: str, value: Any) -> Self | None:
        """Convert JSON to pydantic model object allowing for mutable behavior"""
        if isinstance(value, cls) or value is None:
            return value

        if isinstance(value, str):
            return cls.model_validate_json(value)

        if isinstance(value, dict):
            return cls.model_validate(value)

        return super().coerce(key, value)


def _is_subclass_of_base_model(t: type):
    try:
        return issubclass(t, BaseModel)
    except TypeError:
        return False


def _is_base_model(t: type):
    def _is_union_of_base_models(t: type):
        return get_origin(t) is Union and any(
            issubclass(a, BaseModel) for a in get_args(t)
        )

    return (
        _is_subclass_of_base_model(t)
        or _is_union_of_base_models(t)
        or (get_origin(t) is Annotated and _is_base_model(get_args(t)[0]))
    )


def as_sa_type(type_: type) -> type:
    try:
        if issubclass(type_, BaseModel):
            return type(type_.__name__, (type_, MutableBaseModel), {}).as_mutable(  # type: ignore
                BaseModelType(type_)
            )
    except TypeError:
        pass

    origin = get_origin(type_)
    args = get_args(type_)
    t: type = args[0]

    if origin is Annotated:
        return as_sa_type(t)

    if origin is list and _is_base_model(t):
        return MutableList[t].as_mutable(BaseModelType(RootModel[type_]))  # type: ignore

    if origin is Union:
        new_type = RootModel[type_]
        return type(new_type.__name__, (new_type, MutableBaseModel), {}).as_mutable(  # type: ignore
            UnionModelType(new_type)
        )

    if origin is Literal:
        return Enum(*args)  # type: ignore

    raise ValueError(f"Unsupported type {type_}")
