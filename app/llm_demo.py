"""Day 1: send one prompt to a local AI model (via Ollama) and save the result."""

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

# --- Settings (the "knobs" of our program) ---
MODEL = "qwen3"  # which AI model to talk to
PROMPT = "In two sentences, explain what a customer support agent does."
URL = "http://localhost:11434/api/chat"  # where Ollama listens on your Mac

# Save the result to <project folder>/artifacts/day01.json
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "artifacts" / "day01.json"

# --- 1. Build the request (our message to the AI) ---
request_body = {
    "model": MODEL,
    "messages": [{"role": "user", "content": PROMPT}],
    "stream": False,  # give me the whole answer at once, not word by word
}

# --- 2. Send it to Ollama ---
http_request = urllib.request.Request(
    URL,
    data=json.dumps(request_body).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)

try:
    with urllib.request.urlopen(http_request, timeout=300) as http_response:
        response_body = json.loads(http_response.read().decode("utf-8"))
except urllib.error.URLError as error:
    print("Could not reach Ollama. Is the Ollama app running?")
    print(f"Details: {error}")
    sys.exit(1)

# --- 3. Save both the request and the response as evidence ---
OUTPUT_FILE.parent.mkdir(exist_ok=True)
OUTPUT_FILE.write_text(
    json.dumps({"request": request_body, "response": response_body}, indent=2)
)

# --- 4. Show the answer on screen ---
print("Model said:")
print(response_body["message"]["content"])
print(f"\nSaved to {OUTPUT_FILE}")
