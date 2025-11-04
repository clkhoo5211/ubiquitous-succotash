"""Media and IPFS-related Pydantic schemas"""

from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class MediaUploadResponse(BaseModel):
    """Response after successful media upload"""

    success: bool
    ipfs_hash: str = Field(..., description="IPFS CID (Content Identifier)")
    ipfs_url: HttpUrl = Field(..., description="Gateway URL to access the file")
    file_name: str
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str
    message: str


class MediaMetadata(BaseModel):
    """Metadata for uploaded media"""

    ipfs_hash: str
    ipfs_url: HttpUrl
    file_name: str
    file_size: int
    mime_type: str
    uploaded_at: str
    uploader_id: int


class MediaDeleteRequest(BaseModel):
    """Request to delete media"""

    ipfs_hash: str = Field(..., description="IPFS hash of file to delete")


class MediaDeleteResponse(BaseModel):
    """Response after media deletion attempt"""

    success: bool
    message: str
    note: str = Field(
        default="IPFS files are permanent and cannot be deleted from the network. "
        "This operation only removes the file from our pinning service."
    )


class ImageOptimizationRequest(BaseModel):
    """Request for image optimization"""

    max_width: Optional[int] = Field(default=1920, description="Maximum width in pixels")
    max_height: Optional[int] = Field(default=1080, description="Maximum height in pixels")
    quality: Optional[int] = Field(default=85, ge=1, le=100, description="JPEG quality (1-100)")
    format: Optional[str] = Field(
        default="JPEG", pattern="^(JPEG|PNG|WEBP)$", description="Output format"
    )
