import logging
from pathlib import Path
from uuid import uuid4

import cv2
from bson import ObjectId
from fastapi import UploadFile

from app.ai.video_analyser import VideoAnalyser
from app.core.config import get_settings

logger = logging.getLogger(__name__)
ALLOWED_TYPES = {"video/mp4": ".mp4", "video/webm": ".webm", "video/quicktime": ".mov"}


class UnsupportedMediaError(ValueError):
    pass


class MediaTooLargeError(ValueError):
    pass


class MediaService:
    def __init__(self, database) -> None:
        self.database = database
        self.root = Path(get_settings().media_root).resolve()

    async def stage_and_analyse(self, upload: UploadFile):
        suffix = ALLOWED_TYPES.get(upload.content_type or "")
        if suffix is None:
            raise UnsupportedMediaError("Supported video formats are MP4, WebM, and MOV")
        self.root.mkdir(parents=True, exist_ok=True)
        media_id = str(ObjectId())
        video_path = self.root / f"{uuid4().hex}{suffix}"
        size = 0
        frame_paths: list[str] = []
        try:
            with video_path.open("wb") as handle:
                while chunk := await upload.read(1024 * 1024):
                    size += len(chunk)
                    if size > get_settings().max_video_bytes:
                        raise MediaTooLargeError("Video must be 50 MB or smaller")
                    handle.write(chunk)
            analysis = VideoAnalyser().analyse(video_path, get_settings().max_video_seconds)
            for image in analysis.frame_images:
                frame_path = self.root / f"{uuid4().hex}.jpg"
                if not cv2.imwrite(str(frame_path), image):
                    raise OSError("Could not save a representative frame")
                frame_paths.append(str(frame_path))
            return media_id, video_path, frame_paths, size, analysis
        except Exception:
            video_path.unlink(missing_ok=True)
            for frame_path in frame_paths:
                Path(frame_path).unlink(missing_ok=True)
            raise

    async def delete_paths(self, paths: list[str]) -> None:
        for raw_path in paths:
            try:
                path = Path(raw_path).resolve()
                if path.parent == self.root:
                    path.unlink(missing_ok=True)
            except OSError:
                logger.exception("Could not remove a private media file")

    async def get_owned(self, media_id: str, owner_id: str):
        if not ObjectId.is_valid(media_id):
            return None
        return await self.database.media.find_one({"_id": ObjectId(media_id), "owner_id": owner_id})

    async def delete_for_observation(self, observation_id: str, owner_id: str) -> None:
        query = {"observation_id": observation_id, "owner_id": owner_id}
        documents = self.database.media.find(query)
        async for document in documents:
            await self.delete_paths([document["path"], *document.get("frame_paths", [])])
        await self.database.media.delete_many(query)
