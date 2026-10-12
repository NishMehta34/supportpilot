"""Day 18 safety and shared-business-logic tests."""
import json
import pytest
from app.mcp_server import create_mcp_server, make_toolbox, native_invoke


def tb(role='agent', retrieve_fn=None):
    return make_toolbox(user_id='u1', tenant_id='t1', role=role, retrieve_fn=retrieve_fn)


def test_native_and_mcp_share_dispatch():
    toolbox = tb()
    assert native_invoke(toolbox, 'get_order', {'order_id': 'ORD-1001'}) == toolbox.execute('get_order', {'order_id': 'ORD-1001'})


def test_read_only_does_not_create_tickets():
    toolbox = tb()
    native_invoke(toolbox, 'get_order', {'order_id': 'ORD-1001'})
    native_invoke(toolbox, 'search_kb', {'query': 'returns'})
    assert toolbox.tickets.count() == 0


def test_write_only_stages_draft():
    toolbox = tb()
    result = native_invoke(toolbox, 'create_ticket', {'customer_id': 'CUS-001', 'subject': 'Damaged', 'description': 'Box damaged'})
    assert result.get('status') == 'pending_confirmation', result
    assert 'token' not in json.dumps(result)
    assert toolbox.tickets.count() == 0


def test_viewer_cannot_draft():
    toolbox = tb('viewer')
    result = native_invoke(toolbox, 'create_ticket', {'customer_id': 'CUS-001', 'subject': 'Damage', 'description': 'Damage'})
    assert 'permission_denied' in result.get('error', '')
    assert toolbox.tickets.count() == 0


def test_mcp_cannot_confirm_or_override_confirmation():
    toolbox = tb()
    assert 'Unknown tool' in native_invoke(toolbox, 'confirm_ticket', {'draft_id': 'DRAFT-0001'}).get('error', '')
    result = native_invoke(toolbox, 'create_ticket', {'customer_id': 'CUS-001', 'subject': 'Damage', 'description': 'Damage', 'confirmed': True})
    assert 'error' in result
    assert toolbox.tickets.count() == 0


def test_retrieval_scoped_to_server_identity():
    calls = []
    toolbox = tb(retrieve_fn=lambda q, tenant, k: calls.append((q, tenant, k)) or [])
    native_invoke(toolbox, 'search_kb', {'query': 'returns'})
    assert calls and calls[0][1] == 't1'


def test_mcp_tool_discovery():
    pytest.importorskip('mcp')
    server = create_mcp_server(tb())
    names = {t.name for t in server._tool_manager.list_tools()}
    assert names == {'get_order', 'search_kb', 'create_ticket'}


@pytest.mark.asyncio
async def test_mcp_tool_invocation():
    pytest.importorskip('mcp')
    toolbox = tb()
    server = create_mcp_server(toolbox)
    result = await server._tool_manager.call_tool('create_ticket', {'customer_id': 'CUS-001', 'subject': 'Damage', 'description': 'Damaged package'})
    assert 'pending_confirmation' in str(result)
    assert toolbox.tickets.count() == 0
