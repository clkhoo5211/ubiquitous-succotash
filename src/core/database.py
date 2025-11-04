"""Database connection and session management

Uses SQLAlchemy 2.0+ async engine with asyncpg for PostgreSQL.
Implements connection pooling and async session management.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.pool import NullPool, QueuePool

from src.core.config import config


class Base(DeclarativeBase):
    """Base class for all database models"""

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name automatically from class name"""
        return cls.__name__.lower()


# Create async engine
if config.app.environment == "production":
    engine: AsyncEngine = create_async_engine(
        str(config.database.url),
        echo=config.database.echo,
        pool_size=config.database.pool_size,
        max_overflow=config.database.max_overflow,
        poolclass=QueuePool,
        future=True,
    )
else:
    # Development: Use NullPool (no pooling, direct connections)
    engine: AsyncEngine = create_async_engine(
        str(config.database.url),
        echo=config.database.echo,
        poolclass=NullPool,
        future=True,
    )

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions

    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables

    Creates all tables defined in models.
    Should only be called once during application startup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections

    Disposes of the engine and closes all connections.
    Should be called during application shutdown.
    """
    await engine.dispose()
