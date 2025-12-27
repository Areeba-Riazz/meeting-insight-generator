"""Database configuration and connection management."""

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/meeting_insights",
)

# Connection pool settings
DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "10"))
DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    pool_size=DATABASE_POOL_SIZE,
    max_overflow=DATABASE_MAX_OVERFLOW,
    echo=False,  # Set to True for SQL query logging
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function for FastAPI to get database session.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db)):
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
    """Initialize database by creating all tables."""
    from src.models.db_models import (
        Project,
        Meeting,
        Transcript,
        TranscriptSegment,
        Topic,
        Decision,
        ActionItem,
        SentimentAnalysis,
        SentimentSegment,
        Summary,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def ensure_tables_exist() -> None:
    """
    Ensure all database tables exist. Safe to call multiple times.
    Creates tables if they don't exist, does nothing if they already exist.
    """
    try:
        await init_db()
        print("[Database] Tables verified/created successfully")
    except Exception as e:
        print(f"[Database] Warning: Could not verify/create tables: {e}")
        # Don't raise - allow app to start even if DB connection fails
        # (for backward compatibility with filesystem-only mode)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()

