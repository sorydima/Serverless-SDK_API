import asyncio
from ai.ai.mcp.adapter import MCPAdapter


async def _run_test():
    adapter = MCPAdapter()
    resp = await adapter.send('gpt-sim', 'hello world', context={'session': 't1'})
    assert 'reply' in resp
    assert 'hello' in resp['prompt']
    await adapter.close()


def test_mcp_adapter():
    asyncio.run(_run_test())
