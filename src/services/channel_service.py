"""Channel service"""

from datetime import datetime
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import re

from src.models.organization import Channel
from src.schemas.channel import ChannelCreate, ChannelUpdate
from src.core.exceptions import ChannelNotFoundError, ValidationError


class ChannelService:
    """Service for channel operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from name"""
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        return slug

    async def create_channel(self, channel_data: ChannelCreate) -> Channel:
        """Create a new channel"""
        slug = self._generate_slug(channel_data.name)

        # Check if slug already exists
        existing = await self.db.execute(
            select(Channel).where(Channel.slug == slug)
        )
        if existing.scalar_one_or_none():
            raise ValidationError(f"Channel with slug '{slug}' already exists")

        channel = Channel(
            name=channel_data.name,
            slug=slug,
            description=channel_data.description,
            icon=channel_data.icon,
            color=channel_data.color,
            post_count=0,
            subscriber_count=0,
            sort_order=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self.db.add(channel)
        await self.db.commit()
        await self.db.refresh(channel)
        return channel

    async def get_channel_by_id(self, channel_id: int) -> Channel:
        """Get channel by ID"""
        result = await self.db.execute(
            select(Channel).where(Channel.id == channel_id)
        )
        channel = result.scalar_one_or_none()
        if not channel:
            raise ChannelNotFoundError(f"Channel with ID {channel_id} not found")
        return channel

    async def get_channel_by_slug(self, slug: str) -> Channel:
        """Get channel by slug"""
        result = await self.db.execute(
            select(Channel).where(Channel.slug == slug)
        )
        channel = result.scalar_one_or_none()
        if not channel:
            raise ChannelNotFoundError(f"Channel with slug '{slug}' not found")
        return channel

    async def update_channel(self, channel_id: int, channel_data: ChannelUpdate) -> Channel:
        """Update a channel"""
        channel = await self.get_channel_by_id(channel_id)

        if channel_data.name is not None:
            channel.name = channel_data.name
            channel.slug = self._generate_slug(channel_data.name)
        if channel_data.description is not None:
            channel.description = channel_data.description
        if channel_data.icon is not None:
            channel.icon = channel_data.icon
        if channel_data.color is not None:
            channel.color = channel_data.color
        if channel_data.sort_order is not None:
            channel.sort_order = channel_data.sort_order

        channel.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(channel)
        return channel

    async def delete_channel(self, channel_id: int) -> None:
        """Delete a channel"""
        channel = await self.get_channel_by_id(channel_id)
        await self.db.delete(channel)
        await self.db.commit()

    async def list_channels(self) -> List[Channel]:
        """List all channels (sorted by sort_order)"""
        result = await self.db.execute(
            select(Channel).order_by(Channel.sort_order, Channel.name)
        )
        channels = result.scalars().all()
        return list(channels)
