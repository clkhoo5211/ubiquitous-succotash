"""Tags API routes"""

from fastapi import APIRouter, Depends, status, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.tag import TagCreate, TagUpdate, TagResponse, TagListResponse
from src.core.dependencies import get_db, require_moderator
from src.models.user import User
from src.services.tag_service import TagService

router = APIRouter()


@router.post(
    "/", response_model=TagResponse, status_code=status.HTTP_201_CREATED, summary="Create a tag"
)
async def create_tag(
    tag_data: TagCreate,
    current_user: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """Create a new tag (moderator only)."""
    tag_service = TagService(db)
    tag = await tag_service.create_tag(tag_data)
    return tag


@router.get("/", response_model=TagListResponse, summary="List all tags")
async def list_tags(db: AsyncSession = Depends(get_db)):
    """Get all tags (sorted by popularity)."""
    tag_service = TagService(db)
    tags = await tag_service.list_tags()
    return TagListResponse(tags=tags, total=len(tags))


@router.get("/{tag_id}", response_model=TagResponse, summary="Get tag by ID")
async def get_tag_by_id(
    tag_id: int = Path(..., description="Tag ID"), db: AsyncSession = Depends(get_db)
):
    """Get tag details by ID."""
    tag_service = TagService(db)
    tag = await tag_service.get_tag_by_id(tag_id)
    return tag


@router.get("/slug/{slug}", response_model=TagResponse, summary="Get tag by slug")
async def get_tag_by_slug(
    slug: str = Path(..., description="Tag slug"), db: AsyncSession = Depends(get_db)
):
    """Get tag details by slug."""
    tag_service = TagService(db)
    tag = await tag_service.get_tag_by_slug(slug)
    return tag


@router.patch("/{tag_id}", response_model=TagResponse, summary="Update a tag")
async def update_tag(
    tag_id: int = Path(..., description="Tag ID"),
    tag_data: TagUpdate = ...,
    current_user: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """Update a tag (moderator only)."""
    tag_service = TagService(db)
    tag = await tag_service.update_tag(tag_id, tag_data)
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a tag")
async def delete_tag(
    tag_id: int = Path(..., description="Tag ID"),
    current_user: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """Delete a tag (moderator only)."""
    tag_service = TagService(db)
    await tag_service.delete_tag(tag_id)
    return None
