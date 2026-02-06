# Robert - Tu Asesor Personal Inteligente

Backend con Clean Architecture que combina FastAPI + Gemini + MongoDB + Telegram Bot.

## Características

- 🤖 **Bot de Telegram** con personalidad de Robert (asesor financiero y estratégico)
- 🧠 **Memoria conversacional** persistente por usuario
- 💾 **Base de datos MongoDB** para datos de la app Llego
- 🎯 **LLM Gemini** para procesamiento de lenguaje natural
- 🖼️ **Soporte de imágenes** vía Telegram
- 🏗️ **Clean Architecture** con separación de capas

## Estructura del Proyecto

```
Robert/
├── main.py                    # FastAPI server
├── bot_main.py               # Telegram bot runner
├── config/
│   └── settings.py           # Configuración
├── models/
│   └── schemas.py            # Pydantic schemas
├── database/
│   └── mongodb.py            # Conexión MongoDB
├── services/
│   ├── gemini_service.py     # Servicio Gemini LLM
│   ├── mongo_service.py      # Operaciones MongoDB
│   ├── memory_service.py     # Sistema de memoria
│   └── telegram_bot.py       # Bot de Telegram
└── api/
    └── routes.py             # Endpoints REST
```

## Instalación

1. **Clonar y entrar al proyecto**
```bash
cd Robert
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
```

Edita `.env` y agrega:
- `GEMINI_API_KEY`: Tu API key de Google Gemini
- `TELEGRAM_BOT_TOKEN`: Token de tu bot de Telegram (obtén uno con [@BotFather](https://t.me/botfather))
- `MONGO_URI`: URI de conexión a MongoDB

## Uso

### Opción 1: Solo Bot de Telegram

```bash
python bot_main.py
```

El bot estará disponible en Telegram. Cada usuario tiene su propia sesión automáticamente.

### Opción 2: Solo API REST (FastAPI)

```bash
uvicorn main:app --reload
```

Endpoints disponibles en `http://localhost:8000`:
- `POST /chat` - Enviar mensaje
- `GET /history/{session_id}` - Ver historial
- `DELETE /history/{session_id}` - Limpiar historial
- `GET /health` - Health check

### Opción 3: Ambos (recomendado)

En una terminal:
```bash
uvicorn main:app --reload
```

En otra terminal:
```bash
python bot_main.py
```

## Comandos del Bot de Telegram

- `/start` - Iniciar conversación con Robert
- `/help` - Ver ayuda
- `/clear` - Limpiar historial de conversación

## Personalidad de Robert

Robert es un asesor personal con:
- ✅ Origen cubano, empresario de mundo
- ✅ Experto en finanzas (Padre Rico, Padre Pobre)
- ✅ Estratega (48 Leyes del Poder)
- ✅ Diplomático (Dale Carnegie)
- ✅ Humor irónico e inteligente
- ✅ Directo y sin frases de IA

## Base de Datos

### DB Principal: `mydb.items`
Datos de la app Llego (negocios visitados)

### DB de Memoria: `robert_memory.chats`
Historial de conversaciones por usuario:
```json
{
  "sessionID": "telegram_user_id",
  "role": "user|assistant",
  "message": "texto del mensaje",
  "timestamp": "2024-..."
}
```

## API REST Ejemplos

### Chat con memoria
```bash
curl -X POST http://localhost:8000/chat \
  -F 'message=¿Cuánto gasté este mes?' \
  -F 'session_id=user_123'
```

### Con imagen
```bash
curl -X POST http://localhost:8000/chat \
  -F 'message=Analiza este recibo' \
  -F 'session_id=user_123' \
  -F 'image=@recibo.jpg'
```

### Ver historial
```bash
curl http://localhost:8000/history/user_123?limit=10
```

### Limpiar historial
```bash
curl -X DELETE http://localhost:8000/history/user_123
```

## Tecnologías

- **FastAPI** - API REST
- **Python Telegram Bot** - Integración con Telegram
- **Motor** - MongoDB async driver
- **Google Gemini** - LLM para procesamiento
- **Pydantic** - Validación de datos

## Desarrollo

Para modificar la personalidad de Robert, edita:
- `config/settings.py` - `SYSTEM_PROMPT`

Para agregar nuevos comandos al bot:
- `services/telegram_bot.py`

## Licencia

Proyecto personal
