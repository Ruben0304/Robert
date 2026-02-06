"""
Memory service for storing and retrieving chat history
"""
from datetime import datetime
from typing import List, Dict
import database.mongodb as db
from config.settings import MEMORY_DB_NAME, MEMORY_COLLECTION


def get_memory_collection():
    """Get the memory collection"""
    return db.db_client[MEMORY_DB_NAME][MEMORY_COLLECTION]


async def save_message(session_id: str, role: str, message: str):
    """
    Save a message to chat history

    Args:
        session_id: Unique identifier for the conversation session
        role: Either 'user' or 'assistant'
        message: The message content
    """
    col = get_memory_collection()
    await col.insert_one({
        "sessionID": session_id,
        "role": role,
        "message": message,
        "timestamp": datetime.utcnow()
    })


async def get_chat_history(session_id: str, limit: int = 20) -> List[Dict[str, str]]:
    """
    Retrieve chat history for a session

    Args:
        session_id: Unique identifier for the conversation session
        limit: Maximum number of messages to retrieve (default 20)

    Returns:
        List of messages in format [{"role": "user", "message": "..."}, ...]
    """
    col = get_memory_collection()
    cursor = col.find(
        {"sessionID": session_id}
    ).sort("timestamp", 1).limit(limit)

    messages = await cursor.to_list(length=limit)

    return [
        {"role": msg["role"], "message": msg["message"]}
        for msg in messages
    ]


async def clear_session_history(session_id: str):
    """
    Clear all chat history for a specific session

    Args:
        session_id: Unique identifier for the conversation session
    """
    col = get_memory_collection()
    await col.delete_many({"sessionID": session_id})
