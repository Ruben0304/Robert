"""
API endpoints
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from models.schemas import ChatResponse, ActionEnum
from services.gemini_service import ask_gemini
from services.mongo_service import execute_operation
from services.memory_service import save_message, get_chat_history, clear_session_history
from database.mongodb import ping_db

router = APIRouter()


# ──────────────────────────── Endpoints ─────────────────────────


@router.post("/chat", response_model=ChatResponse)
async def chat(
    message: str = Form(...),
    session_id: str = Form(...),
    image: UploadFile | None = File(default=None),
):
    """
    Mensaje + imagen opcional → LLM → MongoDB CRUD con memoria.

    Args:
        message: Mensaje del usuario
        session_id: ID único de la sesión de conversación
        image: Imagen opcional
    """
    image_bytes = None
    image_mime = None

    if image:
        image_bytes = await image.read()
        image_mime = image.content_type

    # Get chat history
    history = await get_chat_history(session_id)

    # Save user message to history (without image, only text)
    await save_message(session_id, "user", message)

    # Ask Gemini with history
    llm = await ask_gemini(message, image_bytes, image_mime, history)

    data = None
    op_dict = None

    if llm.operation and llm.operation.action != ActionEnum.none:
        op_dict = llm.operation.model_dump(exclude_none=True)
        try:
            data = await execute_operation(llm.operation)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"MongoDB error: {e}")

    # Save assistant reply to history
    await save_message(session_id, "assistant", llm.reply)

    return ChatResponse(reply=llm.reply, operation=op_dict, data=data)


@router.get("/health")
async def health():
    db_connected = await ping_db()
    return {
        "status": "ok",
        "db": "connected" if db_connected else "disconnected"
    }


@router.get("/history/{session_id}")
async def get_history(session_id: str, limit: int = 20):
    """
    Get chat history for a session

    Args:
        session_id: ID de la sesión
        limit: Número máximo de mensajes a retornar (default 20)
    """
    history = await get_chat_history(session_id, limit)
    return {"session_id": session_id, "history": history}


@router.delete("/history/{session_id}")
async def delete_history(session_id: str):
    """
    Clear chat history for a session

    Args:
        session_id: ID de la sesión a limpiar
    """
    await clear_session_history(session_id)
    return {"message": f"History cleared for session {session_id}"}
