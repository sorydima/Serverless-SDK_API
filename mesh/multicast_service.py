"""Multicast discovery service scaffold.

Provides a lightweight UDP multicast-based discovery service for mesh nodes.
This is a scaffold suitable for unit tests and local demos.
"""
import socket
import struct
import threading
import time
import json
from typing import Dict, Any, Callable, List


class MulticastDiscoveryService:
    """Simple UDP multicast-based local discovery.

    Usage:
        svc = MulticastDiscoveryService(group='224.0.0.251', port=9999)
        svc.start()
        svc.broadcast({'id': 'node1', 'addr': '192.168.1.5'})
        time.sleep(1)
        topo = svc.get_topology()
        svc.stop()
    """

    def __init__(self, group: str = '224.0.0.251', port: int = 9999, on_receive: Callable[[Dict[str, Any]], None] = None):
        self.group = group
        self.port = port
        self.on_receive = on_receive
        self._sock = None
        self._running = False
        self._thread = None
        self._topology: Dict[str, Dict[str, Any]] = {}

    def start(self):
        if self._running:
            return
        self._running = True
        # Create UDP socket for multicast
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self._sock.bind(('', self.port))
        except OSError:
            # On some platforms binding to '' may require elevated privileges; fallback
            self._sock.bind(('0.0.0.0', self.port))

        mreq = struct.pack('4sl', socket.inet_aton(self.group), socket.INADDR_ANY)
        self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        self._thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._sock:
            try:
                mreq = struct.pack('4sl', socket.inet_aton(self.group), socket.INADDR_ANY)
                self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)
            except Exception:
                pass
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None

    def _recv_loop(self):
        while self._running and self._sock:
            try:
                data, addr = self._sock.recvfrom(4096)
                try:
                    payload = json.loads(data.decode('utf-8'))
                except Exception:
                    continue
                node_id = payload.get('id') or payload.get('node_id') or str(addr)
                self._topology[node_id] = {**payload, 'last_seen': time.time(), 'remote': addr}
                if self.on_receive:
                    try:
                        self.on_receive(payload)
                    except Exception:
                        pass
            except Exception:
                time.sleep(0.1)

    def broadcast(self, info: Dict[str, Any]):
        """Broadcast discovery information to multicast group."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        try:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            msg = json.dumps(info).encode('utf-8')
            sock.sendto(msg, (self.group, self.port))
        finally:
            sock.close()

    def get_topology(self, stale_after: float = 300.0) -> Dict[str, Dict[str, Any]]:
        """Return the current known topology, pruning nodes not seen within stale_after seconds."""
        now = time.time()
        keys = list(self._topology.keys())
        for k in keys:
            if now - self._topology[k].get('last_seen', 0) > stale_after:
                del self._topology[k]
        return dict(self._topology)


__all__ = ["MulticastDiscoveryService"]
