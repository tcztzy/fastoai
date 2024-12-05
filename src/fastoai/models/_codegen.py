import ast
import inspect
from collections import defaultdict
from pathlib import Path
from types import ModuleType
from typing import cast

from pydantic.alias_generators import to_snake

ID_PREFIXES = {
    "FileObject": "file-",
    "Assistant": "asst_",
    "RunStep": "step_",
    "Message": "msg_",
}

CLS_TO_TABLE = {
    "FileObject": "file",
    "RunStep": "step",
}
TABLE_TO_CLS = {
    "file": "FileObject",
    "step": "RunStep",
}


def ruff_check(path: Path):
    import os
    import subprocess

    from ruff.__main__ import find_ruff_bin

    ruff = os.fsdecode(find_ruff_bin())
    argv = ["check", "--fix", path]

    subprocess.run([ruff, *argv])


def Annotated(type_, *args) -> ast.Subscript:
    return ast.Subscript(
        value=ast.Name(id="Annotated", ctx=ast.Load()),
        slice=ast.Tuple(
            elts=[type_, *args],
            ctx=ast.Load(),
        ),
        ctx=ast.Load(),
    )


def Field(*args, **kwargs) -> ast.Call:
    return ast.Call(
        func=ast.Name(id="Field", ctx=ast.Load()),
        args=list(args),
        keywords=[ast.keyword(arg=k, value=v) for k, v in kwargs.items()],
    )


def _fix_id(class_def: ast.ClassDef):
    id_field = cast(ast.AnnAssign, class_def.body[0])
    id_field.annotation = Annotated(
        id_field.annotation,
        Field(
            primary_key=ast.Constant(value=True),
            default_factory=ast.Call(
                func=ast.Name(id="random_id_with_prefix", ctx=ast.Load()),
                args=[
                    ast.Constant(
                        value=ID_PREFIXES.get(
                            class_def.name, class_def.name.lower() + "_"
                        )
                    )
                ],
                keywords=[],
            ),
        ),
    )


def _fix_literal(class_def: ast.ClassDef):
    for n in class_def.body:
        if (
            isinstance(n, ast.AnnAssign)
            and isinstance(n.annotation, ast.Subscript)
            and isinstance(n.annotation.value, ast.Name)
            and n.annotation.value.id == "Literal"
        ):
            t = n.annotation
            f = Field(
                sa_type=ast.Call(
                    func=ast.Name(id="Enum", ctx=ast.Load()),
                    args=[
                        elt
                        for elt in cast(ast.Tuple, cast(ast.Subscript, t).slice).elts
                    ],
                    keywords=[],
                )
            )
            n.annotation = Annotated(t, f)


def _get_object_literal(n: ast.ClassDef) -> str:
    object_field = next(
        (
            a
            for a in n.body
            if isinstance(a, ast.AnnAssign)
            and isinstance(a.target, ast.Name)
            and a.target.id == "object"
        )
    )
    n.body.remove(object_field)
    return cast(
        str,
        cast(ast.Constant, cast(ast.Subscript, object_field.annotation).slice).value,
    )


def _fix_optional(class_def: ast.ClassDef):
    for stmt in class_def.body:
        if (
            isinstance(stmt, ast.AnnAssign)
            and isinstance(ann := stmt.annotation, ast.Subscript)
            and isinstance(ann.value, ast.Name)
            and ann.value.id == "Optional"
        ):
            if isinstance(ann.slice, ast.Name) and ann.slice.id in {
                "str",
                "int",
                "float",
                "bool",
            }:
                stmt.annotation = ast.BinOp(
                    left=ann.slice,
                    op=ast.BitOr(),
                    right=ast.Name(id="None", ctx=ast.Load()),
                )
            else:
                if (
                    isinstance(ann.slice, ast.Subscript)
                    and isinstance(ann.slice.value, ast.Name)
                    and ann.slice.value.id == "List"
                ):
                    ann.slice.value.id = "list"
                t = ast.BinOp(
                    left=ann.slice,
                    op=ast.BitOr(),
                    right=ast.Name(id="None", ctx=ast.Load()),
                )
                as_sa_type_call = ast.Call(
                    func=ast.Name(id="as_sa_type", ctx=ast.Load()),
                    args=[ann.slice],
                    keywords=[],
                )
                f = Field(
                    sa_type=as_sa_type_call,
                    nullable=ast.Constant(value=True),
                )
                stmt.annotation = Annotated(t, f)


