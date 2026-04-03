from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import Role, User
from app.security import hash_password


async def ensure_bootstrap_admin() -> None:
    async with AsyncSessionLocal() as session:
        n = await session.scalar(select(User.id).limit(1))
        if n is not None:
            return
        admin = User(
            email="admin@example.com",
            hashed_password=hash_password("admin123"),
            role=Role.admin,
            is_active=True,
        )
        session.add(admin)
        await session.commit()
