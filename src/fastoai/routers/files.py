from shutil import copyfileobj
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import select

from ..models import FileObject
from ..schema import ListObject
from ..settings import Settings, get_settings

router = APIRouter(tags=["Files"])


@router.post("/files")
async def upload_file(
    upload_file: UploadFile,
    purpose: Literal["avatar", "attachment"],
    settings: Settings = Depends(get_settings),
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
    settings.session.add(file_object)
    settings.session.commit()
    settings.session.refresh(file_object)
    return FileObject.model_validate(file_object.model_dump())


@router.get("/files")
async def list_files(
    settings: Settings = Depends(get_settings),
) -> ListObject[FileObject]:
    files = settings.session.exec(select(FileObject)).all()
    return ListObject[FileObject](
        data=[FileObject.model_validate(file.model_dump()) for file in files]
    )


@router.get("/files/{file_id}")
async def retrieve_file(
    file_id: str,
    settings: Settings = Depends(get_settings),
) -> FileObject:
    file = settings.session.get(FileObject, file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")
    return FileObject.model_validate(file.model_dump())


@router.get("/files/{file_id}/content")
async def retrieve_file_content(
    file_id: str,
    settings: Settings = Depends(get_settings),
):
    file = settings.session.get(FileObject, file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(settings.upload_dir / file.id, filename=file.filename)


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    settings: Settings = Depends(get_settings),
):
    file = settings.session.get(FileObject, file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")
    settings.session.delete(file)
    settings.session.commit()
    return FileObject.model_validate(file.model_dump())