def _fix_list(class_def: ast.ClassDef):
    for stmt in class_def.body:
        if (
            isinstance(ann_assign := stmt, ast.AnnAssign)
            and isinstance(ann := ann_assign.annotation, ast.Subscript)
            and isinstance(ann.value, ast.Name)
        ):
            if ann.value.id == "List":
                ann.value.id = "list"
                as_sa_type_call = ast.Call(
                    func=ast.Name(id="as_sa_type", ctx=ast.Load()),
                    args=[ann],
                    keywords=[],
                )
                ann_assign.annotation = Annotated(
                    ann,
                    Field(
                        default_factory=ast.Name("list", ctx=ast.Load()),
                        sa_type=as_sa_type_call,
                    ),
                )


def _fix_name(class_def: ast.ClassDef):
    for stmt in class_def.body:
        if (
            isinstance(ann_assign := stmt, ast.AnnAssign)
            and isinstance(ann := ann_assign.annotation, ast.Name)
            and ann.id not in {"str", "int", "float", "bool"}
        ):
            as_sa_type_call = ast.Call(
                func=ast.Name(id="as_sa_type", ctx=ast.Load()),
                args=[ann],
                keywords=[],
            )
            ann_assign.annotation = Annotated(
                ann,
                Field(
                    sa_type=as_sa_type_call,
                ),
            )


def Optional(type_) -> ast.BinOp:
    return ast.BinOp(
        left=type_,
        op=ast.BitOr(),
        right=ast.Name(id="None", ctx=ast.Load()),
    )


def _fix_timestamp(class_def: ast.ClassDef):
    timestamps = []
    optional = False
    for stmt in class_def.body:
        if (
            isinstance(ann_assign := stmt, ast.AnnAssign)
            and isinstance(ann_assign.target, ast.Name)
            and ann_assign.target.id.endswith("_at")
        ):
            if isinstance(ann_assign.annotation, ast.Name):
                ann_assign.annotation = Annotated(
                    ast.Name(id="datetime", ctx=ast.Load()),
                    Field(default_factory=ast.Name(id="now", ctx=ast.Load())),
                )
            else:
                ann_assign.annotation = Optional(
                    ast.Name(id="datetime", ctx=ast.Load())
                )
                optional = True
            timestamps.append(ann_assign.target.id)
    if timestamps:
        name_int = ast.Name(id="int", ctx=ast.Load())
        name_datetime = ast.Name(id="datetime", ctx=ast.Load())
        serializor = ast.FunctionDef(
            name="serialize_datetime",
            args=ast.arguments(
                posonlyargs=[],
                args=[
                    ast.arg("self"),
                    ast.arg(
                        arg="dt",
                        annotation=Optional(name_datetime)
                        if optional
                        else name_datetime,
                    ),
                ],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[],
            ),
            body=[
                *(
                    [
                        ast.If(
                            test=ast.Compare(
                                left=ast.Name(id="dt", ctx=ast.Load()),
                                ops=[ast.Is()],
                                comparators=[ast.Name(id="None", ctx=ast.Load())],
                            ),
                            body=[ast.Return(value=ast.Constant(value=None))],
                            orelse=[],
                        )
                    ]
                    if optional
                    else []
                ),
                ast.Return(
                    value=ast.Call(
                        func=name_int,
                        args=[
                            ast.Call(
                                func=ast.Attribute(
                                    value=ast.Name(id="dt", ctx=ast.Load()),
                                    attr="timestamp",
                                    ctx=ast.Load(),
                                ),
                                args=[],
                                keywords=[],
                            )
                        ],
                        keywords=[],
                    )
                ),
            ],
            decorator_list=[
                ast.Call(
                    func=ast.Name(id="field_serializer", ctx=ast.Load()),
                    args=[ast.Constant(value=f) for f in timestamps],
                    keywords=[],
                )
            ],
            returns=Optional(name_int) if optional else name_int,
            type_params=[],
        )
        class_def.body.append(serializor)


