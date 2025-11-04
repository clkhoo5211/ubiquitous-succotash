import asyncio
from src.core.database import AsyncSessionLocal
from src.models.user import User, UserLevelEnum
from src.core.security import hash_password
from datetime import datetime

async def main():
    async with AsyncSessionLocal() as db:
        # Create test user with valid password (8+ characters)
        user = User(
            email="test@test.com",
            username="testuser",
            password_hash=hash_password("Test1234"),
            display_name="Test User",
            points=1000,
            level=UserLevelEnum.TRUSTED_USER,
            is_active=True,
            email_verified=True,
            created_at=datetime.utcnow(),
        )
        db.add(user)
        await db.commit()
        print("✅ User created successfully!")
        print("\nLogin with:")
        print("  Email: test@test.com")
        print("  Password: Test1234")

if __name__ == "__main__":
    asyncio.run(main())

