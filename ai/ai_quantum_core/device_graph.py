"""
Device Graph representation for mesh network connections.
"""

try:
    import networkx as nx
    _HAS_NETWORKX = True
except ImportError:
    _HAS_NETWORKX = False
    nx = None

from typing import Dict, List, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)


class DeviceGraph:
    """
    Represents a graph of device connections in a mesh network.
    """

    def __init__(self):
        if not _HAS_NETWORKX:
            logger.warning("NetworkX not available. Using simplified graph implementation.")
            self.graph = None
            self.device_features = {}
            self._nodes = set()
            self._edges = []
        else:
            self.graph = nx.Graph()
            self.device_features = {}

    def add_device(self, device_id: str, features: Dict[str, Any]):
        """
        Add a device to the graph with its features.

        Args:
            device_id: Unique identifier for the device
            features: Dictionary of device features (e.g., location, capabilities)
        """
        if self.graph is not None:
            self.graph.add_node(device_id)
            self.device_features[device_id] = features
        else:
            self._nodes.add(device_id)
            self.device_features[device_id] = features

    def add_connection(self, device1: str, device2: str, weight: float = 1.0,
                      connection_type: str = "wireless"):
        """
        Add a connection between two devices.

        Args:
            device1: First device ID
            device2: Second device ID
            weight: Connection strength/weight
            connection_type: Type of connection (wireless, wired, etc.)
        """
        if self.graph is not None:
            self.graph.add_edge(device1, device2, weight=weight,
                               connection_type=connection_type)
        else:
            if device1 in self._nodes and device2 in self._nodes:
                self._edges.append((device1, device2, weight, connection_type))

    def get_neighbors(self, device_id: str) -> List[str]:
        """Get list of neighboring devices."""
        if self.graph is not None:
            return list(self.graph.neighbors(device_id))
        else:
            neighbors = []
            for edge in self._edges:
                if edge[0] == device_id:
                    neighbors.append(edge[1])
                elif edge[1] == device_id:
                    neighbors.append(edge[0])
            return neighbors

    def get_shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        """Find shortest path between two devices."""
        if self.graph is not None:
            try:
                return nx.shortest_path(self.graph, source, target, weight='weight')
            except nx.NetworkXNoPath:
                return None
        else:
            # Simple BFS implementation
            return self._simple_bfs(source, target)

    def _simple_bfs(self, start: str, goal: str) -> Optional[List[str]]:
        """Simple BFS for fallback implementation."""
        if start not in self._nodes or goal not in self._nodes:
            return None

        visited = set()
        queue = [[start]]

        while queue:
            path = queue.pop(0)
            node = path[-1]

            if node not in visited:
                neighbors = self.get_neighbors(node)
                for neighbor in neighbors:
                    new_path = path + [neighbor]
                    queue.append(new_path)
                    if neighbor == goal:
                        return new_path

                visited.add(node)

        return None

    def get_graph_features(self) -> Dict[str, Any]:
        """Extract graph-level features for ML training."""
        if self.graph is not None:
            features = {
                'num_nodes': self.graph.number_of_nodes(),
                'num_edges': self.graph.number_of_edges(),
                'average_degree': sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes() if self.graph.number_of_nodes() > 0 else 0,
                'density': nx.density(self.graph),
                'is_connected': nx.is_connected(self.graph),
                'diameter': nx.diameter(self.graph) if nx.is_connected(self.graph) else float('inf')
            }
        else:
            features = {
                'num_nodes': len(self._nodes),
                'num_edges': len(self._edges),
                'average_degree': (2 * len(self._edges)) / len(self._nodes) if self._nodes else 0,
                'density': (2 * len(self._edges)) / (len(self._nodes) * (len(self._nodes) - 1)) if len(self._nodes) > 1 else 0,
                'is_connected': self._is_connected_simple(),
                'diameter': float('inf')  # Simplified
            }
        return features

    def _is_connected_simple(self) -> bool:
        """Simple connectivity check."""
        if not self._nodes:
            return True
        start = next(iter(self._nodes))
        visited = set()
        self._dfs_simple(start, visited)
        return len(visited) == len(self._nodes)

    def _dfs_simple(self, node: str, visited: set):
        """Simple DFS for connectivity."""
        visited.add(node)
        for neighbor in self.get_neighbors(node):
            if neighbor not in visited:
                self._dfs_simple(neighbor, visited)

    def to_json(self) -> str:
        """Serialize graph to JSON."""
        if self.graph is not None:
            data = {
                'nodes': list(self.graph.nodes()),
                'edges': list(self.graph.edges(data=True)),
                'features': self.device_features
            }
        else:
            data = {
                'nodes': list(self._nodes),
                'edges': self._edges,
                'features': self.device_features
            }
        return json.dumps(data, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'DeviceGraph':
        """Deserialize graph from JSON."""
        data = json.loads(json_str)
        graph = cls()
        if graph.graph is not None:
            graph.graph.add_nodes_from(data['nodes'])
            graph.graph.add_edges_from(data['edges'])
        else:
            graph._nodes = set(data['nodes'])
            graph._edges = data['edges']
        graph.device_features = data['features']
        return graph
