from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.api.dependencies import CurrentUser, Database
from app.services.media import MediaService

router = APIRouter()


@router.get("/{media_id}")
async def get_video(media_id: str, database: Database, current_user: CurrentUser) -> FileResponse:
    document = await MediaService(database).get_owned(media_id, current_user.id)
    if document is None:
        raise HTTPException(status_code=404, detail="Media not found")
    return FileResponse(
        document["path"],
        media_type=document["content_type"],
        filename=document["filename"],
        content_disposition_type="inline",
    )


@router.get("/{media_id}/frames/{frame_index}")
async def get_frame(
    media_id: str, frame_index: int, database: Database, current_user: CurrentUser
) -> FileResponse:
    document = await MediaService(database).get_owned(media_id, current_user.id)
    paths = document.get("frame_paths", []) if document else []
    if frame_index < 0 or frame_index >= len(paths):
        raise HTTPException(status_code=404, detail="Media frame not found")
    return FileResponse(Path(paths[frame_index]), media_type="image/jpeg")
