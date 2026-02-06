"""
Gemini LLM service for processing natural language queries
"""
from google import genai
from google.genai import types

from config.settings import GEMINI_MODEL, SYSTEM_PROMPT
from models.schemas import LLMResponse

# ──────────────────────────── Globals ───────────────────────────

gemini_client: genai.Client = None


# ──────────────────────────── Client Init ───────────────────────


def init_gemini():
    """Initialize Gemini client (reads GEMINI_API_KEY from env automatically)"""
    global gemini_client
    gemini_client = genai.Client()
    return gemini_client


# ──────────────────────────── LLM Call ──────────────────────────


async def ask_gemini(
    message: str,
    image_bytes: bytes | None = None,
    image_mime: str | None = None,
    history: list[dict] | None = None,
) -> LLMResponse:
    """
    Ask Gemini to interpret the message and return structured response
    with MongoDB operation if needed
    """
    # Build conversation with Content objects
    contents = []

    # Add history if provided
    if history:
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["message"])]
                )
            )

    # Add current message
    current_parts = [types.Part.from_text(text=message)]
    if image_bytes and image_mime:
        current_parts.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime))

    contents.append(
        types.Content(role="user", parts=current_parts)
    )

    response = await gemini_client.aio.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=LLMResponse,
            temperature=0.1,
        ),
    )

    # .parsed devuelve el objeto parseado según el schema
    if response.parsed and isinstance(response.parsed, LLMResponse):
        return response.parsed

    # Fallback: parsear manualmente si hay texto
    try:
        raw = response.text
        if raw:
            return LLMResponse.model_validate_json(raw)
    except (TypeError, IndexError, AttributeError):
        pass

    # Último recurso: respuesta vacía
    return LLMResponse(reply="No pude procesar tu mensaje. Intenta de nuevo.", operation=None)
