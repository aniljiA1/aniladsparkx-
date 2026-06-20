import json
from app.llm_client import chat_completion

VALID_PERSONAS = ["Technical Expert", "Frustrated User", "Business Executive"]

SYSTEM_INSTRUCTION = """You are an advanced classification engine for a customer support system.
Analyze the vocabulary, tone, and intent of the incoming support message and classify it into
EXACTLY ONE of these three customer personas:

1. "Technical Expert": Uses technical terminology, asks about APIs, logs, error codes,
   configurations, integrations, or wants detailed root-cause explanations.
2. "Frustrated User": Uses emotional language, exclamation marks, repeated complaints,
   urgency words ("immediately", "nothing works", "still broken"), or expresses dissatisfaction.
3. "Business Executive": Focused on business/operational impact, timelines, SLAs, cost,
   and prefers concise, outcome-oriented communication rather than technical detail.

Respond ONLY with a strict JSON object of the form:
{"persona": "<one of the three options>", "confidence": <float between 0 and 1>, "reasoning": "<one sentence>"}
"""


def classify_persona(user_message: str) -> dict:
    """Classifies a user's message into one of three personas using the LLM.

    Falls back to a deterministic rule-based heuristic if the LLM call fails
    or returns malformed output, so the system degrades gracefully.
    """
    try:
        raw = chat_completion(
            system_prompt=SYSTEM_INSTRUCTION,
            user_prompt=user_message,
            temperature=0.0,
            response_format_json=True,
        )
        parsed = json.loads(raw)
        if parsed.get("persona") in VALID_PERSONAS:
            parsed["confidence"] = float(parsed.get("confidence", 0.7))
            return parsed
    except Exception:
        pass

    return _rule_based_fallback(user_message)


def _rule_based_fallback(message: str) -> dict:
    text = message.lower()

    frustrated_signals = ["!", "nothing works", "still broken", "again and again",
                           "frustrat", "angry", "unacceptable", "fed up", "immediately"]
    technical_signals = ["api", "log", "error", "config", "endpoint", "token",
                          "auth", "database", "sdk", "code", "stack trace", "schema"]
    executive_signals = ["impact", "business", "timeline", "sla", "operations",
                          "revenue", "cost", "stakeholder", "resolution time"]

    scores = {
        "Frustrated User": sum(s in text for s in frustrated_signals),
        "Technical Expert": sum(s in text for s in technical_signals),
        "Business Executive": sum(s in text for s in executive_signals),
    }
    persona = max(scores, key=scores.get)
    if scores[persona] == 0:
        persona = "Business Executive"  # neutral default: concise, safe tone

    return {"persona": persona, "confidence": 0.5, "reasoning": "rule-based fallback classification"}
