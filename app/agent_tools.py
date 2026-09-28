"""Day 4 toolbox: Day 3's tools plus a calculator and an order search."""

import ast
import operator

from app.tools import ORDERS, TOOL_FUNCTIONS, TOOL_SCHEMAS, normalize_id

# ---------- Calculator (safe: never uses eval) ----------
_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}


def _evaluate(node):
    if isinstance(node, ast.Expression):
        return _evaluate(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) \
            and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        left, right = _evaluate(node.left), _evaluate(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise ValueError("exponent too large")
        return _OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_evaluate(node.operand))
    raise ValueError("only numbers and + - * / ** ( ) are allowed")


def calculator(expression: str) -> dict:
    if len(expression) > 200:
        return {"error": "Expression too long"}
    try:
        value = _evaluate(ast.parse(expression, mode="eval"))
    except ZeroDivisionError:
        return {"error": "Division by zero"}
    except (ValueError, SyntaxError, TypeError, OverflowError) as error:
        return {"error": f"Cannot calculate: {error}"}
    return {"expression": expression, "result": round(value, 4)}


# ---------- Order search ----------
def search_orders(customer_id: str = None, status: str = None) -> dict:
    if not customer_id and not status:
        return {"error": "Provide customer_id and/or status"}
    customer_id = normalize_id(customer_id) if customer_id else None
    status = status.strip().lower() if status else None
    matches = [
        order for order in ORDERS.values()
        if (not customer_id or order["customer_id"] == customer_id)
        and (not status or order["status"] == status)
    ]
    return {"count": len(matches), "orders": matches}


# ---------- Registry ----------
AGENT_TOOL_FUNCTIONS = {**TOOL_FUNCTIONS, "calculator": calculator, "search_orders": search_orders}

AGENT_TOOL_SCHEMAS = TOOL_SCHEMAS + [
    {"type": "function", "function": {
        "name": "calculator",
        "description": "Do arithmetic. Always use this for maths instead of calculating yourself.",
        "parameters": {"type": "object",
                       "properties": {"expression": {"type": "string", "description": "e.g. 24.99 + 45.5"}},
                       "required": ["expression"]}}},
    {"type": "function", "function": {
        "name": "search_orders",
        "description": "Find orders by customer ID and/or status (processing, shipped, delivered).",
        "parameters": {"type": "object",
                       "properties": {
                           "customer_id": {"type": "string", "description": "e.g. CUS-001"},
                           "status": {"type": "string", "description": "processing, shipped or delivered"}},
                       "required": []}}},
]


def execute_agent_tool(name, arguments):
    """Safely run a tool. Never crashes; returns an error dict instead."""
    function = AGENT_TOOL_FUNCTIONS.get(name)
    if function is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return function(**arguments)
    except TypeError as error:
        return {"error": f"Invalid arguments for {name}: {error}"}
    except Exception as error:
        return {"error": f"Tool {name} failed: {error}"}
