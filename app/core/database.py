from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.core.config import settings
from typing import Optional
import uuid


class Base(DeclarativeBase):
    pass


# Create async engine
engine = create_async_engine(
    settings.effective_database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.debug,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def set_tenant_context(
    session: AsyncSession, 
    tenant_id: uuid.UUID, 
    user_id: Optional[int] = None,
    user_role: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Set comprehensive context for Row-Level Security and audit logging"""
    # Set tenant context (PostgreSQL SET doesn't support parameterized queries)
    await session.execute(
        text(f"SET app.current_tenant = '{str(tenant_id)}'")
    )
    
    # Set user context if provided
    if user_id is not None:
        await session.execute(
            text(f"SET app.current_user_id = '{str(user_id)}'")
        )
    
    # Set user role if provided
    if user_role:
        await session.execute(
            text(f"SET app.current_user_role = '{user_role}'")
        )
    
    # Set user agent for audit logging
    if user_agent:
        # Escape single quotes in user agent
        safe_user_agent = user_agent.replace("'", "''")
        await session.execute(
            text(f"SET app.user_agent = '{safe_user_agent}'")
        )