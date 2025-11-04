"""Seed data script for development environment

This script populates the database with sample data for testing and development:
- 10 users with different levels
- 5 channels with posts
- 15 posts with various statuses
- 50+ comments (nested structure)
- Likes, points transactions
- Sample tags
- Point economy configuration

Usage:
    python scripts/seed_data.py

Environment Variables:
    APP_SECRET_KEY
    SECURITY_JWT_SECRET_KEY
    IPFS_API_KEY
    DATABASE_URL (from config.yaml)
"""

import asyncio
import random
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal
from src.models.user import User, UserLevelEnum, OAuthAccount, Level
from src.models.content import Post, Comment, Like, Media, ContentStatus
from src.models.organization import Channel, Tag, PostTag
from src.models.points import Transaction, PointEconomy, TransactionType
from src.models.moderation import Report, Ban, ReportStatus, ReportReason
from src.core.security import hash_password


# Sample data
SAMPLE_USERS = [
    {
        "email": "admin@forum.com",
        "username": "admin",
        "display_name": "Forum Administrator",
        "password": "Admin123!",
        "points": 50000,
        "level": UserLevelEnum.SENIOR_MODERATOR,
        "bio": "Official forum administrator account",
    },
    {
        "email": "moderator@forum.com",
        "username": "mod_alice",
        "display_name": "Alice (Moderator)",
        "password": "Moderator123!",
        "points": 5000,
        "level": UserLevelEnum.MODERATOR,
        "bio": "Keeping the forums clean and friendly",
    },
    {
        "email": "bob@example.com",
        "username": "bob_dev",
        "display_name": "Bob the Developer",
        "password": "User123!",
        "points": 1200,
        "level": UserLevelEnum.TRUSTED_USER,
        "bio": "Full-stack developer passionate about blockchain",
    },
    {
        "email": "carol@example.com",
        "username": "carol_crypto",
        "display_name": "Carol",
        "password": "User123!",
        "points": 300,
        "level": UserLevelEnum.ACTIVE_USER,
        "bio": "Crypto enthusiast and Web3 advocate",
    },
    {
        "email": "dave@example.com",
        "username": "dave_newbie",
        "display_name": "Dave",
        "password": "User123!",
        "points": 50,
        "level": UserLevelEnum.NEW_USER,
        "bio": "Just joined! Learning about decentralization",
    },
    {
        "email": "eve@example.com",
        "username": "eve_writer",
        "display_name": "Eve the Writer",
        "password": "User123!",
        "points": 800,
        "level": UserLevelEnum.ACTIVE_USER,
        "bio": "Technical writer and documentation enthusiast",
    },
    {
        "email": "frank@example.com",
        "username": "frank_designer",
        "display_name": "Frank",
        "password": "User123!",
        "points": 450,
        "level": UserLevelEnum.ACTIVE_USER,
        "bio": "UI/UX designer focused on Web3",
    },
    {
        "email": "grace@example.com",
        "username": "grace_security",
        "display_name": "Grace",
        "password": "User123!",
        "points": 2500,
        "level": UserLevelEnum.MODERATOR,
        "bio": "Security researcher and ethical hacker",
    },
    {
        "email": "henry@example.com",
        "username": "henry_trader",
        "display_name": "Henry",
        "password": "User123!",
        "points": 600,
        "level": UserLevelEnum.ACTIVE_USER,
        "bio": "DeFi trader and yield farmer",
    },
    {
        "email": "iris@example.com",
        "username": "iris_artist",
        "display_name": "Iris",
        "password": "User123!",
        "points": 200,
        "level": UserLevelEnum.ACTIVE_USER,
        "bio": "NFT artist exploring decentralized platforms",
    },
]

