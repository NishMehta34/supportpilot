"""Real MCP client: launch the server via stdio, discover tools and invoke them.

Run: python3 -m scripts.day18_mcp_client
"""
import asyncio
import json
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(command=sys.executable, args=['-m', 'app.mcp_server'])
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {tool.name for tool in tools.tools}
            assert names == {'get_order', 'search_kb', 'create_ticket'}, names
            print('Discovered tools:', ', '.join(sorted(names)))
            order = await session.call_tool('get_order', {'order_id': 'ORD-1001'})
            kb = await session.call_tool('search_kb', {'query': 'return policy'})
            draft = await session.call_tool('create_ticket', {
                'customer_id': 'CUS-001', 'subject': 'Damaged item',
                'description': 'Package arrived damaged',
            })
            def payload(result):
                return json.loads(result.content[0].text)
            order_data, kb_data, draft_data = map(payload, (order, kb, draft))
            assert draft_data.get('status') == 'pending_confirmation', draft_data
            assert 'token' not in json.dumps(draft_data)
            report = {
                'tools_discovered': sorted(names), 'order_result': order_data,
                'kb_result': kb_data, 'draft_result': draft_data,
                'confirmation_tool_exposed': False,
                'ticket_created': False,  # The only exposed write operation stages a draft.
            }
            Path('artifacts').mkdir(exist_ok=True)
            Path('artifacts/day18.json').write_text(json.dumps(report, indent=2) + '\n')
            print('DAY 18 PASSED: MCP discovery + invocation + draft-only write')
            print('Report: artifacts/day18.json')


if __name__ == '__main__':
    asyncio.run(main())
