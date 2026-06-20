import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Google Gemini — free tier API key from https://aistudio.google.com/apikey
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    CHAT_MODEL: str = os.environ.get("CHAT_MODEL", "gemini-2.0-flash")
    EMBEDDING_MODEL: str = os.environ.get("EMBEDDING_MODEL", "text-embedding-004")

    MONGO_URI: str = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.environ.get("MONGO_DB_NAME", "persona_support_agent")

    CHUNK_SIZE: int = int(os.environ.get("CHUNK_SIZE", 500))
    CHUNK_OVERLAP: int = int(os.environ.get("CHUNK_OVERLAP", 50))
    TOP_K: int = int(os.environ.get("TOP_K", 3))

    # Escalation configuration
    RETRIEVAL_CONFIDENCE_THRESHOLD: float = float(os.environ.get("RETRIEVAL_CONFIDENCE_THRESHOLD", 0.45))
    MAX_FRUSTRATED_TURNS_BEFORE_ESCALATION: int = int(os.environ.get("MAX_FRUSTRATED_TURNS_BEFORE_ESCALATION", 2))
    SENSITIVE_KEYWORDS = [
        "refund", "chargeback", "legal", "lawsuit", "dispute", "fraud",
        "delete my account", "gdpr", "subpoena", "cancel subscription",
        "unauthorized charge", "duplicate charge", "billing dispute",
    ]

    DATA_DIR: str = os.path.join(os.path.dirname(__file__), "data")


settings = Settings()
