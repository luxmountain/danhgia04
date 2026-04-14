import os
from openai import OpenAI

_client = None

SYSTEM_PROMPT = (
    "You are a helpful e-commerce assistant. Use the provided context about products "
    "and user history to give accurate, concise recommendations. "
    "If the context is insufficient, say so honestly."
)


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def chat(user_query: str, context: str, history: list[dict] | None = None) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({
        "role": "user",
        "content": f"Context:\n{context}\n\nQuestion: {user_query}",
    })
    resp = _get_client().chat.completions.create(
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        messages=messages,
        temperature=0.3,
        max_tokens=1024,
    )
    return resp.choices[0].message.content
