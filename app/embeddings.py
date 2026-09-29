"""Turn text into embeddings (lists of numbers) using the local Ollama model,
and compare embeddings with cosine similarity.
"""

import json
import math
import urllib.request

EMBED_MODEL = "embeddinggemma"
EMBED_URL = "http://localhost:11434/api/embed"


def _http_post(url, body, timeout=120):
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def get_embedding(text, model=EMBED_MODEL, http_post=_http_post):
    """Return one embedding (a list of floats) for a piece of text."""
    response = http_post(EMBED_URL, {"model": model, "input": text})
    # Ollama's /api/embed returns {"embeddings": [[...]]} - one list per input.
    return response["embeddings"][0]


def get_embeddings(texts, model=EMBED_MODEL, http_post=_http_post, batch_size=8):
    """Embed many texts. Sent in small batches so one huge request can't time out."""
    vectors = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        response = http_post(EMBED_URL, {"model": model, "input": batch})
        vectors.extend(response["embeddings"])
    return vectors


def cosine_similarity(vector_a, vector_b):
    """1.0 = identical meaning, 0.0 = unrelated, negative = opposite. Never crashes on a zero vector."""
    dot = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = math.sqrt(sum(a * a for a in vector_a))
    norm_b = math.sqrt(sum(b * b for b in vector_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def top_k(query_vector, items, k=5):
    """items: [{"vector": [...], ...}]. Returns the k most similar items, each with a 'score' added."""
    scored = []
    for item in items:
        score = cosine_similarity(query_vector, item["vector"])
        scored.append({**{key: value for key, value in item.items() if key != "vector"}, "score": score})
    return sorted(scored, key=lambda entry: entry["score"], reverse=True)[:k]
