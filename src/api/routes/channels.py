"""Channels API routes"""

from fastapi import APIRouter, Depends, status, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.channel import ChannelCreate, ChannelUpdate, ChannelResponse, ChannelListResponse
from src.core.dependencies import get_db, require_moderator
from src.models.user import User
from src.services.channel_service import ChannelService

router = APIRouter()


@router.post(
    "/",
    response_model=ChannelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a channel",
)
async def create_channel(
    channel_data: ChannelCreate,
    current_user: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new channel (moderator only).

    **Required fields:**
    - `name`: Channel name (2-100 chars)

    **Optional fields:**
    - `description`: Channel description
    - `icon`: Emoji or icon name
    - `color`: Hex color code (default: #3B82F6)
    """
    channel_service = ChannelService(db)
    channel = await channel_service.create_channel(channel_data)
    return channel


@router.get("/", response_model=ChannelListResponse, summary="List all channels")
async def list_channels(db: AsyncSession = Depends(get_db)):
    """
    Get all channels.

    **Returns:**
    - All channels sorted by sort_order and name
    - Includes post count and subscriber count
    """
    channel_service = ChannelService(db)
    channels = await channel_service.list_channels()
    return ChannelListResponse(channels=channels, total=len(channels))


@router.get("/{channel_id}", response_model=ChannelResponse, summary="Get channel by ID")
async def get_channel_by_id(
    channel_id: int = Path(..., description="Channel ID"), db: AsyncSession = Depends(get_db)
):
    """Get channel details by ID."""
    channel_service = ChannelService(db)
    channel = await channel_service.get_channel_by_id(channel_id)
    return channel


@router.get("/slug/{slug}", response_model=ChannelResponse, summary="Get channel by slug")
async def get_channel_by_slug(
    slug: str = Path(..., description="Channel slug"), db: AsyncSession = Depends(get_db)
):
    """Get channel details by slug (URL-friendly name)."""
    channel_service = ChannelService(db)
    channel = await channel_service.get_channel_by_slug(slug)
    return channel


@router.patch("/{channel_id}", response_model=ChannelResponse, summary="Update a channel")
async def update_channel(
    channel_id: int = Path(..., description="Channel ID"),
    channel_data: ChannelUpdate = ...,
    current_user: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a channel (moderator only).

    **Updatable fields:**
    - `name`: Channel name
    - `description`: Channel description
    - `icon`: Icon
    - `color`: Hex color
    - `sort_order`: Display order
    """
    channel_service = ChannelService(db)
    channel = await channel_service.update_channel(channel_id, channel_data)
    return channel


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a channel")
async def delete_channel(
    channel_id: int = Path(..., description="Channel ID"),
    current_user: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a channel (moderator only).

    **Warning:** This will also delete all posts in the channel.
    """
    channel_service = ChannelService(db)
    await channel_service.delete_channel(channel_id)
    return None