def _to_openai_model(
    openai_model_name: str, object_literal: str
) -> ast.AsyncFunctionDef:
    return ast.AsyncFunctionDef(
        name="to_openai_model",
        args=ast.arguments(
            posonlyargs=[],
            args=[ast.arg(arg="self")],
            kwonlyargs=[],
            kw_defaults=[],
            defaults=[],
        ),
        body=[
            ast.Assign(
                targets=[ast.Name(id="value", ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id="self", ctx=ast.Load()),
                        attr="model_dump",
                        ctx=ast.Load(),
                    ),
                    args=[],
                    keywords=[ast.keyword("by_alias", ast.Constant(True))],
                ),
            ),
            ast.Assign(
                targets=[
                    ast.Subscript(
                        value=ast.Name(id="value", ctx=ast.Load()),
                        slice=ast.Constant(value="object"),
                        ctx=ast.Store(),
                    )
                ],
                value=ast.Constant(value=object_literal),
            ),
            ast.Return(
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id=openai_model_name, ctx=ast.Load()),
                        attr="model_validate",
                        ctx=ast.Load(),
                    ),
                    args=[ast.Name(id="value", ctx=ast.Load())],
                    keywords=[],
                )
            ),
        ],
        decorator_list=[],
        returns=ast.Name(id=openai_model_name, ctx=ast.Load()),
        type_params=[],
    )


def generate_module(module: ModuleType) -> ast.Module:
    tree = ast.parse(inspect.getsource(module))
    all_defs = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "__all__"
    )
    all_defs_index = tree.body.index(all_defs)
    imports = cast(list[ast.ImportFrom], tree.body[:all_defs_index])
    body = tree.body[all_defs_index + 1 :]
    for n in imports:
        match n:
            case n if n.module == "typing_extensions":
                n.module = "typing"
            case n if n.level != 0:
                n.module = ".".join(
                    (module.__name__.split("."))[: -n.level] + [n.module or ""]
                )
                n.level = 0
    imports.extend(
        [
            ast.ImportFrom("datetime", [ast.alias("datetime")], 0),
            ast.ImportFrom("typing", [ast.alias("Annotated")], 0),
            ast.ImportFrom("sqlalchemy.ext.asyncio", [ast.alias("AsyncAttrs")], 0),
            ast.ImportFrom(
                "sqlmodel",
                [
                    ast.alias("SQLModel"),
                    ast.alias("Enum"),
                    ast.alias("Field"),
                    ast.alias("Relationship"),
                ],
                0,
            ),
            ast.ImportFrom("pydantic", [ast.alias("field_serializer")], 0),
            ast.ImportFrom("_metadata", [ast.alias("WithMetadata")], 2),
            ast.ImportFrom("_types", [ast.alias("as_sa_type")], 2),
            ast.ImportFrom(
                "_utils", [ast.alias("now"), ast.alias("random_id_with_prefix")], 2
            ),
        ]
    )
    class_def = cast(ast.ClassDef, body.pop())

    class_def.body = [
        stmt for stmt in class_def.body if isinstance(stmt, ast.AnnAssign)
    ]
    metadata_field = next(
        (
            a
            for a in class_def.body
            if isinstance(a, ast.AnnAssign)
            and isinstance(a.target, ast.Name)
            and a.target.id == "metadata"
        ),
        None,
    )
    if metadata_field:
        class_def.body.remove(metadata_field)
    class_def.bases = [
        ast.Name(id="AsyncAttrs", ctx=ast.Load()),
        ast.Name(
            id="WithMetadata" if metadata_field else "SQLModel",
            ctx=ast.Load(),
        ),
    ]
    class_def.keywords = [ast.keyword(arg="table", value=ast.Constant(value=True))]
    _fix_id(class_def)
    if tablename := CLS_TO_TABLE.get(class_def.name):
        class_def.body.insert(
            0,
            ast.Assign(
                targets=[ast.Name(id="__tablename__", ctx=ast.Store())],
                value=ast.Constant(value=tablename),
            ),
        )
    imports.append(
        ast.ImportFrom(
            module.__name__,
            [ast.alias(class_def.name, f"_{class_def.name}")],
            0,
        )
    )
    object_literal = _get_object_literal(class_def)
    class_def.body.append(_to_openai_model(f"_{class_def.name}", object_literal))
    _fix_literal(class_def)
    _fix_optional(class_def)
    _fix_list(class_def)
    _fix_name(class_def)
    _fix_timestamp(class_def)
    for node in body:
        if isinstance(node, ast.ClassDef):
            imports.append(
                ast.ImportFrom(
                    module.__name__,
                    [ast.alias(node.name)],
                    0,
                )
            )
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.annotation, ast.Subscript):
                imports.append(
                    ast.ImportFrom(
                        module.__name__,
                        [ast.alias(cast(ast.Name, node.annotation.value).id)],
                        0,
                    )
                )
            elif (
                isinstance(node.annotation, ast.Name)
                and node.annotation.id == "TypeAlias"
            ):
                imports.append(
                    ast.ImportFrom(
                        module.__name__,
                        [ast.alias(cast(ast.Name, node.target).id)],
                        0,
                    )
                )
    tree.body = imports + tree.body[-1:]
    return tree


