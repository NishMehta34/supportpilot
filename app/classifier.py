"""Classify a support message with the local model, and validate the answer."""

import json
import urllib.request

from pydantic import ValidationError

from app.json_cleanup import extract_json
from app.schemas import TicketClassification

MODEL = "qwen3"
URL = "http://localhost:11434/api/chat"

SYSTEM_PROMPT = (
    "You classify customer support messages. Reply ONLY with JSON containing: "
    "category (billing, technical, shipping, account, other), "
    "priority (low, medium, high, urgent), "
    "summary (one short sentence), "
    "confidence (a number from 0 to 1)."
)


class ClassificationError(Exception):
    """Raised when the model never produces a valid answer."""


def ollama_chat(messages, schema):
    """Send messages to Ollama and return the model's raw text reply."""
    body = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "format": schema,  # tells Ollama: answer must match this JSON shape
        "think": False,
    }
    request = urllib.request.Request(
        URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.loads(response.read().decode("utf-8"))["message"]["content"]


def classify_message(message, chat_fn=ollama_chat, max_attempts=3):
    """Return a validated TicketClassification, or raise ClassificationError.

    chat_fn can be swapped for a fake in tests (no real model needed).
    """
    schema = TicketClassification.model_json_schema()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": message},
    ]
    last_error = None

    for _ in range(max_attempts):
        raw = chat_fn(messages, schema)
        try:
            return TicketClassification.model_validate_json(extract_json(raw))
        except ValidationError as error:
            last_error = error
            # Tell the model what went wrong so the retry can improve.
            messages.append({"role": "assistant", "content": raw})
            messages.append(
                {"role": "user", "content": f"That was invalid: {error}. Try again."}
            )

    raise ClassificationError(
        f"No valid answer after {max_attempts} attempts: {last_error}"
    )
