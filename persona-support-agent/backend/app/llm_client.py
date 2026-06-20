from google import genai
from google.genai import types

from app.config import settings

_client = None


def _get_client():
    global _client
    if _client is None:
        if not settings.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Get a free key at "
                "https://aistudio.google.com/apikey and add it to backend/.env"
            )
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def get_embedding(text: str) -> list:
    text = text.replace("\n", " ").strip()
    if not text:
        text = " "
    client = _get_client()
    model_name = settings.EMBEDDING_MODEL
    if not model_name.startswith("models/"):
        model_name = f"models/{model_name}"
    response = client.models.embed_content(
        model=model_name,
        contents=text,
    )
    return response.embeddings[0].values


def chat_completion(system_prompt: str, user_prompt: str, temperature: float = 0.2,
                     response_format_json: bool = False) -> str:
    client = _get_client()

    config_kwargs = {
        "system_instruction": system_prompt,
        "temperature": temperature,
    }
    if response_format_json:
        config_kwargs["response_mime_type"] = "application/json"

    model_name = settings.CHAT_MODEL
    if not model_name.startswith("models/"):
        model_name = f"models/{model_name}"

    response = client.models.generate_content(
        model=model_name,
        contents=user_prompt,
        config=types.GenerateContentConfig(**config_kwargs),
    )
    if not response.text:
        raise RuntimeError(
            f"Gemini returned no text. Full response: {response}"
        )
    return response.text