"""
Gemini LLM service for processing natural language queries
"""
import json
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

    try:
        response = await gemini_client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=LLMResponse,
                temperature=0.6,
            ),
        )
    except Exception as e:
        print(f"[GEMINI ERROR] API call failed: {e}")
        return LLMResponse(reply=f"Error llamando a Gemini: {e}", operation=None)

    # Try to parse the response
    try:
        if response.parsed and isinstance(response.parsed, LLMResponse):
            return response.parsed
    except Exception as e:
        print(f"[GEMINI ERROR] response.parsed failed: {e}")

    # Fallback: try response.text
    try:
        raw = response.text
        if raw:
            return LLMResponse.model_validate_json(raw)
    except Exception as e:
        print(f"[GEMINI ERROR] response.text failed: {e}")

    # Last fallback: try candidates directly
    try:
        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                text = candidate.content.parts[0].text
                if text:
                    return LLMResponse.model_validate_json(text)
            # Check if blocked
            if candidate.finish_reason:
                print(f"[GEMINI ERROR] finish_reason: {candidate.finish_reason}")
    except Exception as e:
        print(f"[GEMINI ERROR] candidates fallback failed: {e}")

    print(f"[GEMINI ERROR] Full response object: {response}")
    return LLMResponse(reply="No pude procesar tu mensaje. Intenta de nuevo.", operation=None)
