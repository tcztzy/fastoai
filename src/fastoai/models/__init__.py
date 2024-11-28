import inspect
import re
from itertools import chain
from pathlib import Path
from textwrap import indent

from openai._models import BaseModel
from pydantic.alias_generators import to_snake

from ..settings import get_settings
from ._metadata import WithMetadata as WithMetadata
from .user import APIKey, User

Imports = list[tuple[str, tuple[str, ...]]]


def _get_imports(src: str, module: list[str]) -> Imports:
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
    literal_pattern = re.compile(r"    (\w+): (Literal\[\s*(.+?)\s*\])")
    src = re.sub(
        literal_pattern,
        r"    \1: Annotated[\2, Field(sa_type=Enum(\3))]",
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
    source_file = inspect.getsourcefile(cls)
    if source_file is None:
        raise ValueError(f"Can't find source file for {cls.__name__}")
    src = Path(source_file).read_text()

    imports = _get_imports(src, cls.__module__.split("."))
    mo = re.search(r"^__all__ = (\[[\s\S]+?\])", src, re.MULTILINE)
    exports: list[str] = eval(mo.group(1) if mo is not None else "[]")
    exports.remove(cls.__name__)

    name = cls.__name__
    new_name = name
    relationships: list[str] = []
    typing_check_imports: list[tuple[str, tuple[str, ...]]] = []
    regular_imports = (
        [("typing" if mod.startswith("typing") else mod, imp) for (mod, imp) in imports]
        + [
            ("datetime", ("datetime",)),
            ("typing", ("TYPE_CHECKING", "Annotated", "ClassVar")),
            ("pydantic", ("RootModel", "field_serializer")),
            ("sqlalchemy.ext.mutable", ("MutableDict", "MutableList")),
            (
                "sqlmodel",
                ("JSON", "Column", "Enum", "Field", "Relationship", "SQLModel"),
            ),
            (".._types", ("as_sa_type",)),
            (".._utils", ("now", "random_id_with_prefix")),
            (".._metadata", ("WithMetadata",)),
        ]
        + ([(cls.__module__, tuple(exports))] if len(exports) else [])
    )
    match name:
        case "Assistant":
            typing_check_imports = [
                (".message", ("Message",)),
                (".thread", ("Thread",)),
            ]
            relationships = [
                'messages: list["Message"] = Relationship(back_populates="assistant")',
                'threads: list["Thread"] = Relationship(back_populates="assistant")',
            ]
        case "Message":
            regular_imports.extend(
                [
                    (".assistant", ("Assistant",)),
                    (".thread", ("Thread",)),
                    (".run", ("Run",)),
                ]
            )
            typing_check_imports = []
            relationships = [
                'assistant: Assistant | None = Relationship(back_populates="messages")',
                'thread: Thread = Relationship(back_populates="messages")',
                'run: Run | None = Relationship(back_populates="messages")',
            ]
        case "Thread":
            typing_check_imports = [
                (".message", ("Message",)),
                (".run", ("Run",)),
            ]
            relationships = [
                'messages: list["Message"] = Relationship(back_populates="thread")',
                'runs: list["Run"] = Relationship(back_populates="thread")',
            ]
        case "Run":
            regular_imports.extend(
                [(".assistant", ("Assistant",)), (".thread", ("Thread",))]
            )
            typing_check_imports = [
                (".message", ("Message",)),
                (".run_step", ("Step",)),
            ]
            relationships = [
                'assistant: Assistant = Relationship(back_populates="runs")',
                'thread: Thread = Relationship(back_populates="runs")',
                'steps: list["Step"] = Relationship(back_populates="run")',
                'messages: list["Message"] = Relationship(back_populates="run")',
            ]
        case "RunStep":
            new_name = "Step"
            regular_imports.extend(
                [
                    (".assistant", ("Assistant",)),
                    (".run", ("Run",)),
                    (".thread", ("Thread",)),
                ]
            )
            relationships = [
                'run: Run = Relationship(back_populates="steps")',
                'assistant: Assistant = Relationship(back_populates="steps")',
                'thread: Thread = Relationship(back_populates="steps")',
            ]
        case "FileObject":
            new_name = "File"
        case _:
            raise ValueError(f"Unsupported class {name}")
    header = "# Generated by FastOAI, DON'T EDIT\n" + _format_imports(regular_imports)
    if len(typing_check_imports):
        header += f"if TYPE_CHECKING:\n{indent(_format_imports(typing_check_imports), '    ')}\n"

    base = inspect.getsource(cls)
    base = base.replace(
        f"class {name}(BaseModel):",
        f"class {new_name}(SQLModel, table=True):",
    )
    prefix_map = {
        "Assistant": "asst_",
        "Thread": "thread_",
        "Message": "msg_",
        "Run": "run_",
        "RunStep": "step_",
        "FileObject": "file-",
    }
    base = re.sub(
        "    id: str",
        "    id: Annotated[str, Field(primary_key=True, default_factory="
        f'random_id_with_prefix("{prefix_map[name]}"))]',
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

    object_pattern = r"object: Literal\[\"([\w\.]+)\"\](\s*\"\"\"[\s\S]*?\"\"\"\s*)"
    mo = re.search(object_pattern, base)
    if mo is None:
        raise ValueError(f"Can't find object field for {name}")
    obj = mo.group(1)
    base = re.sub(object_pattern, r'object: ClassVar[Literal["\1"]] = "\1"\2', base)
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

    for f, o in re.findall(r"(\w+)_id: str( \| None = None)?", base):
        base = base.replace(
            f"{f}_id: str",
            f"{f}_id: Annotated[str{'| None' if o else ''}, Field(foreign_key='{f}.id')]",
        )
    dst_path = Path(__file__).parent / "generated" / f"{to_snake(cls.__name__)}.py"
    text = "\n".join((header, base))
    if len(relationships):
        text += "\n" + indent("\n".join(relationships), "    ") + "\n"
    dst_path.write_text(text)
    return obj


if get_settings().generate_models:
    from openai.types.beta.assistant import Assistant
    from openai.types.beta.thread import Thread
    from openai.types.beta.threads.message import Message
    from openai.types.beta.threads.run import Run
    from openai.types.beta.threads.runs.run_step import RunStep
    from openai.types.file_object import FileObject

    for cls in (Assistant, Message, Run, RunStep, Thread, FileObject):
        generate_module(cls)
    del Assistant, Message, Run, RunStep, Thread, FileObject
    _ruff_check(Path(__file__).parent / "generated")

from .generated.assistant import Assistant  # noqa: E402
from .generated.file_object import File  # noqa: E402
from .generated.message import Message  # noqa: E402
from .generated.run import Run  # noqa: E402
from .generated.run_step import Step  # noqa: E402
from .generated.thread import Thread  # noqa: E402

__all__ = [
    "APIKey",
    "User",
    "Assistant",
    "Message",
    "Run",
    "Step",
    "Thread",
    "File",
]
