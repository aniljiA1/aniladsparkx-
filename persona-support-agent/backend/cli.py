import json
import uuid
import requests

API_BASE = "http://localhost:8000"


def main():
    session_id = str(uuid.uuid4())
    print("=" * 70)
    print(" Persona-Adaptive Customer Support Agent — CLI")
    print(" Type 'exit' to quit.")
    print("=" * 70)

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break
        if not user_input:
            continue

        try:
            resp = requests.post(
                f"{API_BASE}/chat",
                json={"message": user_input, "session_id": session_id},
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[Error contacting backend: {e}]")
            continue

        print(f"\n[Detected Persona]: {data['persona']} (confidence: {data.get('persona_confidence')})")
        if data["retrieved_sources"]:
            print("[Retrieved Sources]:")
            for s in data["retrieved_sources"]:
                loc = f"page {s['page']}" if s.get("page") else s.get("section", "")
                print(f"   - {s['source']} ({loc}) score={s['score']}")
        else:
            print("[Retrieved Sources]: none")

        print(f"\nAgent: {data['response']}")

        if data["escalated"]:
            print("\n*** ESCALATED TO HUMAN SUPPORT ***")
            print("Reasons:", ", ".join(data["escalation_reasons"]))
            print("Handoff Summary:")
            print(json.dumps(data["handoff_summary"], indent=2, default=str))


if __name__ == "__main__":
    main()
