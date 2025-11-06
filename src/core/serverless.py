"""Serverless-compatible database and Redis initialization

This module provides lazy initialization for serverless environments like Vercel.
Database and Redis connections are created on-demand rather than at startup.
"""

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# Global variables for lazy initialization
_engine: Optional[AsyncEngine] = None
_async_session_factory: Optional[sessionmaker] = None
_redis_client = None


def get_engine() -> AsyncEngine:
    """Get or create async database engine (lazy initialization)"""
    global _engine
    
    if _engine is None:
        from src.core.config import config
        
        logger.info("Creating database engine for serverless...")
        _engine = create_async_engine(
            str(config.database.url),
            echo=config.app.debug,
            pool_pre_ping=True,
            pool_size=1,  # Minimal pool for serverless
            max_overflow=0,  # No overflow in serverless
            pool_recycle=300,  # Recycle connections after 5 minutes
        )
    
    return _engine


def get_session_factory() -> sessionmaker:
    """Get or create async session factory (lazy initialization)"""
    global _async_session_factory
    
    if _async_session_factory is None:
        engine = get_engine()
        _async_session_factory = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
    
    return _async_session_factory


async def get_serverless_db():
    """Get database session for serverless (lazy initialization)
    
    This is a drop-in replacement for get_db() in serverless environments.
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


def get_redis_client():
    """Get or create Redis client (lazy initialization)"""
    global _redis_client
    
    if _redis_client is None:
        from src.core.config import config
        import redis.asyncio as redis
        
        logger.info("Creating Redis client for serverless...")
        _redis_client = redis.from_url(
            str(config.redis.url),
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
    
    return _redis_client