SAMPLE_CHANNELS = [
    {
        "name": "General Discussion",
        "slug": "general",
        "description": "General discussions about anything and everything",
        "icon": "💬",
        "color": "#3B82F6",
        "sort_order": 1,
    },
    {
        "name": "Announcements",
        "slug": "announcements",
        "description": "Official announcements and platform updates",
        "icon": "📢",
        "color": "#EF4444",
        "sort_order": 2,
    },
    {
        "name": "Development",
        "slug": "development",
        "description": "Software development, coding, and technical discussions",
        "icon": "💻",
        "color": "#10B981",
        "sort_order": 3,
    },
    {
        "name": "Blockchain & Crypto",
        "slug": "crypto",
        "description": "Cryptocurrency, blockchain technology, and Web3",
        "icon": "⛓️",
        "color": "#F59E0B",
        "sort_order": 4,
    },
    {
        "name": "Community",
        "slug": "community",
        "description": "Community events, meetups, and social activities",
        "icon": "🎉",
        "color": "#8B5CF6",
        "sort_order": 5,
    },
]

SAMPLE_TAGS = [
    {"name": "Help Wanted", "slug": "help-wanted", "color": "#EF4444"},
    {"name": "Tutorial", "slug": "tutorial", "color": "#10B981"},
    {"name": "Discussion", "slug": "discussion", "color": "#3B82F6"},
    {"name": "News", "slug": "news", "color": "#F59E0B"},
    {"name": "Question", "slug": "question", "color": "#8B5CF6"},
    {"name": "Solved", "slug": "solved", "color": "#10B981"},
    {"name": "Bug Report", "slug": "bug-report", "color": "#EF4444"},
    {"name": "Feature Request", "slug": "feature-request", "color": "#F59E0B"},
    {"name": "Showcase", "slug": "showcase", "color": "#EC4899"},
    {"name": "Meta", "slug": "meta", "color": "#6B7280"},
]

SAMPLE_POSTS = [
    {
        "channel_slug": "announcements",
        "author_username": "admin",
        "title": "Welcome to the Decentralized Forum! 🎉",
        "body": """We're excited to launch our new decentralized forum platform!

**Key Features:**
- Point-based gamification system
- Crypto rewards for quality contributions
- Community-driven moderation
- Decentralized storage with IPFS
- OAuth2 authentication with multiple providers

Start participating, earn points, and shape the future of decentralized discussion!""",
        "tags": ["News", "Meta"],
        "is_pinned": True,
    },
    {
        "channel_slug": "development",
        "author_username": "bob_dev",
        "title": "Best Practices for Async Python with FastAPI",
        "body": """I've been working with FastAPI and async SQLAlchemy, and here are some lessons learned:

1. **Always use async/await consistently**
2. **Connection pooling is crucial for performance**
3. **Use Pydantic for data validation**
4. **Proper error handling with custom exceptions**

What are your experiences with async Python?""",
        "tags": ["Tutorial", "Discussion"],
    },
    {
        "channel_slug": "crypto",
        "author_username": "carol_crypto",
        "title": "Understanding Points to Crypto Rewards",
        "body": """Quick guide on how our points system works:

- Earn points by creating quality posts and comments
- Receive bonus points when your content gets liked
- Redeem 10,000 points for 0.01 BNB
- All transactions are recorded on-chain for transparency

Has anyone claimed crypto rewards yet?""",
        "tags": ["Tutorial", "Question"],
    },
    {
        "channel_slug": "general",
        "author_username": "dave_newbie",
        "title": "How do I earn points quickly?",
        "body": """I'm new here and want to understand the points system better.

What's the best way to earn points? Should I focus on posts or comments?

Any tips for newcomers?""",
        "tags": ["Question", "Help Wanted"],
    },
    {
        "channel_slug": "development",
        "author_username": "eve_writer",
        "title": "Documentation Sprint - Join Us!",
        "body": """We're organizing a documentation sprint this weekend to improve our API docs.

**When:** This Saturday, 10 AM - 4 PM UTC
**Where:** Virtual (Discord link in comments)
**What:** Writing guides, improving examples, fixing typos

Who's interested?""",
        "tags": ["Community", "Help Wanted"],
    },
]


