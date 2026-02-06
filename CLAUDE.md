# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Robert is an AI-powered personal advisor chatbot that combines FastAPI, Google Gemini LLM, MongoDB, and Telegram Bot. The bot has a distinctive personality as a Cuban entrepreneur and financial/strategic advisor inspired by "Rich Dad Poor Dad", "48 Laws of Power", and "How to Win Friends and Influence People".

The system provides two interfaces:
- **Telegram Bot**: Primary interface for user interactions with conversational memory
- **REST API**: HTTP endpoints for programmatic access

## Development Commands

### Setup
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and MongoDB URI
```

### Running the Application

**Option 1: Telegram Bot + FastAPI (Recommended for Production)**
```bash
python bot_main.py
```
This runs both the Telegram bot and FastAPI server in a single process on port 8000 (or PORT env var).

**Option 2: FastAPI Only (Development/Testing)**
```bash
uvicorn main:app --reload
```
Runs only the API server on http://localhost:8000 with hot reload.

**Option 3: Both Separately (Development)**
```bash
# Terminal 1
uvicorn main:app --reload

# Terminal 2
python bot_main.py
```

### Testing the API
```bash
# Health check
curl http://localhost:8000/health

# Send chat message
curl -X POST http://localhost:8000/chat \
  -F 'message=¿Cuánto gasté este mes?' \
  -F 'session_id=test_user_123'

# With image
curl -X POST http://localhost:8000/chat \
  -F 'message=Analiza este recibo' \
  -F 'session_id=test_user_123' \
  -F 'image=@/path/to/image.jpg'

# Get chat history
curl http://localhost:8000/history/test_user_123?limit=10

# Clear history
curl -X DELETE http://localhost:8000/history/test_user_123
```

## Architecture

### Clean Architecture Layers

The codebase follows clean architecture with clear separation of concerns:

```
┌─────────────────────────────────────┐
│  Presentation Layer                 │
│  - main.py (FastAPI app)            │
│  - bot_main.py (Telegram runner)    │
│  - api/routes.py (HTTP endpoints)   │
│  - services/telegram_bot.py         │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Business Logic / Services          │
│  - services/gemini_service.py       │
│  - services/memory_service.py       │
│  - services/mongo_service.py        │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Data Layer                         │
│  - database/mongodb.py              │
│  - models/schemas.py                │
└─────────────────────────────────────┘
```

### Key Architectural Patterns

**1. Dual Initialization Pattern**
Both `main.py` and `bot_main.py` can initialize the database and Gemini clients. The lifespan manager in `main.py` checks if clients are already initialized (by `bot_main.py`) before re-initializing. This allows running either separately or together without conflicts.

**2. Module-Level Singletons with Lazy Init**
Database and Gemini clients use module-level globals (`db_client`, `gemini_client`) that are initialized via `init_db()` and `init_gemini()`. Services import these modules and access the live global values after initialization.

**Critical**: When importing `db_client` or `gemini_client`, import the module, not the value directly:
```python
# CORRECT - gets live value after init
import database.mongodb as db
collection = db.db_client[DB_NAME][COLLECTION]

