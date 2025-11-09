"""
Mesh Network Routing for Device Communication

This module implements routing algorithms for mesh networks,
enabling efficient device-to-device communication in decentralized networks.
"""

import asyncio
from typing import Dict, List, Optional, Set, Tuple
import logging
import time

logger = logging.getLogger(__name__)


class MeshRouter:
    """
    Router for mesh network communication between devices.
    Implements various routing algorithms for optimal path finding.
    """

    def __init__(self, device_id: str, max_hops: int = 5):
        self.device_id = device_id
        self.max_hops = max_hops
        self.routing_table: Dict[str, Dict] = {}
        self.neighbors: Set[str] = set()
        self.last_update = time.time()

    def add_neighbor(self, neighbor_id: str, connection_quality: float = 1.0):
        """Add a neighboring device to the routing table."""
        self.neighbors.add(neighbor_id)
        self.routing_table[neighbor_id] = {
            'next_hop': neighbor_id,
            'hops': 1,
            'quality': connection_quality,
            'last_seen': time.time()
        }
        logger.info(f"Added neighbor {neighbor_id} to mesh router")

    def remove_neighbor(self, neighbor_id: str):
        """Remove a neighboring device."""
        if neighbor_id in self.neighbors:
            self.neighbors.remove(neighbor_id)
            if neighbor_id in self.routing_table:
                del self.routing_table[neighbor_id]
            logger.info(f"Removed neighbor {neighbor_id} from mesh router")

    def update_routing_table(self, routes: Dict[str, Dict]):
        """Update routing table with new route information."""
        for destination, route_info in routes.items():
            if destination not in self.routing_table or \
               route_info['hops'] < self.routing_table[destination]['hops']:
                self.routing_table[destination] = route_info.copy()
                self.routing_table[destination]['last_seen'] = time.time()

        self.last_update = time.time()

    def find_route(self, destination: str) -> Optional[List[str]]:
        """
        Find the best route to a destination device.

        Returns:
            List of device IDs representing the path, or None if no route found
        """
        if destination == self.device_id:
            return [self.device_id]

        if destination in self.routing_table:
            route = [self.device_id]
            current = destination

            # Reconstruct path by backtracking
            visited = set()
            while current != self.device_id and current not in visited:
                visited.add(current)
                route.append(current)
                if current in self.routing_table:
                    next_hop = self.routing_table[current].get('next_hop')
                    if next_hop and next_hop != current:
                        current = next_hop
                    else:
                        break
                else:
                    break

            if route[-1] == destination:
                return route

        return None

    def broadcast_routing_info(self) -> Dict[str, Dict]:
        """Broadcast current routing information to neighbors."""
        routes = {}
        for dest, info in self.routing_table.items():
            if info['hops'] < self.max_hops:
                routes[dest] = {
                    'next_hop': self.device_id,
                    'hops': info['hops'] + 1,
                    'quality': info['quality'] * 0.9,  # Quality degrades with distance
                    'last_seen': info['last_seen']
                }
        return routes

    def get_network_topology(self) -> Dict[str, List[str]]:
        """Get current view of network topology."""
        topology = {}
        for dest in self.routing_table:
            route = self.find_route(dest)
            if route:
                topology[dest] = route
        return topology

    async def maintain_routes(self):
        """Maintain routing table by periodically cleaning up stale routes."""
        while True:
            current_time = time.time()
            stale_routes = []

            for dest, info in self.routing_table.items():
                if current_time - info['last_seen'] > 300:  # 5 minutes
                    stale_routes.append(dest)

            for dest in stale_routes:
                del self.routing_table[dest]
                logger.info(f"Removed stale route to {dest}")

            await asyncio.sleep(60)  # Check every minute

    def get_routing_stats(self) -> Dict[str, int]:
        """Get routing statistics."""
        return {
            'total_routes': len(self.routing_table),
            'direct_neighbors': len(self.neighbors),
            'max_hops_configured': self.max_hops,
            'last_update_seconds_ago': time.time() - self.last_update
        }


class AODVRouting(MeshRouter):
    """
    Ad-hoc On-Demand Distance Vector routing implementation.
    Optimized for mesh networks with dynamic topology.
    """

    def __init__(self, device_id: str, max_hops: int = 5):
        super().__init__(device_id, max_hops)
        self.route_requests: Dict[str, Dict] = {}
        self.route_replies: Dict[str, Dict] = {}

    def initiate_route_discovery(self, destination: str) -> Dict:
        """Initiate route discovery for a destination."""
        request_id = f"{self.device_id}_{int(time.time())}"

        route_request = {
            'type': 'RREQ',
            'source': self.device_id,
            'destination': destination,
            'request_id': request_id,
            'hop_count': 0,
            'source_seq': 0,
            'destination_seq': 0
        }

        self.route_requests[request_id] = route_request
        return route_request

    def process_route_request(self, request: Dict) -> Optional[Dict]:
        """Process incoming route request."""
        if request['hop_count'] >= self.max_hops:
            return None

        # Check if we have a route to destination
        if request['destination'] in self.routing_table:
            # Send route reply
            reply = {
                'type': 'RREP',
                'source': request['source'],
                'destination': request['destination'],
                'request_id': request['request_id'],
                'hop_count': 0,
                'lifetime': 300  # 5 minutes
            }
            return reply

        # Forward request with incremented hop count
        request['hop_count'] += 1
        return request

    def process_route_reply(self, reply: Dict):
        """Process incoming route reply."""
        destination = reply['destination']
        hop_count = reply['hop_count'] + 1

        # Update routing table
        self.routing_table[destination] = {
            'next_hop': reply.get('next_hop', reply['source']),
            'hops': hop_count,
            'quality': 1.0 / hop_count,  # Quality decreases with hop count
            'last_seen': time.time()
        }

        logger.info(f"Updated route to {destination} via {self.routing_table[destination]['next_hop']}")