async def create_point_economy(db: AsyncSession) -> PointEconomy:
    """Create point economy configuration"""
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
    db.add(economy)
    await db.commit()
    await db.refresh(economy)
    return economy


async def create_users(db: AsyncSession) -> dict[str, User]:
    """Create sample users"""
    users = {}

    for user_data in SAMPLE_USERS:
        user = User(
            email=user_data["email"],
            username=user_data["username"],
            password_hash=hash_password(user_data["password"]),
            display_name=user_data["display_name"],
            bio=user_data.get("bio"),
            points=user_data["points"],
            level=user_data["level"],
            is_active=True,
            email_verified=True,
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 90)),
            last_login_at=datetime.utcnow() - timedelta(hours=random.randint(1, 24)),
        )
        db.add(user)
        users[user.username] = user

    await db.commit()

    for user in users.values():
        await db.refresh(user)

    return users


async def create_channels(db: AsyncSession) -> dict[str, Channel]:
    """Create sample channels"""
    channels = {}

    for channel_data in SAMPLE_CHANNELS:
        channel = Channel(**channel_data, created_at=datetime.utcnow() - timedelta(days=30))
        db.add(channel)
        channels[channel.slug] = channel

    await db.commit()

    for channel in channels.values():
        await db.refresh(channel)

    return channels


async def create_tags(db: AsyncSession) -> dict[str, Tag]:
    """Create sample tags"""
    tags = {}

    for tag_data in SAMPLE_TAGS:
        tag = Tag(**tag_data, created_at=datetime.utcnow() - timedelta(days=20))
        db.add(tag)
        tags[tag.name] = tag

    await db.commit()

    for tag in tags.values():
        await db.refresh(tag)

    return tags


async def create_posts(
    db: AsyncSession, users: dict[str, User], channels: dict[str, Channel], tags: dict[str, Tag]
) -> list[Post]:
    """Create sample posts with tags"""
    posts = []

    for post_data in SAMPLE_POSTS:
        author = users[post_data["author_username"]]
        channel = channels[post_data["channel_slug"]]

        post = Post(
            title=post_data["title"],
            body=post_data["body"],
            author_id=author.id,
            channel_id=channel.id,
            is_pinned=post_data.get("is_pinned", False),
            status=ContentStatus.ACTIVE,
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
        )
        db.add(post)
        await db.flush()

        # Add tags
        for tag_name in post_data.get("tags", []):
            if tag_name in tags:
                post_tag = PostTag(post_id=post.id, tag_id=tags[tag_name].id)
                db.add(post_tag)

        posts.append(post)

    await db.commit()

    for post in posts:
        await db.refresh(post)

    return posts


async def create_comments(db: AsyncSession, posts: list[Post], users: dict[str, User]):
    """Create sample comments with nested replies"""
    comment_bodies = [
        "Great post! Thanks for sharing.",
        "I completely agree with this.",
        "Has anyone tried this in production?",
        "This is exactly what I was looking for!",
        "Thanks for the detailed explanation.",
        "I have a question about the second point...",
        "This worked perfectly for me!",
        "Can you elaborate on this?",
        "Interesting perspective!",
        "Thanks for bringing this up.",
    ]

    all_comments = []

    for post in posts:
        # Create 3-5 top-level comments per post
        num_comments = random.randint(3, 5)
        user_list = list(users.values())

        for _ in range(num_comments):
            author = random.choice(user_list)
            comment = Comment(
                body=random.choice(comment_bodies),
                post_id=post.id,
                author_id=author.id,
                parent_id=None,
                status=ContentStatus.ACTIVE,
                created_at=post.created_at + timedelta(hours=random.randint(1, 48)),
            )
            db.add(comment)
            await db.flush()
            all_comments.append(comment)

            # Add 0-2 replies to each comment
            num_replies = random.randint(0, 2)
            for _ in range(num_replies):
                reply_author = random.choice(user_list)
                reply = Comment(
                    body=random.choice(comment_bodies),
                    post_id=post.id,
                    author_id=reply_author.id,
                    parent_id=comment.id,
                    status=ContentStatus.ACTIVE,
                    created_at=comment.created_at + timedelta(hours=random.randint(1, 24)),
                )
                db.add(reply)
                await db.flush()
                all_comments.append(reply)

    await db.commit()