def Relationship(*, back_populates: str) -> ast.Call:
    return ast.Call(
        func=ast.Name(id="Relationship", ctx=ast.Load()),
        args=[],
        keywords=[
            ast.keyword(arg="back_populates", value=ast.Constant(value=back_populates))
        ],
    )


def _add_foreign_key(module: ast.Module, back_populates: dict[str, list[str]]):
    class_def = cast(ast.ClassDef, module.body[-1])
    for stmt in class_def.body:
        if (
            isinstance(ann_assign := stmt, ast.AnnAssign)
            and isinstance(field_name := ann_assign.target, ast.Name)
            and field_name.id.endswith("_id")
        ):
            table = field_name.id[:-3]
            f = Field(foreign_key=ast.Constant(value=f"{table}.id"))
            optional = False
            if isinstance(ann_assign.annotation, ast.BinOp):
                optional = True
                f.keywords.append(
                    ast.keyword(arg="nullable", value=ast.Constant(value=True))
                )
            ann_assign.annotation = Annotated(
                ann_assign.annotation,
                f,
            )
            module.body.insert(
                0, ast.ImportFrom(to_snake(cls := _t2c(table)), [ast.alias(cls)], 1)
            )
            ann = ast.Name(id=cls, ctx=ast.Load())
            class_def.body.append(
                ast.AnnAssign(
                    target=ast.Name(id=table, ctx=ast.Store()),
                    annotation=Optional(ann) if optional else ann,
                    value=Relationship(back_populates=_c2t(class_def.name) + "s"),
                    simple=1,
                )
            )
            back_populates[table].append(_c2t(class_def.name))


def _t2c(table_name: str):
    """Table name to class name"""
    return TABLE_TO_CLS.get(table_name, table_name.capitalize())


def _c2t(class_name: str):
    return CLS_TO_TABLE.get(class_name, class_name.lower())


def _add_back_populates(module: ast.Module, table: str, back_populates: list[str]):
    *imports, class_def = module.body
    class_def = cast(ast.ClassDef, class_def)
    class_def.body.extend(
        [
            ast.AnnAssign(
                target=ast.Name(id=p + "s", ctx=ast.Store()),
                annotation=ast.Subscript(
                    value=ast.Name(id="list", ctx=ast.Load()),
                    slice=ast.Constant(value=_t2c(p)),
                    ctx=ast.Load(),
                ),
                value=Relationship(back_populates=table),
                simple=1,
            )
            for p in back_populates
        ]
    )
    module.body = (
        imports
        + [
            ast.ImportFrom("typing", names=[ast.alias("TYPE_CHECKING")], level=0),
            ast.If(
                test=ast.Name("TYPE_CHECKING", ctx=ast.Load()),
                body=[
                    ast.ImportFrom(
                        to_snake(cls := _t2c(p)), names=[ast.alias(cls)], level=1
                    )
                    for p in back_populates
                ],
                orelse=[],
            ),
        ]
        + [class_def]
    )


def generate_modules(*modules: ModuleType):
    module_map: dict[str, ast.Module] = {}
    for module in modules:
        table = _c2t(module.__name__.split(".")[-1])
        module_map[table] = generate_module(module)
    back_populates: dict[str, list[str]] = defaultdict(list)
    for module_name, mod in module_map.items():
        _add_foreign_key(mod, back_populates)
    for table, back in back_populates.items():
        _add_back_populates(module_map[table], table, back)
    for module_name, mod in module_map.items():
        dest = (
            Path(__file__).parent / "generated" / module_name.split(".")[-1]
        ).with_suffix(".py")
        dest.write_text(ast.unparse(ast.fix_missing_locations(mod)))
