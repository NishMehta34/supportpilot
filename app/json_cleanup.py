"""Pull the JSON out of a model reply that may be wrapped in extra text."""

import re


def extract_json(text):
    """Remove <think> blocks, code fences and chatty intros/outros around a JSON object.

    This only *finds* the JSON. Strict validation still happens afterwards,
    so wrong values are still blocked.
    """
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL).strip()

    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()

    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        text = text[start : end + 1]
    return text
