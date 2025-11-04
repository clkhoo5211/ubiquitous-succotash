"""Pytest configuration and fixtures

This module provides comprehensive test fixtures for unit, integration, and E2E tests.
Uses in-memory SQLite for fast test execution.
"""

import asyncio
from typing import AsyncGenerator
from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from faker import Faker
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.core.database import Base, get_db
from src.core.security import hash_password, create_access_token
from src.main import app
from src.models.user import User, UserLevelEnum
from src.models.content import Post, Comment, ContentStatus
from src.models.organization import Channel, Tag
from src.models.points import PointEconomy, Transaction, TransactionType


# Test database URL (use SQLite in-memory for fast tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Faker instance for generating test data
fake = Faker()


# ============================================================================
# Event Loop Configuration
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def test_db_with_data(test_db: AsyncSession) -> AsyncSession:
    """Create test database with sample data"""
    # Create point economy
    economy = PointEconomy(
        id=1,
        create_post_cost=-5,
        create_comment_cost=-2,
        like_cost=-1,
        registration_bonus=100,
        receive_like_tier1=3,
        receive_like_tier2=30,
        receive_like_tier3=350,
        crypto_reward_cost=10000,
        crypto_reward_bnb_amount="0.01",
    )
    test_db.add(economy)
    await test_db.commit()

    return test_db


# ============================================================================
# HTTP Client Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def async_client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for API testing"""

    # Override database dependency
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """FastAPI synchronous test client (for simple tests)"""
    from fastapi.testclient import TestClient

    return TestClient(app)


# ============================================================================
# User Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def test_user(test_db: AsyncSession) -> User:
    """Create a test user"""
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash=hash_password("TestPassword123!"),
        display_name="Test User",
        points=100,
        level=UserLevelEnum.NEW_USER,
        is_active=True,
        email_verified=True,
        created_at=datetime.utcnow(),
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(test_db: AsyncSession) -> User:
    """Create an admin user (senior moderator level)"""
    admin = User(
        email="admin@example.com",
        username="admin",
        password_hash=hash_password("AdminPassword123!"),
        display_name="Admin User",
        points=50000,
        level=UserLevelEnum.SENIOR_MODERATOR,  # Highest level in the system
        is_active=True,
        email_verified=True,
        created_at=datetime.utcnow(),
    )
    test_db.add(admin)
    await test_db.commit()
    await test_db.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def test_moderator(test_db: AsyncSession) -> User:
    """Create a moderator user"""
    moderator = User(
        email="mod@example.com",
        username="moderator",
        password_hash=hash_password("ModPassword123!"),
        display_name="Moderator User",
        points=5000,
        level=UserLevelEnum.MODERATOR,
        is_active=True,
        email_verified=True,
        created_at=datetime.utcnow(),
    )
    test_db.add(moderator)
    await test_db.commit()
    await test_db.refresh(moderator)
    return moderator


@pytest_asyncio.fixture
async def multiple_users(test_db: AsyncSession) -> list[User]:
    """Create multiple test users"""
    users = []
    for i in range(5):
        user = User(
            email=f"user{i}@example.com",
            username=f"user{i}",
            password_hash=hash_password(f"Password{i}123!"),
            display_name=f"User {i}",
            points=100 * (i + 1),
            level=UserLevelEnum.ACTIVE_USER,
            is_active=True,
            email_verified=True,
            created_at=datetime.utcnow() - timedelta(days=i),
        )
        test_db.add(user)
        users.append(user)

    await test_db.commit()
    for user in users:
        await test_db.refresh(user)

    return users


# ============================================================================
# Authentication Fixtures
# ============================================================================


@pytest.fixture
def test_user_token(test_user: User) -> str:
    """Create access token for test user"""
    return create_access_token({"sub": test_user.id})


@pytest.fixture
def test_admin_token(test_admin: User) -> str:
    """Create access token for admin user"""
    return create_access_token({"sub": test_admin.id})


@pytest.fixture
def test_moderator_token(test_moderator: User) -> str:
    """Create access token for moderator user"""
    return create_access_token({"sub": test_moderator.id})


@pytest.fixture
def auth_headers(test_user_token: str) -> dict:
    """Create authorization headers with test user token"""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def admin_auth_headers(test_admin_token: str) -> dict:
    """Create authorization headers with admin token"""
    return {"Authorization": f"Bearer {test_admin_token}"}


@pytest.fixture
def moderator_auth_headers(test_moderator_token: str) -> dict:
    """Create authorization headers with moderator token"""
    return {"Authorization": f"Bearer {test_moderator_token}"}


