"""Day 18: MCP adapter for the existing Day 13 SupportToolbox.

Run: python -m app.mcp_server
MCP stdio protocol uses stdout; never print logs to stdout in this module.
"""
import json
import os
from app.support_tools import SupportToolbox, UserContext


def make_toolbox(*, user_id, tenant_id, role, retrieve_fn=None):
    """Identity is provided by the trusted server launcher, NOT MCP tool arguments.

    For local demo only: production must authenticate clients and authorize tool reads.
    """
    return SupportToolbox(
        UserContext(user_id, tenant_id, role),
        retrieve_fn=retrieve_fn or (lambda query, tenant, k: []),
    )


def native_invoke(toolbox, name, arguments):
    """Single shared dispatch path for native and MCP consumers."""
    return toolbox.execute(name, arguments)


def create_mcp_server(toolbox):
    """Build an MCP stdio server with exactly three business tools."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError('MCP SDK missing: python3 -m pip install "mcp>=1,<2"') from exc

    server = FastMCP('supportpilot')

    @server.tool()
    def get_order(order_id: str) -> str:
        """Read-only: look up an order by ID. Never changes business data."""
        return json.dumps(native_invoke(toolbox, 'get_order', {'order_id': order_id}))

    @server.tool()
    def search_kb(query: str) -> str:
        """Read-only: search tenant-scoped support knowledge base passages."""
        return json.dumps(native_invoke(toolbox, 'search_kb', {'query': query}))

    @server.tool()
    def create_ticket(customer_id: str, subject: str, description: str) -> str:
        """Stage a ticket draft only; a human must confirm outside MCP."""
        return json.dumps(native_invoke(toolbox, 'create_ticket', {
            'customer_id': customer_id, 'subject': subject, 'description': description,
        }))

    return server


def main():
    # Local-only launcher: these values are set by the trusted process operator.
    # Never expose this launcher as a remotely accessible authenticated service.
    toolbox = make_toolbox(
        user_id=os.environ.get('SUPPORTPILOT_USER_ID', 'demo-user'),
        tenant_id=os.environ.get('SUPPORTPILOT_TENANT_ID', 'demo-tenant'),
        role=os.environ.get('SUPPORTPILOT_ROLE', 'agent'),
    )
    create_mcp_server(toolbox).run(transport='stdio')


if __name__ == '__main__':
    main()
