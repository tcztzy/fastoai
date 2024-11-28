from shutil import copyfileobj
from typing import Annotated, cast

from fastapi import APIRouter, Form, Query, UploadFile
from fastapi.responses import FileResponse
from openai.types.file_deleted import FileDeleted
from openai.types.file_list_params import FileListParams
from openai.types.file_purpose import FilePurpose
from sqlmodel import col, select

from ..dependencies import SessionDependency, SettingsDependency
from ..models import File
from ..pagination import AsyncCursorPage
from ._utils import create_model_from

router = APIRouter(tags=["Files"])


@router.post("/files")
async def upload_file(
    file: UploadFile,
    purpose: Annotated[FilePurpose, Form()],
    settings: SettingsDependency,
    session: SessionDependency,
) -> File:
    file_object = File.model_validate(
        {
            "bytes": file.size,
            "filename": file.filename,
            "purpose": purpose,
            "status": "uploaded",
        }
    )
    with (settings.upload_dir / file_object.id).open("wb") as f:
        copyfileobj(file.file, f)
    session.add(file_object)
    await session.commit()
    await session.refresh(file_object)
    return File.model_validate(file_object.model_dump())


@router.get("/files")
async def list_files(
    q: Annotated[create_model_from(FileListParams), Query()],  # type: ignore
    session: SessionDependency,
) -> AsyncCursorPage[File]:
    params = cast(FileListParams, q.model_dump())
    statement = select(File)
    if purpose := params.get("purpose"):
        statement = statement.where(File.purpose == purpose)
    if order := params.get("order"):
        statement = statement.order_by(getattr(col(File.created_at), order)())
    if after := params.get("after"):
        all_files = (await session.exec(statement)).all()
        after_file = await session.get_one(File, after)
        offset = all_files.index(after_file) + 1
        statement = statement.offset(offset)
    if limit := params.get("limit"):
        statement = statement.limit(limit)
    files = (await session.exec(statement)).all()
    return AsyncCursorPage[File](
        data=[File.model_validate(file.model_dump()) for file in files]
    )


@router.get("/files/{file_id}")
async def retrieve_file(
    file_id: str,
    session: SessionDependency,
) -> File:
    file = await session.get_one(File, file_id)
    return File.model_validate(file.model_dump())


@router.get("/files/{file_id}/content")
async def retrieve_file_content(
    file_id: str,
    settings: SettingsDependency,
    session: SessionDependency,
):
    file = await session.get_one(File, file_id)
    return FileResponse(settings.upload_dir / file.id, filename=file.filename)


@router.delete("/files/{file_id}", response_model=FileDeleted)
async def delete_file(
    file_id: str,
    session: SessionDependency,
):
    file = await session.get_one(File, file_id)
    await session.delete(file)
    await session.commit()
    return FileDeleted(id=file_id, deleted=True, object="file")