async def create_likes(db: AsyncSession, posts: list[Post], users: dict[str, User]):
    """Create sample likes for posts"""
    user_list = list(users.values())

    for post in posts:
        # Each post gets 3-8 random likes
        num_likes = random.randint(3, 8)
        likers = random.sample(user_list, min(num_likes, len(user_list)))

        for liker in likers:
            like = Like(
                user_id=liker.id,
                post_id=post.id,
                created_at=post.created_at + timedelta(hours=random.randint(1, 72)),
            )
            db.add(like)

        # Update post like count
        post.like_count = num_likes

    await db.commit()


async def create_transactions(db: AsyncSession, users: dict[str, User]):
    """Create sample point transactions"""
    for user in users.values():
        # Registration bonus
        tx = Transaction(
            user_id=user.id,
            amount=100,
            transaction_type=TransactionType.REGISTRATION_BONUS,
            description="Welcome bonus for joining the forum",
            balance_after=100,
            created_at=user.created_at,
        )
        db.add(tx)

        # Simulate some activity transactions
        balance = 100
        for _ in range(random.randint(5, 15)):
            tx_type = random.choice(
                [
                    TransactionType.CREATE_POST,
                    TransactionType.CREATE_COMMENT,
                    TransactionType.LIKE_CONTENT,
                    TransactionType.RECEIVE_LIKE,
                ]
            )

            if tx_type == TransactionType.CREATE_POST:
                amount = -5
                desc = "Created a new post"
            elif tx_type == TransactionType.CREATE_COMMENT:
                amount = -2
                desc = "Created a comment"
            elif tx_type == TransactionType.LIKE_CONTENT:
                amount = -1
                desc = "Liked a post"
            else:  # RECEIVE_LIKE
                amount = random.choice([3, 30, 350])
                desc = f"Received a like on your content"

            balance += amount
            if balance < 0:
                balance = 0

            tx = Transaction(
                user_id=user.id,
                amount=amount,
                transaction_type=tx_type,
                description=desc,
                balance_after=balance,
                created_at=user.created_at + timedelta(days=random.randint(1, 80)),
            )
            db.add(tx)

    await db.commit()


async def main():
    """Main seed data function"""
    print("🌱 Starting database seeding...")

    async with AsyncSessionLocal() as db:
        print("  ✅ Creating point economy configuration...")
        await create_point_economy(db)

        print("  ✅ Creating users...")
        users = await create_users(db)
        print(f"     Created {len(users)} users")

        print("  ✅ Creating channels...")
        channels = await create_channels(db)
        print(f"     Created {len(channels)} channels")

        print("  ✅ Creating tags...")
        tags = await create_tags(db)
        print(f"     Created {len(tags)} tags")

        print("  ✅ Creating posts...")
        posts = await create_posts(db, users, channels, tags)
        print(f"     Created {len(posts)} posts")

        print("  ✅ Creating comments...")
        await create_comments(db, posts, users)
        print(f"     Created nested comments")

        print("  ✅ Creating likes...")
        await create_likes(db, posts, users)
        print(f"     Created likes for posts")

        print("  ✅ Creating point transactions...")
        await create_transactions(db, users)
        print(f"     Created transaction history")

    print("\n✨ Database seeding completed successfully!")
    print("\n📊 Sample Accounts:")
    print("   Admin: admin@forum.com / Admin123!")
    print("   Moderator: moderator@forum.com / Moderator123!")
    print("   User: bob@example.com / User123!")
    print("\n🎯 You can now start the application and explore the seeded data!")


if __name__ == "__main__":
    asyncio.run(main())
