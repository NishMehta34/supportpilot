"""The 'toolbox': real Python functions the AI is allowed to ask us to run."""

# Fake business data (a stand-in for a real database).
ORDERS = {
    "ORD-1001": {"order_id": "ORD-1001", "customer_id": "CUS-001", "product_id": "PRD-001",
                 "status": "shipped", "eta": "2026-10-02"},
    "ORD-1002": {"order_id": "ORD-1002", "customer_id": "CUS-002", "product_id": "PRD-002",
                 "status": "processing", "eta": "2026-10-06"},
    "ORD-1003": {"order_id": "ORD-1003", "customer_id": "CUS-001", "product_id": "PRD-003",
                 "status": "delivered", "eta": None},
}
CUSTOMERS = {
    "CUS-001": {"customer_id": "CUS-001", "name": "Asha Patel", "email": "asha@example.com", "tier": "gold"},
    "CUS-002": {"customer_id": "CUS-002", "name": "Ben Carter", "email": "ben@example.com", "tier": "standard"},
    "CUS-003": {"customer_id": "CUS-003", "name": "Chen Wei", "email": "chen@example.com", "tier": "premium"},
}
PRODUCTS = {
    "PRD-001": {"product_id": "PRD-001", "name": "Wireless Mouse", "price": 24.99, "in_stock": True},
    "PRD-002": {"product_id": "PRD-002", "name": "Mechanical Keyboard", "price": 89.00, "in_stock": True},
    "PRD-003": {"product_id": "PRD-003", "name": "USB-C Hub", "price": 45.50, "in_stock": False},
}


def normalize_id(value) -> str:
    """' ord-1001 ' -> 'ORD-1001' (models often change case or add spaces)."""
    return str(value).strip().upper()


def get_order(order_id: str) -> dict:
    return ORDERS.get(normalize_id(order_id)) or {"error": f"Order {order_id} not found"}


def get_customer(customer_id: str) -> dict:
    return CUSTOMERS.get(normalize_id(customer_id)) or {"error": f"Customer {customer_id} not found"}


def get_product(product_id: str) -> dict:
    return PRODUCTS.get(normalize_id(product_id)) or {"error": f"Product {product_id} not found"}


TOOL_FUNCTIONS = {
    "get_order": get_order,
    "get_customer": get_customer,
    "get_product": get_product,
}


def _schema(name, description, arg_name, arg_description):
    """Build the 'menu description' that tells the AI what a tool does."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {arg_name: {"type": "string", "description": arg_description}},
                "required": [arg_name],
            },
        },
    }


TOOL_SCHEMAS = [
    _schema("get_order", "Look up an order's status and delivery date by order ID.",
            "order_id", "The order ID, like ORD-1001"),
    _schema("get_customer", "Look up a customer's name, email and tier by customer ID.",
            "customer_id", "The customer ID, like CUS-001"),
    _schema("get_product", "Look up a product's name, price and stock by product ID.",
            "product_id", "The product ID, like PRD-001"),
]


def execute_tool(name, arguments):
    """Safely run a tool the AI asked for. Never crashes; returns an error dict instead."""
    function = TOOL_FUNCTIONS.get(name)
    if function is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return function(**arguments)
    except TypeError as error:
        return {"error": f"Invalid arguments for {name}: {error}"}
    except Exception as error:  # a broken tool must not crash the app
        return {"error": f"Tool {name} failed: {error}"}
