import inspect
import re
from itertools import chain
from pathlib import Path

from openai._models import BaseModel
from openai.types.beta.assistant import Assistant
from pydantic.alias_generators import to_snake

from ..settings import settings
from .user import User, get_current_active_user

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


def _id_field(src: str):
    id_pattern = re.compile(r"    id: str\n    (\"\"\"[\s\S]*?\"\"\")\n\n")
    id_doc = re.search(id_pattern, src).group(1)
    src = re.sub(id_pattern, "", src)
    return src, id_doc


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


def _construct_table_model(name: str, id_doc: str):
    return f"""\n\nclass {name}({name}Base, SQLModel, table=True):
    id: Annotated[str, Field(primary_key=True)]
    {id_doc}
"""


def _construct_public_model(
    name: str,
    id_doc: str,
    metadata_field: str,
    object_field: str,
    datetime_fields: list[str],
):
    public = f"\n\nclass {name}Public({name}Base):\n    id: str\n    {id_doc}\n"
    if metadata_field:
        public += f"\n    {metadata_field.strip()}\n"
    if object_field:
        public += f"\n    {object_field.strip()}\n"
    if len(datetime_fields):
        public += f"""
    @field_serializer({', '.join(f'"{f}"' for f in datetime_fields)})
    def serialize_datetime(self, dt: Optional[datetime], _):
        if dt is None:
            return None
        return int(dt.timestamp())
"""
    return public


def _ruff_check(path: Path):
    import os
    import subprocess

    from ruff.__main__ import find_ruff_bin

    ruff = os.fsdecode(find_ruff_bin())
    argv = ["check", "--fix", path]

    subprocess.run([ruff, *argv])


def generate_types(imports: Imports):
    path = Path(__file__).parent / "generated" / "types.py"
    path.write_text(
        "# Generated by FastOAI, DON'T EDIT\n"
        + _format_imports(imports)
        + "\n\n__all__ = [\n    'BaseModelType',\n    'MutableBaseModel',\n]\n"
    )
    _ruff_check(path)


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
            ("sqlalchemy.ext.mutable", ("MutableList",)),
            ("sqlmodel", ("JSON", "Enum", "Field", "SQLModel")),
            (".._types", ("BaseModelType", "MutableBaseModel", "as_sa_type")),
        ]
        + ([(cls.__module__, exports)] if len(exports) else [])
    )

    name = cls.__name__
    base = inspect.getsource(cls)
    base = base.replace(f"class {name}(BaseModel):", f"class {name}Base(BaseModel):")
    base, id_doc = _id_field(base)
    metadata_pattern = re.compile(r"    metadata: .+\s*\"\"\"[\s\S]*?\"\"\"\n\n")
    if (mo := metadata_pattern.search(base)) is not None:
        metadata_field = mo.group()
        base = re.sub(metadata_pattern, "", base)
    else:
        metadata_field = ""

    object_pattern = r"    object: Literal\[\"[\w\.]+\"\]\s*\"\"\"[\s\S]*?\"\"\"\n\n"
    object_field = re.search(object_pattern, base).group()
    base = re.sub(object_pattern, "", base)
    base = re.sub(
        r"(\w+): (List\[.+?\])",
        r"\1: Annotated[\2, Field(sa_type=as_sa_type(\2))]",
        base,
    )
    base = re.sub(
        r"(\w+): Optional\[(List\[.+?\])\]",
        r"\1: Annotated[Optional[\2], Field(sa_type=as_sa_type(\2), nullable=True)]",
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
            r"\1: Annotated[Optional[\2], Field(sa_type=as_sa_type(\2), nullable=True)]",
            base,
        )

    base = base.replace("_at: int", "_at: datetime")
    base = base.replace("_at: Optional[int]", "_at: Optional[datetime]")
    datetime_fields = re.findall(r"(\w+_at)(?=:)", base)

    table = _construct_table_model(name, id_doc)
    public = _construct_public_model(
        name, id_doc, metadata_field, object_field, datetime_fields
    )
    dst_path = Path(__file__).parent / "generated" / f"{to_snake(cls.__name__)}.py"
    dst_path.write_text(header + base + table + public)
    _ruff_check(dst_path)


if settings.generate_models:
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
    "User",
    "get_current_active_user",
    "Assistant",
    "Message",
    "Run",
    "RunStep",
    "Thread",
    "FileObject",
]
