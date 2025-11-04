"""Media upload and IPFS storage service"""

import hashlib
from datetime import datetime
from typing import List, Optional
from pathlib import Path
from fastapi import UploadFile

from sqlalchemy.ext.asyncio import AsyncSession
from src.models.content import Media, MediaType


class FileUploadService:
    """Service for handling file uploads and storage"""

    UPLOAD_DIR = Path("uploads")
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    def __init__(self, db: AsyncSession):
        self.db = db
        # Ensure upload directory exists
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    async def upload_file(
        self, file: UploadFile, user_id: int, post_id: Optional[int] = None
    ) -> Media:
        """Upload a file and create Media record"""

        # Validate file size
        content = await file.read()
        if len(content) > self.MAX_FILE_SIZE:
            raise ValueError(
                f"File too large. Maximum size is {self.MAX_FILE_SIZE / 1024 / 1024}MB"
            )

        # Generate unique filename using hash of content
        file_hash = hashlib.sha256(content).hexdigest()
        file_ext = Path(file.filename).suffix if file.filename else ""
        unique_filename = f"{file_hash}{file_ext}"
        file_path = self.UPLOAD_DIR / unique_filename

        # Save file to disk if not already exists
        if not file_path.exists():
            file_path.write_bytes(content)

        # Determine media type
        mime_type = file.content_type or "application/octet-stream"
        media_type = MediaType.IMAGE
        if mime_type.startswith("video/"):
            media_type = MediaType.VIDEO
        elif mime_type == "image/gif":
            media_type = MediaType.GIF

        # Generate a simple IPFS hash (mock for now - in production, upload to IPFS)
        # ipfs_hash = f"ipfs_{file_hash[:12]}"  # TODO: Use when IPFS is implemented

        # Create media record (use hash as the stored filename for uniqueness)
        media = Media(
            post_id=post_id,
            user_id=user_id,
            file_name=file.filename or unique_filename,
            file_type=media_type,
            file_size_bytes=len(content),
            mime_type=mime_type,
            ipfs_hash=unique_filename,  # Store the actual filename that's saved
            ipfs_url=f"/uploads/{unique_filename}",  # Direct path to uploaded file
            created_at=datetime.utcnow(),
        )

        self.db.add(media)
        await self.db.commit()
        await self.db.refresh(media)

        return media

    async def get_media_by_post(self, post_id: int) -> List[Media]:
        """Get all media for a post"""
        from sqlalchemy import select

        stmt = select(Media).where(Media.post_id == post_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
