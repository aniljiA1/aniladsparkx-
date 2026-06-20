from app.config import settings


def contains_sensitive_topic(message: str) -> bool:
    text = message.lower()
    return any(keyword in text for keyword in settings.SENSITIVE_KEYWORDS)


def is_low_confidence(context_chunks: list) -> bool:
    if not context_chunks:
        return True
    best_score = max(c["score"] for c in context_chunks)
    return best_score < settings.RETRIEVAL_CONFIDENCE_THRESHOLD


def repeated_frustration(history: list, current_persona: str) -> bool:
    """Checks if the user has been classified as 'Frustrated User' for
    MAX_FRUSTRATED_TURNS_BEFORE_ESCALATION consecutive turns (including current)."""
    if current_persona != "Frustrated User":
        return False
    recent = [h for h in history if h.get("role") == "user"][-(settings.MAX_FRUSTRATED_TURNS_BEFORE_ESCALATION):]
    if len(recent) < settings.MAX_FRUSTRATED_TURNS_BEFORE_ESCALATION:
        return False
    return all(h.get("persona") == "Frustrated User" for h in recent)


def should_escalate(message: str, persona: str, context_chunks: list, history: list) -> dict:
    """Evaluates all configured escalation triggers and returns a structured decision."""
    reasons = []

    if not context_chunks:
        reasons.append("No relevant information found in the knowledge base.")
    elif is_low_confidence(context_chunks):
        reasons.append(
            f"Retrieval confidence is below threshold ({settings.RETRIEVAL_CONFIDENCE_THRESHOLD})."
        )

    if contains_sensitive_topic(message):
        reasons.append("Message involves a billing, legal, or account-sensitive issue.")

    if repeated_frustration(history, persona):
        reasons.append("User has remained dissatisfied (Frustrated User) across multiple turns.")

    return {
        "escalate": len(reasons) > 0,
        "reasons": reasons,
    }


def build_handoff_summary(session_id: str, persona: str, message: str,
                           history: list, context_chunks: list, reasons: list) -> dict:
    attempted_steps = [
        h.get("message") for h in history if h.get("role") == "user"
    ][:-1]  # all prior user messages excluding the current one

    documents_used = sorted(set(c["source"] for c in context_chunks)) if context_chunks else []

    recommendation = "Review conversation history and resolve manually."
    if "billing" in " ".join(reasons).lower() or any(
        kw in message.lower() for kw in ["refund", "duplicate charge", "billing dispute"]
    ):
        recommendation = "Route to billing team for manual review of charge/refund dispute."
    elif "legal" in " ".join(reasons).lower():
        recommendation = "Route to legal/compliance team before responding to customer."
    elif not context_chunks:
        recommendation = "No matching documentation found; investigate as a potential new/undocumented issue."
    elif persona == "Frustrated User":
        recommendation = "Prioritize immediate human follow-up given repeated dissatisfaction."

    return {
        "session_id": session_id,
        "persona": persona,
        "issue": message,
        "conversation_history": history,
        "documents_used": documents_used,
        "attempted_steps": attempted_steps,
        "escalation_reasons": reasons,
        "recommendation": recommendation,
    }
