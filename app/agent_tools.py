"""Agent toolbox: the Day 3 tools plus a safe calculator and an order search."""

import ast
import operator

from app.tools import ORDERS, TOOL_FUNCTIONS, TOOL_SCHEMAS

# ---------- Calculator (safe: only numbers and + - * /, never runs code) ----------

_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def _evaluate(node):
    if isinstance(node, ast.Expression):
        return _evaluate(node.body)
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
    ):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_evaluate(node.left), _evaluate(node.right))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_evaluate(node.operand)
    raise ValueError("Unsupported expression")


def calculator(expression: str) -> dict:
    """Evaluate simple arithmetic like '24.99 * 3 + 5'."""
    if len(expression) > 200:
        return {"error": "Expression too long"}
    try:
        return {"result": round(_evaluate(ast.parse(expression, mode="eval")), 6)}
    except ZeroDivisionError:
        return {"error": "Division by zero"}
    except (ValueError, SyntaxError):
        return {"error": "Unsupported expression. Use numbers and + - * / only."}


# ---------- Order search ----------

def search_orders(customer_id: str = None, status: str = None) -> dict:
    """Find orders by customer and/or status."""
    matches = [
        order
        for order in ORDERS.values()
        if (customer_id is None or order["customer_id"] == customer_id)
        and (status is None or order["status"] == status)
    ]
    return {"orders": matches, "count": len(matches)}


# ---------- Combined toolbox ----------

AGENT_FUNCTIONS = {
    **TOOL_FUNCTIONS,
    "calculator": calculator,
    "search_orders": search_orders,
}

AGENT_SCHEMAS = TOOL_SCHEMAS + [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Do arithmetic. ALWAYS use this for any maths.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "e.g. '24.99 * 3'"}
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_orders",
            "description": "Find orders by customer ID and/or status (processing, shipped, delivered).",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "e.g. CUS-001"},
                    "status": {"type": "string", "description": "e.g. processing"},
                },
                "required": [],
            },
        },
    },
]


def execute_agent_tool(name, arguments):
    """Safely run any agent tool. Returns an error dict instead of crashing."""
    function = AGENT_FUNCTIONS.get(name)
    if function is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return function(**arguments)
    except TypeError as error:
        return {"error": f"Invalid arguments for {name}: {error}"}
    except Exception as error:
        return {"error": f"Tool {name} failed: {error}"}
