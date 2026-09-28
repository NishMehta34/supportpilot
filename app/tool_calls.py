"""Safely read a tool call from a model, even when it is malformed."""

import json


def parse_tool_call(call):
    """Return (name, arguments). Never raises; bad input becomes ("", {}) or ({}) arguments."""
    function = call.get("function") if isinstance(call, dict) else None
    if not isinstance(function, dict):
        return "", {}

    name = function.get("name") or ""
    arguments = function.get("arguments")

    if isinstance(arguments, str):  # some models send arguments as text
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            arguments = {}
    if not isinstance(arguments, dict):
        arguments = {}

    return str(name), arguments