# ============================================================================
# Content Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def test_channel(test_db: AsyncSession) -> Channel:
    """Create a test channel"""
    channel = Channel(
        name="Test Channel",
        slug="test-channel",
        description="A test channel for testing",
        icon="💬",
        color="#3B82F6",
        sort_order=1,
        created_at=datetime.utcnow(),
    )
    test_db.add(channel)
    await test_db.commit()
    await test_db.refresh(channel)
    return channel


@pytest_asyncio.fixture
async def test_tag(test_db: AsyncSession) -> Tag:
    """Create a test tag"""
    tag = Tag(
        name="Test Tag",
        slug="test-tag",
        description="A test tag for testing",
        color="#6B7280",
        created_at=datetime.utcnow(),
    )
    test_db.add(tag)
    await test_db.commit()
    await test_db.refresh(tag)
    return tag


@pytest_asyncio.fixture
async def test_post(test_db: AsyncSession, test_user: User, test_channel: Channel) -> Post:
    """Create a test post"""
    post = Post(
        title="Test Post",
        body="This is a test post body.",
        body_html="<p>This is a test post body.</p>",
        user_id=test_user.id,
        channel_id=test_channel.id,
        status=ContentStatus.ACTIVE,
        created_at=datetime.utcnow(),
    )
    test_db.add(post)
    await test_db.commit()
    await test_db.refresh(post)
    return post


@pytest_asyncio.fixture
async def test_comment(test_db: AsyncSession, test_user: User, test_post: Post) -> Comment:
    """Create a test comment"""
    comment = Comment(
        body="This is a test comment.",
        body_html="<p>This is a test comment.</p>",
        post_id=test_post.id,
        user_id=test_user.id,
        parent_id=None,
        status=ContentStatus.ACTIVE,
        created_at=datetime.utcnow(),
    )
    test_db.add(comment)
    await test_db.commit()
    await test_db.refresh(comment)
    return comment


@pytest_asyncio.fixture
async def multiple_posts(
    test_db: AsyncSession, test_user: User, test_channel: Channel
) -> list[Post]:
    """Create multiple test posts"""
    posts = []
    for i in range(10):
        post = Post(
            title=f"Test Post {i}",
            body=f"This is test post body {i}.",
            body_html=f"<p>This is test post body {i}.</p>",
            user_id=test_user.id,
            channel_id=test_channel.id,
            status=ContentStatus.ACTIVE,
            created_at=datetime.utcnow() - timedelta(hours=i),
        )
        test_db.add(post)
        posts.append(post)

    await test_db.commit()
    for post in posts:
        await test_db.refresh(post)

    return posts


# ============================================================================
# Points & Economy Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def test_economy(test_db: AsyncSession) -> PointEconomy:
    """Create test point economy configuration"""
    economy = PointEconomy(
        id=1,
        create_post_cost=-5,
        create_comment_cost=-2,
        like_cost=-1,
        registration_bonus=100,
        receive_like_tier1=3,
        receive_like_tier2=30,
        receive_like_tier3=350,
        crypto_reward_cost=10000,
        crypto_reward_bnb_amount="0.01",
    )
    test_db.add(economy)
    await test_db.commit()
    await test_db.refresh(economy)
    return economy


@pytest_asyncio.fixture
async def test_transaction(test_db: AsyncSession, test_user: User) -> Transaction:
    """Create a test transaction"""
    transaction = Transaction(
        user_id=test_user.id,
        amount=100,
        transaction_type=TransactionType.REGISTRATION_BONUS,
        description="Registration bonus",
        balance_after=100,
        created_at=datetime.utcnow(),
    )
    test_db.add(transaction)
    await test_db.commit()
    await test_db.refresh(transaction)
    return transaction


# ============================================================================
# Faker Data Generators
# ============================================================================


@pytest.fixture
def fake_user_data() -> dict:
    """Generate fake user data"""
    return {
        "email": fake.email(),
        "username": fake.user_name(),
        "password": "Password123!",
        "display_name": fake.name(),
    }


@pytest.fixture
def fake_post_data() -> dict:
    """Generate fake post data"""
    return {
        "title": fake.sentence(),
        "body": fake.paragraph(nb_sentences=5),
    }


@pytest.fixture
def fake_comment_data() -> dict:
    """Generate fake comment data"""
    return {
        "body": fake.paragraph(nb_sentences=2),
    }


# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "asyncio: mark test as async")
