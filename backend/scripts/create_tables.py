"""Script to create database tables."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import init_db, close_db


async def main():
    """Create all database tables."""
    print("Creating database tables...")
    try:
        await init_db()
        print("✓ Database tables created successfully!")
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        raise
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())

