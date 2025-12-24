#!/usr/bin/env python3
"""
Database setup script for Meeting Insight Generator.

This script initializes the database, creates tables, and optionally seeds test data.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.core.database import get_async_session, engine
from src.core.config import settings


async def create_tables():
    """Create all database tables."""
    print("Creating database tables...")
    async with engine.begin() as conn:
        # Import all models to ensure they're registered
        from src.models import meeting, transcript, insight  # noqa: F401
        
        # Create tables
        from src.models import Base
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Database tables created successfully")


async def check_connection():
    """Check database connection."""
    print("Checking database connection...")
    try:
        async with get_async_session() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
        print("✓ Database connection successful")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


async def main():
    """Main setup function."""
    print("=" * 50)
    print("Meeting Insight Generator - Database Setup")
    print("=" * 50)
    print()
    
    # Check connection
    if not await check_connection():
        print("\nPlease ensure PostgreSQL is running and DATABASE_URL is correct.")
        sys.exit(1)
    
    # Create tables
    await create_tables()
    
    print()
    print("=" * 50)
    print("Database setup complete!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Run migrations: alembic upgrade head")
    print("2. Start the API: uvicorn main:app --reload  # run from backend/")


if __name__ == "__main__":
    asyncio.run(main())

