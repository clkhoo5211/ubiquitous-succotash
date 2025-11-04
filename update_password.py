import asyncio
from src.core.database import AsyncSessionLocal
from src.core.security import hash_password
from sqlalchemy import select
from src.models.user import User

async def main():
    async with AsyncSessionLocal() as db:
        # Find existing test@test.com user
        result = await db.execute(select(User).where(User.email == "test@test.com"))
        user = result.scalar_one_or_none()
        
        if user:
            # Update password
            user.password_hash = hash_password("Test1234")
            await db.commit()
            print("✅ Password updated successfully!")
            print("\nLogin with:")
            print("  Email: test@test.com")
            print("  Password: Test1234")
        else:
            print("❌ User not found")

if __name__ == "__main__":
    asyncio.run(main())

