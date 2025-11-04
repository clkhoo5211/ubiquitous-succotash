"""Tag service"""

from datetime import datetime
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import re

from src.models.organization import Tag
from src.schemas.tag import TagCreate, TagUpdate
from src.core.exceptions import TagNotFoundError, ValidationError


class TagService:
    """Service for tag operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug"""
        slug = name.lower()
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        slug = slug.strip("-")
        return slug

    async def create_tag(self, tag_data: TagCreate) -> Tag:
        """Create a new tag"""
        slug = self._generate_slug(tag_data.name)

        # Check if slug exists
        existing = await self.db.execute(select(Tag).where(Tag.slug == slug))
        if existing.scalar_one_or_none():
            raise ValidationError(f"Tag with slug '{slug}' already exists")

        tag = Tag(
            name=tag_data.name,
            slug=slug,
            description=tag_data.description,
            color=tag_data.color,
            post_count=0,
            created_at=datetime.utcnow(),
        )

        self.db.add(tag)
        await self.db.commit()
        await self.db.refresh(tag)
        return tag

    async def get_tag_by_id(self, tag_id: int) -> Tag:
        """Get tag by ID"""
        result = await self.db.execute(select(Tag).where(Tag.id == tag_id))
        tag = result.scalar_one_or_none()
        if not tag:
            raise TagNotFoundError(f"Tag with ID {tag_id} not found")
        return tag

    async def get_tag_by_slug(self, slug: str) -> Tag:
        """Get tag by slug"""
        result = await self.db.execute(select(Tag).where(Tag.slug == slug))
        tag = result.scalar_one_or_none()
        if not tag:
            raise TagNotFoundError(f"Tag with slug '{slug}' not found")
        return tag

    async def update_tag(self, tag_id: int, tag_data: TagUpdate) -> Tag:
        """Update a tag"""
        tag = await self.get_tag_by_id(tag_id)

        if tag_data.name is not None:
            tag.name = tag_data.name
            tag.slug = self._generate_slug(tag_data.name)
        if tag_data.description is not None:
            tag.description = tag_data.description
        if tag_data.color is not None:
            tag.color = tag_data.color

        await self.db.commit()
        await self.db.refresh(tag)
        return tag

    async def delete_tag(self, tag_id: int) -> None:
        """Delete a tag"""
        tag = await self.get_tag_by_id(tag_id)
        await self.db.delete(tag)
        await self.db.commit()

    async def list_tags(self) -> List[Tag]:
        """List all tags (sorted by post_count desc)"""
        result = await self.db.execute(select(Tag).order_by(Tag.post_count.desc(), Tag.name))
        tags = result.scalars().all()
        return list(tags)
