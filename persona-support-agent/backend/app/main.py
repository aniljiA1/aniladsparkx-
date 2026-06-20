import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import settings
from app.db import conversations_collection, escalations_collection, chunks_collection, init_indexes
from app.classifier import classify_persona
from app.rag_pipeline import retrieve_context, ingest_knowledge_base
from app.generator import generate_response
from app.escalator import should_escalate, build_handoff_summary

app = FastAPI(title="Persona-Adaptive Customer Support Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_indexes()
    if chunks_collection.count_documents({}) == 0:
        ingest_knowledge_base()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class IngestRequest(BaseModel):
    force: bool = False


@app.get("/health")
def health():
    return {"status": "ok", "kb_chunks": chunks_collection.count_documents({})}


@app.post("/ingest")
def ingest(req: IngestRequest):
    result = ingest_knowledge_base(force=req.force)
    return result


@app.post("/chat")
def chat(req: ChatRequest):
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")

    session_id = req.session_id or str(uuid.uuid4())

    try:
        return _handle_chat(req.message, session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")


def _handle_chat(message: str, session_id: str):
    req_message = message
    # Load prior conversation history for this session
    history = list(
        conversations_collection.find({"session_id": session_id}, {"_id": 0}).sort("timestamp", 1)
    )

    # 1. Persona detection
    persona_result = classify_persona(req_message)
    persona = persona_result["persona"]

    # 2. Retrieval
    context_chunks = retrieve_context(req_message)

    # 3. Escalation check
    escalation_decision = should_escalate(req_message, persona, context_chunks, history)

    response_text = None
    handoff_summary = None

    if escalation_decision["escalate"]:
        handoff_summary = build_handoff_summary(
            session_id=session_id,
            persona=persona,
            message=req_message,
            history=history,
            context_chunks=context_chunks,
            reasons=escalation_decision["reasons"],
        )
        escalations_collection.insert_one({**handoff_summary, "timestamp": datetime.utcnow()})
        response_text = (
            "I'm escalating this to a human support specialist who can take care of this for you. "
            "They will have the full context of our conversation."
        )
    else:
        # 4. Adaptive response generation (grounded in retrieved context only)
        response_text = generate_response(req_message, persona, context_chunks)

    # Persist this turn
    conversations_collection.insert_one({
        "session_id": session_id,
        "role": "user",
        "message": req_message,
        "persona": persona,
        "timestamp": datetime.utcnow(),
    })
    conversations_collection.insert_one({
        "session_id": session_id,
        "role": "assistant",
        "message": response_text,
        "persona": persona,
        "timestamp": datetime.utcnow(),
    })

    return {
        "session_id": session_id,
        "persona": persona,
        "persona_confidence": persona_result.get("confidence"),
        "persona_reasoning": persona_result.get("reasoning"),
        "retrieved_sources": [
            {"source": c["source"], "page": c.get("page"), "section": c.get("section"), "score": c["score"]}
            for c in context_chunks
        ],
        "response": response_text,
        "escalated": escalation_decision["escalate"],
        "escalation_reasons": escalation_decision["reasons"],
        "handoff_summary": handoff_summary,
    }


@app.get("/history/{session_id}")
def get_history(session_id: str):
    history = list(
        conversations_collection.find({"session_id": session_id}, {"_id": 0}).sort("timestamp", 1)
    )
    return {"session_id": session_id, "history": history}


@app.get("/escalations")
def list_escalations():
    items = list(escalations_collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(50))
    return {"escalations": items}