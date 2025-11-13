"""
Quantum Bridge API for communication between classical and quantum channels.
Provides RESTful endpoints and WebSocket support for hybrid computing.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, asdict
from datetime import datetime
import aiohttp
from aiohttp import web
import websockets
import threading
import time
try:
    # optional MCP integration helper in same package
    from .mcp_integration import send_prompt_to_llm
except Exception:
    # graceful fallback if module missing
    async def send_prompt_to_llm(model: str, prompt: str, context: dict = None):
        return {'model': model, 'prompt': prompt, 'reply': None, 'metadata': context or {}}

logger = logging.getLogger(__name__)

@dataclass
class QuantumJob:
    """Represents a quantum computation job."""
    job_id: str
    job_type: str  # 'teleportation', 'encryption', 'optimization', etc.
    parameters: Dict[str, Any]
    status: str  # 'pending', 'running', 'completed', 'failed'
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data

class QuantumBridge:
    """
    API bridge between classical and quantum computing systems.
    """

    def __init__(self, host: str = 'localhost', port: int = 8080):
        self.host = host
        self.port = port
        self.jobs: Dict[str, QuantumJob] = {}
        self.job_callbacks: Dict[str, Callable[[QuantumJob], Awaitable[None]]] = {}
        self.websocket_clients: set = set()
        self.app = web.Application()
        self.runner = None
        self.site = None
        self.ws_thread = None
        self._http_loop = None
        self._ws_loop = None
        self._ws_server = None
        self.running = False

        # Setup routes
        self._setup_routes()

    def _setup_routes(self):
        """Setup HTTP routes for the bridge API."""
        self.app.router.add_post('/quantum/jobs', self.create_job)
        self.app.router.add_get('/quantum/jobs/{job_id}', self.get_job)
        self.app.router.add_get('/quantum/jobs', self.list_jobs)
        self.app.router.add_delete('/quantum/jobs/{job_id}', self.cancel_job)
        self.app.router.add_get('/quantum/status', self.get_bridge_status)
        self.app.router.add_post('/quantum/teleport', self.teleport_qubit)
        self.app.router.add_post('/quantum/encrypt', self.encrypt_data)
        self.app.router.add_post('/quantum/optimize', self.optimize_circuit)

    async def create_job(self, request: web.Request) -> web.Response:
        """Create a new quantum computation job."""
        try:
            data = await request.json()
            job_type = data.get('type')
            parameters = data.get('parameters', {})

            if not job_type:
                return web.json_response({'error': 'Job type required'}, status=400)

            job_id = f"job_{int(time.time() * 1000)}_{hash(str(parameters)) % 10000}"
            job = QuantumJob(
                job_id=job_id,
                job_type=job_type,
                parameters=parameters,
                status='pending'
            )

            self.jobs[job_id] = job

            # Start job processing asynchronously
            asyncio.create_task(self._process_job(job))

            logger.info(f"Created quantum job {job_id} of type {job_type}")
            return web.json_response(job.to_dict(), status=201)

        except Exception as e:
            logger.error(f"Error creating job: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_job(self, request: web.Request) -> web.Response:
        """Get job status and result."""
        job_id = request.match_info['job_id']

        if job_id not in self.jobs:
            return web.json_response({'error': 'Job not found'}, status=404)

        return web.json_response(self.jobs[job_id].to_dict())

    async def list_jobs(self, request: web.Request) -> web.Response:
        """List all jobs."""
        job_list = [job.to_dict() for job in self.jobs.values()]
        return web.json_response({'jobs': job_list})

    async def cancel_job(self, request: web.Request) -> web.Response:
        """Cancel a running job."""
        job_id = request.match_info['job_id']

        if job_id not in self.jobs:
            return web.json_response({'error': 'Job not found'}, status=404)

        job = self.jobs[job_id]
        if job.status in ['completed', 'failed']:
            return web.json_response({'error': 'Cannot cancel completed job'}, status=400)

        job.status = 'failed'
        job.error = 'Cancelled by user'
        job.completed_at = datetime.now()

        return web.json_response(job.to_dict())

    async def get_bridge_status(self, request: web.Request) -> web.Response:
        """Get bridge status."""
        status = {
            'status': 'running',
            'active_jobs': len([j for j in self.jobs.values() if j.status == 'running']),
            'pending_jobs': len([j for j in self.jobs.values() if j.status == 'pending']),
            'completed_jobs': len([j for j in self.jobs.values() if j.status == 'completed']),
            'websocket_clients': len(self.websocket_clients)
        }
        return web.json_response(status)

    async def teleport_qubit(self, request: web.Request) -> web.Response:
        """Handle quantum teleportation request."""
        try:
            data = await request.json()
            source_node = data.get('source_node')
            target_node = data.get('target_node')
            qubit_state = data.get('qubit_state', [1.0, 0.0])  # Default |0> state

            if not source_node or not target_node:
                return web.json_response({'error': 'Source and target nodes required'}, status=400)

            # Create teleportation job
            job = QuantumJob(
                job_id=f"teleport_{int(time.time() * 1000)}",
                job_type='teleportation',
                parameters={
                    'source_node': source_node,
                    'target_node': target_node,
                    'qubit_state': qubit_state
                },
                status='running'
            )

            self.jobs[job.job_id] = job

            # Simulate teleportation (in real implementation, this would interface with quantum hardware)
            await asyncio.sleep(0.1)  # Simulate processing time

            job.status = 'completed'
            job.result = {
                'teleported_state': qubit_state,
                'fidelity': 0.99,  # Simulated fidelity
                'source_node': source_node,
                'target_node': target_node
            }
            job.completed_at = datetime.now()

            return web.json_response(job.to_dict())

        except Exception as e:
            logger.error(f"Error in teleportation: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def encrypt_data(self, request: web.Request) -> web.Response:
        """Handle quantum encryption request."""
        try:
            data = await request.json()
            plaintext = data.get('data')
            key_length = data.get('key_length', 256)

            if not plaintext:
                return web.json_response({'error': 'Data required'}, status=400)

            # Create encryption job
            job = QuantumJob(
                job_id=f"encrypt_{int(time.time() * 1000)}",
                job_type='encryption',
                parameters={
                    'data_length': len(plaintext),
                    'key_length': key_length
                },
                status='running'
            )

            self.jobs[job.job_id] = job

            # Simulate quantum encryption
            await asyncio.sleep(0.05)

            # Generate quantum key (simplified)
            quantum_key = self._generate_quantum_key(key_length)
            encrypted_data = self._quantum_encrypt(plaintext, quantum_key)

            job.status = 'completed'
            job.result = {
                'encrypted_data': encrypted_data.hex(),
                'key_id': f"qk_{job.job_id}",
                'algorithm': 'BB84-based'
            }
            job.completed_at = datetime.now()

            return web.json_response(job.to_dict())

        except Exception as e:
            logger.error(f"Error in encryption: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def optimize_circuit(self, request: web.Request) -> web.Response:
        """Handle quantum circuit optimization request."""
        try:
            data = await request.json()
            circuit_description = data.get('circuit')

            if not circuit_description:
                return web.json_response({'error': 'Circuit description required'}, status=400)

            # Create optimization job
            job = QuantumJob(
                job_id=f"optimize_{int(time.time() * 1000)}",
                job_type='optimization',
                parameters={'circuit': circuit_description},
                status='running'
            )

            self.jobs[job.job_id] = job

            # Optionally ask an external LLM for optimization hints via MCP
            try:
                llm_resp = await send_prompt_to_llm('gpt-sim', f'Optimize circuit: {circuit_description}', context={'job_id': job.job_id})
            except Exception:
                llm_resp = None

            # Simulate quantum circuit optimization
            await asyncio.sleep(0.2)

            optimized_circuit = self._optimize_circuit(circuit_description)

            job.status = 'completed'
            job.result = {
                'original_circuit': circuit_description,
                'optimized_circuit': optimized_circuit,
                'gate_reduction': (len(circuit_description) if isinstance(circuit_description, (list, str)) else 0) - (len(optimized_circuit) if isinstance(optimized_circuit, (list, str)) else 0),
                'optimization_method': 'quantum-inspired',
                'llm_advice': llm_resp
            }
            job.completed_at = datetime.now()

            return web.json_response(job.to_dict())

        except Exception as e:
            logger.error(f"Error in optimization: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def _process_job(self, job: QuantumJob):
        """Process a quantum job asynchronously."""
        try:
            job.status = 'running'

            # Simulate job processing based on type
            if job.job_type == 'teleportation':
                await asyncio.sleep(0.1)
                job.result = {'teleported': True, 'fidelity': 0.98}
            elif job.job_type == 'encryption':
                await asyncio.sleep(0.05)
                job.result = {'encrypted': True, 'key_generated': True}
            elif job.job_type == 'optimization':
                await asyncio.sleep(0.2)
                job.result = {'optimized': True, 'improvement': 0.15}

            job.status = 'completed'
            job.completed_at = datetime.now()

            # Notify callbacks
            if job.job_id in self.job_callbacks:
                await self.job_callbacks[job.job_id](job)

            # Broadcast to WebSocket clients
            await self._broadcast_job_update(job)

        except Exception as e:
            job.status = 'failed'
            job.error = str(e)
            job.completed_at = datetime.now()
            logger.error(f"Job {job.job_id} failed: {e}")

    def _generate_quantum_key(self, length: int) -> bytes:
        """Generate a simulated quantum key."""
        import secrets
        return secrets.token_bytes(length // 8)

    def _quantum_encrypt(self, data: str, key: bytes) -> bytes:
        """Simulate quantum encryption."""
        data_bytes = data.encode()
        return bytes(a ^ b for a, b in zip(data_bytes, key * (len(data_bytes) // len(key) + 1)))

    def _optimize_circuit(self, circuit: dict) -> dict:
        """Simulate quantum circuit optimization."""
        # Simplified optimization: remove redundant gates
        optimized = circuit.copy()
        # In a real implementation, this would use quantum algorithms
        return optimized

    async def _broadcast_job_update(self, job: QuantumJob):
        """Broadcast job updates to WebSocket clients."""
        message = {
            'type': 'job_update',
            'job': job.to_dict()
        }

        disconnected = set()
        for websocket in self.websocket_clients:
            try:
                await websocket.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(websocket)

        self.websocket_clients -= disconnected

    async def websocket_handler(self, websocket, path):
        """Handle WebSocket connections."""
        self.websocket_clients.add(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
                if data.get('type') == 'subscribe_job':
                    job_id = data.get('job_id')
                    if job_id in self.jobs:
                        await websocket.send(json.dumps({
                            'type': 'job_update',
                            'job': self.jobs[job_id].to_dict()
                        }))
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.websocket_clients.discard(websocket)

    def start(self):
        """Start the quantum bridge server."""
        self.running = True
        # Start HTTP server in its own thread + event loop and keep loop reference
        def http_thread_target():
            loop = asyncio.new_event_loop()
            self._http_loop = loop
            asyncio.set_event_loop(loop)

            async def _http_runner():
                self.runner = web.AppRunner(self.app)
                await self.runner.setup()
                self.site = web.TCPSite(self.runner, self.host, self.port)
                await self.site.start()
                logger.info(f"Quantum Bridge HTTP server started on {self.host}:{self.port}")
                # Keep running until stopped
                await asyncio.Future()

            try:
                loop.run_until_complete(_http_runner())
            finally:
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.close()

        # Start WebSocket server in its own thread + event loop and keep loop/server refs
        def ws_thread_target():
            loop = asyncio.new_event_loop()
            self._ws_loop = loop
            asyncio.set_event_loop(loop)

            async def _ws_runner():
                # Create the websocket server inside a running event loop
                self._ws_server = await websockets.serve(
                    self.websocket_handler,
                    self.host,
                    self.port + 1  # WebSocket on port + 1
                )
                logger.info(f"Quantum Bridge WebSocket server started on {self.host}:{self.port + 1}")
                await asyncio.Future()

            try:
                loop.run_until_complete(_ws_runner())
            finally:
                # attempt graceful shutdown
                if self._ws_server is not None:
                    loop.run_until_complete(self._ws_server.wait_closed())
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.close()

        http_thread = threading.Thread(target=http_thread_target)
        http_thread.daemon = True
        http_thread.start()

        self.ws_thread = threading.Thread(target=ws_thread_target)
        self.ws_thread.daemon = True
        self.ws_thread.start()

    def stop(self):
        """Stop the quantum bridge server."""
        self.running = False
        # Clean up the aiohttp runner in its own loop if possible
        try:
            if self.runner and self._http_loop:
                fut = asyncio.run_coroutine_threadsafe(self.runner.cleanup(), self._http_loop)
                fut.result(timeout=5)
        except Exception:
            # Fallback: attempt to call cleanup synchronously
            try:
                asyncio.run(self.runner.cleanup())
            except Exception:
                logger.exception("Failed to clean up HTTP runner gracefully")

        # Close websocket server and stop its loop
        try:
            if self._ws_server and self._ws_loop:
                # Close the server and wait for it to finish
                close_coro = self._ws_server.wait_closed()
                fut = asyncio.run_coroutine_threadsafe(close_coro, self._ws_loop)
                fut.result(timeout=5)
                # Stop the loop
                self._ws_loop.call_soon_threadsafe(self._ws_loop.stop)
        except Exception:
            logger.exception("Failed to stop websocket server cleanly")

        logger.info("Quantum Bridge server stopped")

# Client for interacting with the quantum bridge
class QuantumBridgeClient:
    """Client for communicating with the Quantum Bridge API."""

    def __init__(self, bridge_url: str = 'http://localhost:8080'):
        self.bridge_url = bridge_url
        self.session = aiohttp.ClientSession()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def create_job(self, job_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a quantum job."""
        async with self.session.post(
            f'{self.bridge_url}/quantum/jobs',
            json={'type': job_type, 'parameters': parameters}
        ) as response:
            return await response.json()

    async def get_job(self, job_id: str) -> Dict[str, Any]:
        """Get job status."""
        async with self.session.get(f'{self.bridge_url}/quantum/jobs/{job_id}') as response:
            return await response.json()

    async def teleport_qubit(self, source_node: str, target_node: str,
                           qubit_state: List[float] = None) -> Dict[str, Any]:
        """Request quantum teleportation."""
        data = {
            'source_node': source_node,
            'target_node': target_node
        }
        if qubit_state:
            data['qubit_state'] = qubit_state

        async with self.session.post(f'{self.bridge_url}/quantum/teleport', json=data) as response:
            return await response.json()

    async def encrypt_data(self, data: str, key_length: int = 256) -> Dict[str, Any]:
        """Request quantum encryption."""
        async with self.session.post(
            f'{self.bridge_url}/quantum/encrypt',
            json={'data': data, 'key_length': key_length}
        ) as response:
            return await response.json()

    async def optimize_circuit(self, circuit: Dict[str, Any]) -> Dict[str, Any]:
        """Request quantum circuit optimization."""
        async with self.session.post(
            f'{self.bridge_url}/quantum/optimize',
            json={'circuit': circuit}
        ) as response:
            return await response.json()
