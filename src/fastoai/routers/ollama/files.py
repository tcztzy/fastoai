from shutil import copyfileobj

from fastapi import Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from openai.types.file_object import FileObject
from sqlmodel import select

from ...models.file import File, FilePurpose
from ...models.user import User, get_current_active_user
from ...routing import OAIRouter
from ...schema import ListObject
from ...settings import Settings, get_settings

router = OAIRouter(tags=["Files"])


@router.post("/files")
async def upload_file(
    upload_file: UploadFile,
    purpose: FilePurpose,
    settings: Settings = Depends(get_settings),
    user: User = Depends(get_current_active_user),
) -> FileObject:
    file_object = File(
        bytes=upload_file.size,
        filename=upload_file.filename,
        purpose=purpose,
    )
    with (settings.upload_dir / file_object.id).open("wb") as file:
        copyfileobj(upload_file.file, file)
    settings.session.add(file_object)
    settings.session.commit()
    settings.session.refresh(file_object)
    print(file_object.model_dump())
    return FileObject.model_validate(file_object.model_dump())


@router.get("/files")
async def list_files(
    user: User = Depends(get_current_active_user),
    settings: Settings = Depends(get_settings),
) -> ListObject[FileObject]:
    files = settings.session.exec(select(File)).all()
    return ListObject[FileObject](
        data=[FileObject.model_validate(file.model_dump()) for file in files]
    )


@router.get("/files/{file_id}")
async def retrieve_file(
    file_id: str,
    user: User = Depends(get_current_active_user),
    settings: Settings = Depends(get_settings),
) -> FileObject:
    file = settings.session.get(File, file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")
    return FileObject.model_validate(file.model_dump())


@router.get("/files/{file_id}/content")
async def retrieve_file_content(
    file_id: str,
    user: User = Depends(get_current_active_user),
    settings: Settings = Depends(get_settings),
):
    file = settings.session.get(File, file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(settings.upload_dir / file.id, filename=file.filename)


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    user: User = Depends(get_current_active_user),
    settings: Settings = Depends(get_settings),
):
    file = settings.session.get(File, file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")
    settings.session.delete(file)
    settings.session.commit()
    return FileObject.model_validate(file.model_dump())
