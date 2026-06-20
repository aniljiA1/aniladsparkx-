import os
import glob
import numpy as np
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings
from app.db import chunks_collection
from app.llm_client import get_embedding


def _read_txt_or_md(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _read_pdf(path: str) -> list:
    """Returns a list of (page_number, text) tuples."""
    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append((i + 1, text))
    return pages


def _chunk_text(text: str) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )
    return splitter.split_text(text)


def ingest_knowledge_base(data_dir: str = None, force: bool = False) -> dict:
    """Loads every document in data_dir, chunks it, embeds each chunk locally,
    and stores it in MongoDB along with metadata (source document + page/section).
    """
    data_dir = data_dir or settings.DATA_DIR

    if force:
        chunks_collection.delete_many({})
    elif chunks_collection.count_documents({}) > 0:
        return {"status": "skipped", "reason": "knowledge base already ingested",
                "existing_chunks": chunks_collection.count_documents({})}

    files = sorted(
        glob.glob(os.path.join(data_dir, "*.txt"))
        + glob.glob(os.path.join(data_dir, "*.md"))
        + glob.glob(os.path.join(data_dir, "*.pdf"))
    )

    total_chunks = 0
    documents_processed = []

    for filepath in files:
        filename = os.path.basename(filepath)
        ext = filename.split(".")[-1].lower()

        if ext == "pdf":
            pages = _read_pdf(filepath)
            for page_num, page_text in pages:
                for idx, chunk in enumerate(_chunk_text(page_text)):
                    if not chunk.strip():
                        continue
                    _store_chunk(filename, chunk, page=page_num, section=None)
                    total_chunks += 1
        else:
            text = _read_txt_or_md(filepath)
            for idx, chunk in enumerate(_chunk_text(text)):
                if not chunk.strip():
                    continue
                _store_chunk(filename, chunk, page=None, section=f"chunk_{idx}")
                total_chunks += 1

        documents_processed.append(filename)

    return {
        "status": "ingested",
        "documents_processed": documents_processed,
        "total_chunks": total_chunks,
    }


def _store_chunk(source: str, text: str, page: int = None, section: str = None):
    embedding = get_embedding(text)
    chunks_collection.insert_one({
        "source": source,
        "page": page,
        "section": section,
        "text": text,
        "embedding": embedding,
    })


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def retrieve_context(query: str, top_k: int = None) -> list:
    """Embeds the query and performs cosine-similarity search over all stored chunks.

    Returns a list of dicts: {text, source, page, section, score}, sorted by
    descending similarity score (highest confidence first).
    """
    top_k = top_k or settings.TOP_K
    query_vector = np.array(get_embedding(query))

    all_chunks = list(chunks_collection.find({}, {"text": 1, "source": 1, "page": 1,
                                                     "section": 1, "embedding": 1}))
    if not all_chunks:
        return []

    scored = []
    for c in all_chunks:
        score = _cosine_similarity(query_vector, np.array(c["embedding"]))
        scored.append({
            "text": c["text"],
            "source": c["source"],
            "page": c.get("page"),
            "section": c.get("section"),
            "score": round(score, 4),
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]
