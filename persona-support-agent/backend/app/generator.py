from app.llm_client import chat_completion

PERSONA_INSTRUCTIONS = {
    "Technical Expert": (
        "You are a Senior Systems Engineer responding to a technically advanced customer. "
        "Provide a detailed root-cause analysis, precise configuration/API details, and a "
        "clear step-by-step troubleshooting path. Use technical language freely and be exact."
    ),
    "Frustrated User": (
        "You are an empathetic, reassuring Customer Care Specialist. Begin with a brief, "
        "genuine acknowledgement of the customer's frustration. Use simple, plain language, "
        "avoid jargon, and give clear action-oriented steps as a short bulleted list. "
        "Be warm and reassuring throughout."
    ),
    "Business Executive": (
        "You are a concise Client Relations Director speaking to a business executive. "
        "Be brief and outcome-focused. Lead with the direct answer and business impact, "
        "include an estimated resolution timeframe if relevant, and minimize technical jargon."
    ),
}

BASE_RULES = (
    "\n\nCRITICAL RULES:\n"
    "- Base your response ONLY on the FACTUAL CONTEXT DOCUMENTS provided below.\n"
    "- Do NOT invent facts, policies, or steps that are not present in the context.\n"
    "- If the context does not fully answer the question, say so honestly rather than guessing.\n"
    "- Keep the response focused and well-structured for the customer's persona."
)


def generate_response(user_message: str, persona: str, context_chunks: list) -> str:
    persona_instruction = PERSONA_INSTRUCTIONS.get(persona, PERSONA_INSTRUCTIONS["Business Executive"])

    context_text = "\n\n".join(
        f"Source [{c['source']}"
        f"{', page ' + str(c['page']) if c.get('page') else ''}"
        f"{', ' + c['section'] if c.get('section') else ''}]: {c['text']}"
        for c in context_chunks
    ) if context_chunks else "No relevant context was found."

    system_prompt = (
        f"{persona_instruction}{BASE_RULES}\n\n"
        f"FACTUAL CONTEXT DOCUMENTS:\n{context_text}"
    )

    return chat_completion(system_prompt=system_prompt, user_prompt=user_message, temperature=0.3)
