"""Model adapters: ONE plug shape for the real model (Ollama) and a fake one for tests.

Because our code only asks "give me a reply", a test can plug in FakeAdapter and
never touch a real model.
"""

import copy
import json
import urllib.request

DEFAULT_MODEL = "qwen3"
DEFAULT_URL = "http://localhost:11434/api/chat"


def _http_post(url, body, timeout=300):
    """Send JSON to a URL and return the JSON reply."""
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class ChatAdapter:
    """The shared shape: chat(messages, tools=None, schema=None) -> reply message (a dict)."""

    def chat(self, messages, tools=None, schema=None):
        raise NotImplementedError

    def tool_chat_fn(self):
        """A plug for the tool loop and the agent loop."""
        return lambda messages, tools=None: self.chat(messages, tools=tools)

    def json_chat_fn(self):
        """A plug for the classifier (it wants the reply as plain text)."""
        return lambda messages, schema=None: self.chat(messages, schema=schema).get("content", "")


class OllamaAdapter(ChatAdapter):
    """Talks to the real local model."""

    def __init__(self, model=DEFAULT_MODEL, url=DEFAULT_URL, http_post=_http_post):
        self.model = model
        self.url = url
        self._post = http_post  # swappable, so tests never need a network

    def build_body(self, messages, tools=None, schema=None):
        body = {"model": self.model, "messages": messages, "stream": False, "think": False}
        if tools:
            body["tools"] = tools
        if schema:
            body["format"] = schema
        return body

    def chat(self, messages, tools=None, schema=None):
        response = self._post(self.url, self.build_body(messages, tools, schema))
        return response["message"]


class FakeAdapter(ChatAdapter):
    """A scripted actor. Replies come out in order; every call is recorded."""

    def __init__(self, replies, repeat_last=False):
        self._replies = [self._to_message(reply) for reply in replies]
        self._repeat_last = repeat_last  # keep giving the last reply forever
        self._next = 0
        self.calls = []

    @staticmethod
    def _to_message(reply):
        if isinstance(reply, dict):
            return reply
        return {"role": "assistant", "content": reply}

    def chat(self, messages, tools=None, schema=None):
        self.calls.append({"messages": copy.deepcopy(messages), "tools": tools, "schema": schema})
        if self._next < len(self._replies):
            reply = self._replies[self._next]
            self._next += 1
        elif self._repeat_last and self._replies:
            reply = self._replies[-1]
        else:
            raise RuntimeError("FakeAdapter ran out of scripted replies")
        return copy.deepcopy(reply)
