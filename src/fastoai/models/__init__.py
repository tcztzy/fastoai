import inspect
import re
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING

from openai._models import BaseModel
from pydantic.alias_generators import to_snake

from ._metadata import WithMetadata as WithMetadata
from .user import APIKey, User

Imports = list[tuple[str, tuple[str, ...]]]


def _get_imports(src: str, module: tuple[str, ...]) -> Imports:
    imports = []
    for m in re.finditer(r"^from (.*) import (.*)$", src, re.MULTILINE):
        mod = m.group(1)
        if mod.startswith("."):
            mod = (
                ".".join(module[: len(module) - mod.count(".")])
                + "."
                + mod.replace(".", "")
            )
        imports.append((mod, tuple(m.group(2).split(", "))))
    return imports


def _format_imports(imports: Imports):
    return (
        "\n".join(f"from {mod} import {', '.join(imp)}" for mod, imp in imports) + "\n"
    )


def _literal_string_as_enum(src: str):
    literal_pattern = re.compile(
        r"    (\w+): (Literal\[\s*(.+?)\s*\])\s*(\"\"\"[\s\S]*?\"\"\")\n\n"
    )
    src = re.sub(
        literal_pattern,
        r"    \1: Annotated[\2, Field(sa_type=Enum(\3))]\n    \4\n",
        src,
    )
    return src


def _ruff_check(path: Path):
    import os
    import subprocess

    from ruff.__main__ import find_ruff_bin

    ruff = os.fsdecode(find_ruff_bin())
    argv = ["check", "--fix", path]

    subprocess.run([ruff, *argv])


def generate_module(cls: type[BaseModel]):
    src_path = Path(inspect.getsourcefile(cls))
    src = src_path.read_text()

    imports = _get_imports(src, cls.__module__.split("."))
    exports: list[str] = eval(
        re.search(r"^__all__ = (\[[\s\S]+?\])", src, re.MULTILINE).group(1)
    )
    exports.remove(cls.__name__)

    header = "# Generated by FastOAI, DON'T EDIT\n" + _format_imports(
        [("typing" if mod.startswith("typing") else mod, imp) for (mod, imp) in imports]
        + [
            ("datetime", ("datetime",)),
            ("typing", ("Annotated",)),
            ("pydantic", ("RootModel", "field_serializer")),
            ("sqlalchemy.ext.mutable", ("MutableDict", "MutableList")),
            ("sqlmodel", ("JSON", "Column", "Enum", "Field", "SQLModel")),
            (".._types", ("as_sa_type",)),
            (".._utils", ("now", "random_id_with_prefix")),
            (".._metadata", ("WithMetadata",)),
        ]
        + ([(cls.__module__, exports)] if len(exports) else [])
    )

    name = cls.__name__
    base = inspect.getsource(cls)
    base = base.replace(
        f"class {name}(BaseModel):", f"class {name}(SQLModel, table=True):"
    )
    if cls is FileObject:
        base = re.sub(
            "id:",
            '__tablename__ = "file"\n\n    id:',
            base,
        )
    prefix_map = {
        Assistant: "asst_",
        Thread: "thread_",
        Message: "msg_",
        Run: "run_",
        RunStep: "step_",
        FileObject: "file-",
    }
    base = re.sub(
        "id: str",
        "id: Annotated[str, Field(primary_key=True, default_factory="
        f'random_id_with_prefix("{prefix_map[cls]}"))]',
        base,
    )
    metadata_pattern = re.compile(r"metadata: (.+) = None(\s*\"\"\"[\s\S]*?\"\"\"\s*)")
    if metadata_pattern.search(base) is not None:
        base = re.sub(
            metadata_pattern,
            "",
            base,
        )
        base = re.sub(
            "class (.+?)\\(SQLModel, table=True\\):",
            "class \\1(WithMetadata, table=True):",
            base,
        )

    object_pattern = r"object: Literal\[\"([\w\.]+)\"\]\s*\"\"\"[\s\S]*?\"\"\"\s*"
    obj = re.search(object_pattern, base).group(1)
    base = re.sub(object_pattern, "", base)
    base = re.sub(
        r"(\w+): L(ist\[.+?\])",
        r"\1: Annotated[l\2, Field(sa_type=as_sa_type(l\2))]",
        base,
    )
    base = re.sub(
        r"(\w+): Optional\[L(ist\[.+?\])\]",
        r"\1: Annotated[l\2 | None, Field(sa_type=as_sa_type(l\2), nullable=True)]",
        base,
    )
    base = _literal_string_as_enum(base)

    need_types = [
        imp
        for (mod, imp) in imports
        if mod not in ["typing", "typing_extensions", "openai._models"]
    ] + ([exports] if len(exports) else [])
    for i in chain(*need_types):
        base = re.sub(
            rf"(\w+): ({i})",
            r"\1: Annotated[\2, Field(sa_type=as_sa_type(\2))]",
            base,
        )
        base = re.sub(
            rf"(\w+): Optional\[({i})\]",
            r"\1: Annotated[\2 | None, Field(sa_type=as_sa_type(\2), nullable=True)]",
            base,
        )

    base = base.replace(
        "_at: int", "_at: Annotated[datetime, Field(default_factory=now)]"
    )
    base = base.replace("_at: Optional[int]", "_at: datetime | None")
    datetime_fields = re.findall(r"(\w+_at)(?=:)", base)

    if len(datetime_fields):
        optional = len(datetime_fields) > 1
        opt = " | None" if optional else ""
        base += f"""
    @field_serializer({', '.join(f'"{f}"' for f in datetime_fields)})
    def serialize_datetime(self, dt: datetime{opt}, _) -> int{opt}:
        return int(dt.timestamp()){" if dt is not None else None" if optional else ""}
"""
    base = re.sub(r"Optional\[(\w+)\]", r"\1 | None", base)
    dst_path = Path(__file__).parent / "generated" / f"{to_snake(cls.__name__)}.py"
    dst_path.write_text(header + base)
    _ruff_check(dst_path)
    return obj


if TYPE_CHECKING:
    from openai.types.beta.assistant import Assistant
    from openai.types.beta.thread import Thread
    from openai.types.beta.threads.message import Message
    from openai.types.beta.threads.run import Run
    from openai.types.beta.threads.runs.run_step import RunStep
    from openai.types.file_object import FileObject

    for cls in (Assistant, Message, Run, RunStep, Thread, FileObject):
        generate_module(cls)

from .generated.assistant import Assistant  # noqa: E402
from .generated.file_object import FileObject  # noqa: E402
from .generated.message import Message  # noqa: E402
from .generated.run import Run  # noqa: E402
from .generated.run_step import RunStep  # noqa: E402
from .generated.thread import Thread  # noqa: E402

__all__ = [
    "APIKey",
    "User",
    "get_current_active_user",
    "Assistant",
    "Message",
    "Run",
    "RunStep",
    "Thread",
    "FileObject",
]
