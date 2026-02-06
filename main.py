"""
FastAPI + Gemini (google-genai SDK) + Motor — CRUD via LLM
Gemini devuelve un schema Pydantic estructurado con la operación MongoDB.
Soporta texto e imágenes.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI

from database.mongodb import init_db, close_db
from services.gemini_service import init_gemini
from api.routes import router


# ──────────────────────────── Lifespan ──────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — only init if not already initialized (bot_main does it first)
    from database.mongodb import db_client
    from services.gemini_service import gemini_client
    if db_client is None:
        init_db()
    if gemini_client is None:
        init_gemini()
    yield
    # Shutdown
    close_db()


# ──────────────────────────── App ───────────────────────────────


app = FastAPI(title="Robert API", lifespan=lifespan)

# Include routes
app.include_router(router)
