"""
Pydantic models and schemas
"""
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


# ──────────────── Pydantic Schemas (Gemini los respeta) ─────────


class ActionEnum(str, Enum):
    find = "find"
    find_one = "find_one"
    insert_one = "insert_one"
    insert_many = "insert_many"
    update_one = "update_one"
    update_many = "update_many"
    delete_one = "delete_one"
    delete_many = "delete_many"
    aggregate = "aggregate"
    count = "count"
    none = "none"


class MongoOperation(BaseModel):
    action: ActionEnum = Field(description="Operación MongoDB a ejecutar")
    filter: Optional[Any] = Field(
        default=None, description="Filtro para find/update/delete"
    )
    data: Optional[Any] = Field(
        default=None,
        description="Datos para insert_one (dict) o insert_many (list)",
    )
    update: Optional[Any] = Field(
        default=None, description="Update con operadores $set, $inc, etc."
    )
    pipeline: Optional[Any] = Field(
        default=None, description="Pipeline para aggregate"
    )


class LLMResponse(BaseModel):
    """Schema que Gemini DEBE devolver."""

    reply: str = Field(description="Texto de respuesta para el usuario")
    is_final: bool = Field(
        description="True cuando ya tienes suficiente información y la respuesta es final"
    )
    operation: Optional[MongoOperation] = Field(
        default=None,
        description="Operación MongoDB, null si solo es conversación",
    )


# ──────────────────── API Response ──────────────────────────────


class ChatResponse(BaseModel):
    reply: str
    operation: Optional[Any] = None
    data: Optional[Any] = None
