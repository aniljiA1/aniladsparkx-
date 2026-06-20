import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY", "")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=api_key)

print("Models that support generateContent (chat):")
for m in client.models.list():
    if "generateContent" in (m.supported_actions or []):
        print(" -", m.name)

print("\nModels that support embedContent (embeddings):")
for m in client.models.list():
    if "embedContent" in (m.supported_actions or []):
        print(" -", m.name)