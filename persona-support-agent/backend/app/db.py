from pymongo import MongoClient
from app.config import settings

_client = MongoClient(settings.MONGO_URI)
db = _client[settings.MONGO_DB_NAME]

# Collections
chunks_collection = db["kb_chunks"]            # stores text chunks + embeddings + metadata
conversations_collection = db["conversations"]  # stores conversation turns per session
escalations_collection = db["escalations"]      # stores generated handoff summaries


def init_indexes():
    chunks_collection.create_index("source")
    conversations_collection.create_index("session_id")
    escalations_collection.create_index("session_id")
