"""
Robert Bot — Entry point
Runs Telegram bot + FastAPI server in one process.
"""
import os
import asyncio
import uvicorn
from database.mongodb import init_db, close_db
from services.gemini_service import init_gemini
from services.telegram_bot import create_bot_application
from main import app


async def start():
    print("Inicializando Robert Bot...")

    # Initialize database and Gemini
    init_db()
    init_gemini()

    print("Conexiones inicializadas")

    # --- Telegram Bot ---
    bot_app = create_bot_application()
    await bot_app.initialize()
    # Delete any existing webhook and drop pending updates from previous instance
    await bot_app.bot.delete_webhook(drop_pending_updates=True)
    await bot_app.start()
    await bot_app.updater.start_polling(drop_pending_updates=True)
    print("Robert Bot corriendo en Telegram...")

    # --- FastAPI server ---
    port = int(os.getenv("PORT", "8000"))
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    print(f"Servidor web en puerto {port}")

    try:
        await server.serve()
    finally:
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()
        close_db()
        print("Robert Bot detenido")


if __name__ == "__main__":
    asyncio.run(start())
