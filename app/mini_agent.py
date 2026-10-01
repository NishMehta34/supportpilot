"""Day 12, version 3: a TINY wrapper of our own, in the spirit of a framework's
agent class, but with every line visible. Compare this against app/agent_loop.py
(version 1, the raw loop) and scripts/smolagents_version.py (version 2, a real
framework) for the same 2 tools.
"""

from app.agent_loop import run_agent


class MiniAgent:
    """A thin, readable stand-in for what a framework's `Agent` class does:
    bundle a model, a toolbox, and a step limit behind one object with a
    single `.run(task)` method. Underneath, it's still just run_agent.
    """

    def __init__(self, chat_fn, tools, execute_tool, max_steps=6):
        self.chat_fn = chat_fn
        self.tools = tools
        self.execute_tool = execute_tool
        self.max_steps = max_steps
        self.last_result = None  # the framework "remembers" the last run, for convenience

    def run(self, task):
        self.last_result = run_agent(
            task, chat_fn=self.chat_fn, max_steps=self.max_steps,
            tool_schemas=self.tools, execute_tool=self.execute_tool,
        )
        return self.last_result["final_answer"]

    def explain_last_run(self):
        """A convenience a framework might give you: a one-line trace summary."""
        if not self.last_result:
            return "No run yet."
        tools_used = [s["tool"] for s in self.last_result["trace"] if s["type"] == "tool_call"]
        return (f"stop_reason={self.last_result['stop_reason']}, "
                f"steps={self.last_result['steps_used']}, tools_used={tools_used}")