# WRONG - captures None before init
from database.mongodb import db_client  # This captures None!
collection = db_client[DB_NAME][COLLECTION]  # Error: NoneType
```

**3. Structured LLM Responses**
Gemini is configured to return structured JSON conforming to `LLMResponse` schema using `response_schema` parameter. The response always includes:
- `reply`: Human-readable text in Robert's personality
- `operation`: Optional MongoDB operation to execute

**4. Per-User Session Memory**
- Telegram: Uses Telegram user ID as session ID
- REST API: Client provides session_id in requests
- History stored in `robert_memory.chats` collection
- Recent messages (last 20 by default) sent to Gemini for context

## MongoDB Collections

**Primary DB (`mydb.items`)**
- Contains business visit data from the "Llego" app
- Gemini can query/update this based on user requests
- Schema is dynamic (not enforced)

**Memory DB (`robert_memory.chats`)**
```javascript
{
  "sessionID": "telegram_user_id or custom_session_id",
  "role": "user" | "assistant",
  "message": "text content",
  "timestamp": ISODate("...")
}
```

## Gemini Integration

### Response Flow
1. User message + chat history → `ask_gemini()`
2. Gemini returns `LLMResponse` with structured JSON
3. If `operation.action != "none"`, execute via `execute_operation()`
4. Combine LLM reply + operation results
5. Save to chat history

### Supported MongoDB Operations
See `ActionEnum` in `models/schemas.py`:
- `find`, `find_one`: Query data
- `insert_one`, `insert_many`: Insert data
- `update_one`, `update_many`: Update data
- `delete_one`, `delete_many`: Delete data
- `aggregate`: Complex aggregations
- `count`: Count documents
- `none`: No database operation (conversation only)

### Error Handling
The service has robust fallback logic for parsing Gemini responses:
1. Try `response.parsed` (native Pydantic parsing)
2. Fallback to `response.text` with `model_validate_json()`
3. Last resort: extract from `response.candidates[0].content.parts[0].text`
4. If all fail, return error message

## Configuration & Environment

Required environment variables (`.env`):
- `GEMINI_API_KEY`: Google Gemini API key
- `TELEGRAM_BOT_TOKEN`: From [@BotFather](https://t.me/botfather)
- `MONGO_URI`: MongoDB connection string (default: `mongodb://localhost:27017`)

Optional:
- `DB_NAME`: Primary database (default: `mydb`)
- `COLLECTION`: Primary collection (default: `items`)
- `MEMORY_DB_NAME`: Memory database (default: `robert_memory`)
- `MEMORY_COLLECTION`: Memory collection (default: `chats`)
- `GEMINI_MODEL`: Model to use (default: `gemini-2.5-flash`)
- `PORT`: Server port (default: `8000`)

## Robert's Personality

Robert's persona is defined in `config/settings.py` as `SYSTEM_PROMPT`. Key traits:
- Cuban origin, global entrepreneur mindset
- Financial advisor (Rich Dad Poor Dad philosophy)
- Strategic thinker (48 Laws of Power)
- Diplomatic but direct (Dale Carnegie approach)
- Uses intelligent, ironic humor
- Adaptive attitude based on user performance
- Always ends with incisive questions or clear next actions
- Avoids AI-like phrases ("Como modelo de lenguaje...")

When modifying the personality, edit `SYSTEM_PROMPT` in `config/settings.py`.

## Telegram Bot Specifics

### Bot Conflict Prevention
On startup, `bot_main.py` clears previous webhook sessions and waits 5 seconds to avoid conflicts with old polling instances (important for redeployments):
```python
await bot_app.bot.delete_webhook(drop_pending_updates=True)
await asyncio.sleep(5)
```

### Handlers
- `/start`: Welcome message
- `/help`: Help information
- `/clear`: Clear chat history for user
- Text messages: Process with Gemini + history
- Photos: Download, analyze with Gemini vision capabilities

### Image Handling
Photos are downloaded as bytes and sent to Gemini with mime type `image/jpeg`. Caption (or default text) is used as the prompt.

## Common Patterns

### Adding New Telegram Commands
1. Define async handler in `services/telegram_bot.py`
2. Register in `create_bot_application()` with `CommandHandler`

### Adding New API Endpoints
1. Add route to `api/routes.py`
2. Use existing services (`gemini_service`, `mongo_service`, `memory_service`)
3. Follow pattern: get history → process → save to history

### Adding New MongoDB Operations
1. Add action to `ActionEnum` in `models/schemas.py`
2. Add case in `execute_operation()` in `services/mongo_service.py`
3. Update `SYSTEM_PROMPT` if needed to teach Gemini about new operation

## Deployment Notes

When deploying to production:
- Use `bot_main.py` as the entry point
- Set `PORT` environment variable for the web server
- Ensure MongoDB is accessible from the deployment environment
- The 5-second delay on bot startup prevents polling conflicts on redeploys
- Consider using a process manager (PM2, systemd) to auto-restart on crashes
