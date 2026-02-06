"""
MongoDB database connection and utilities
"""
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import MONGO_URI, DB_NAME, COLLECTION

# ──────────────────────────── Globals ───────────────────────────

db_client: AsyncIOMotorClient = None


# ──────────────────────────── Connection ────────────────────────


def init_db():
    """Initialize MongoDB client"""
    global db_client
    db_client = AsyncIOMotorClient(MONGO_URI)
    return db_client


def close_db():
    """Close MongoDB connection"""
    if db_client:
        db_client.close()


def get_collection():
    """Get the configured collection"""
    return db_client[DB_NAME][COLLECTION]


async def ping_db():
    """Check database connection"""
    try:
        await db_client.admin.command("ping")
        return True
    except Exception:
        return False
