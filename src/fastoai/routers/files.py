from shutil import copyfileobj
from typing import Literal

from fastapi import APIRouter, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import select

from ..dependencies import SessionDependency, SettingsDependency
from ..models import FileObject
from ..pagination import AsyncCursorPage

router = APIRouter(tags=["Files"])


@router.post("/files")
async def upload_file(
    upload_file: UploadFile,
    purpose: Literal["avatar", "attachment"],
    settings: SettingsDependency,
    session: SessionDependency,
) -> FileObject:
    file_object = FileObject.model_validate(
        {
            "bytes": upload_file.size,
            "filename": upload_file.filename,
            "purpose": purpose,
            "status": "uploaded",
        }
    )
    with (settings.upload_dir / file_object.id).open("wb") as file:
        copyfileobj(upload_file.file, file)
    session.add(file_object)
    await session.commit()
    await session.refresh(file_object)
    return FileObject.model_validate(file_object.model_dump())


@router.get("/files")
async def list_files(
    session: SessionDependency,
) -> AsyncCursorPage[FileObject]:
    files = (await session.exec(select(FileObject))).all()
    return AsyncCursorPage[FileObject](
        data=[FileObject.model_validate(file.model_dump()) for file in files]
    )


@router.get("/files/{file_id}")
async def retrieve_file(
    file_id: str,
    session: SessionDependency,
) -> FileObject:
    file = await session.get_one(FileObject, file_id)
    return FileObject.model_validate(file.model_dump())


@router.get("/files/{file_id}/content")
async def retrieve_file_content(
    file_id: str,
    settings: SettingsDependency,
    session: SessionDependency,
):
    file = await session.get_one(FileObject, file_id)
    return FileResponse(settings.upload_dir / file.id, filename=file.filename)


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    session: SessionDependency,
):
    file = await session.get_one(FileObject, file_id)
    await session.delete(file)
    await session.commit()
    return FileObject.model_validate(file.model_dump())
