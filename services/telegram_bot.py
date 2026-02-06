"""
Telegram bot service for Robert
"""
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from config.settings import TELEGRAM_BOT_TOKEN
from services.gemini_service import run_agent
from services.memory_service import save_message, get_chat_history, clear_session_history


# ──────────────────────────── Bot Handlers ──────────────────────


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command"""
    user_id = update.effective_user.id
    welcome_message = (
        "¡Qué pasa! Soy Robert, tu asesor personal.\n\n"
        "Estoy aquí para ayudarte con tus finanzas, proyectos y estrategia.\n"
        "Tengo acceso a tus datos de Llego y puedo analizar tus hábitos de gasto.\n\n"
        "Comandos disponibles:\n"
        "/start - Mensaje de bienvenida\n"
        "/clear - Limpiar historial de conversación\n"
        "/help - Ayuda\n\n"
        "Escríbeme lo que necesites y te respondo."
    )
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /help command"""
    help_message = (
        "🤖 *Robert - Tu asesor personal*\n\n"
        "Puedo ayudarte con:\n"
        "• Análisis de gastos y finanzas\n"
        "• Estrategia de negocios\n"
        "• Consejos sobre proyectos personales\n"
        "• Consultas sobre tus datos de Llego\n\n"
        "Comandos:\n"
        "/start - Iniciar conversación\n"
        "/clear - Limpiar memoria\n"
        "/help - Este mensaje\n\n"
        "Solo escríbeme y conversamos."
    )
    await update.message.reply_text(help_message, parse_mode="Markdown")


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /clear command - clears chat history"""
    user_id = str(update.effective_user.id)
    await clear_session_history(user_id)
    await update.message.reply_text(
        "Listo, he limpiado tu historial. Empezamos de cero."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle text messages from users
    Each user's Telegram ID is used as their unique session_id
    """
    user_id = str(update.effective_user.id)
    message_text = update.message.text

    print(f"[BOT] Mensaje recibido de {user_id}: {message_text[:50]}")

    # Send typing indicator
    await update.message.chat.send_action("typing")

    try:
        # Get chat history
        print(f"[BOT] Obteniendo historial...")
        history = await get_chat_history(user_id)
        print(f"[BOT] Historial: {len(history)} mensajes")

        # Save user message
        await save_message(user_id, "user", message_text)
        print(f"[BOT] Mensaje guardado")

        # Ask Gemini with agent loop
        print(f"[BOT] Llamando a Gemini (agent loop)...")
        llm, _steps = await run_agent(message_text, history=history)
        print(f"[BOT] Respuesta de Gemini: {llm.reply[:80]}")

        # Save assistant reply
        await save_message(user_id, "assistant", llm.reply)

        # Send reply to user
        await update.message.reply_text(llm.reply)
        print(f"[BOT] Respuesta enviada")

    except Exception as e:
        import traceback
        print(f"[BOT ERROR] {traceback.format_exc()}")
        error_message = f"Algo salió mal, hermano. Intenta de nuevo.\n\nError: {str(e)}"
        await update.message.reply_text(error_message)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle photo messages from users
    """
    user_id = str(update.effective_user.id)
    caption = update.message.caption or "Analiza esta imagen"

    # Send typing indicator
    await update.message.chat.send_action("typing")

    try:
        # Get the largest photo size
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()

        # Download photo as bytes
        photo_bytes = await photo_file.download_as_bytearray()

        # Determine mime type (Telegram photos are usually JPEG)
        image_mime = "image/jpeg"

        # Get chat history
        history = await get_chat_history(user_id)

        # Save user message (text only, not image)
        await save_message(user_id, "user", f"[Imagen enviada] {caption}")

        # Ask Gemini with image and history (agent loop)
        llm, _steps = await run_agent(caption, bytes(photo_bytes), image_mime, history)

        # Save assistant reply
        await save_message(user_id, "assistant", llm.reply)

        # Send reply
        await update.message.reply_text(llm.reply)

    except Exception as e:
        error_message = f"No pude procesar la imagen. Error: {str(e)}"
        await update.message.reply_text(error_message)


# ──────────────────────────── Bot Setup ─────────────────────────


def create_bot_application():
    """
    Create and configure the Telegram bot application
    """
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN no está configurado en el .env")

    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_command))

    # Handle photos
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Handle text messages (but not commands)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return application


async def run_bot():
    """
    Run the Telegram bot
    """
    application = create_bot_application()

    # Start polling
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    print("🤖 Robert Bot está corriendo...")

    # Keep running
    try:
        await asyncio.Event().wait()
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
