from typing import Any, get_type_hints

from pydantic import BaseModel, create_model
from typing_extensions import is_typeddict


def create_model_from(type_: Any) -> type[BaseModel]:
    if not is_typeddict(type_):
        raise ValueError(f"Expected TypedDict, got {type_}")
    return create_model(
        type_.__name__,
        **{
            fn: (t, ... if fn in type_.__required_keys__ else None)
            for fn, t in get_type_hints(type_, include_extras=True).items()
        },
    )
