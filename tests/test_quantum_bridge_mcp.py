import asyncio
from ai.ai_quantum_core.quantum_bridge import QuantumBridge


def test_optimize_calls_llm():
    # Create bridge and run optimize endpoint handler with simulated request
    bridge = QuantumBridge(host='127.0.0.1', port=18080)

    async def run_test():
        # Try to start the HTTP server and call via aiohttp. If that fails (platform
        # differences / event loop issues), fall back to calling the handler
        # directly (previous, reliable approach).
        started = False
        data = None
        try:
            bridge.start()
            started = True

            import aiohttp
            # wait for server to be ready
            import asyncio as _asyncio
            ready = False
            for _ in range(40):
                try:
                    reader, writer = await _asyncio.open_connection(bridge.host, bridge.port)
                    writer.close()
                    try:
                        await writer.wait_closed()
                    except Exception:
                        pass
                    ready = True
                    break
                except Exception:
                    await _asyncio.sleep(0.05)

            if not ready:
                raise RuntimeError('QuantumBridge HTTP server did not start in time')

            async with aiohttp.ClientSession() as session:
                url = f'http://{bridge.host}:{bridge.port}/quantum/optimize'
                async with session.post(url, json={'circuit': {'gates': [1,2,3]}}) as resp:
                    data = await resp.json()

        except Exception:
            # Fallback: call handler directly
            class FakeRequest:
                def __init__(self, data):
                    self._data = data

                async def json(self):
                    return self._data

            req = FakeRequest({'circuit': {'gates': [1,2,3]}})
            resp = await bridge.optimize_circuit(req)
            import json as _json
            body = None
            if hasattr(resp, 'body') and resp.body is not None:
                body = resp.body
            elif hasattr(resp, '_body') and resp._body is not None:
                body = resp._body
            else:
                body = str(resp).encode('utf-8')
            data = _json.loads(body.decode('utf-8'))

        finally:
            # Attempt to stop bridge if we started it. Use a thread to avoid
            # calling asyncio.run from within a running event loop.
            if started:
                import threading
                t = threading.Thread(target=bridge.stop)
                t.daemon = True
                t.start()

        # The bridge returns a job dict where 'result' contains 'llm_advice'
        assert 'result' in data
        assert 'llm_advice' in data['result']

    asyncio.run(run_test())
