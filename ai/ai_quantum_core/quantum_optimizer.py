"""
Quantum-Inspired Packet Routing Optimizer

This module implements quantum-inspired optimization algorithms for packet routing
in mesh networks. It uses simulated quantum annealing and quantum-inspired
metaheuristics to find optimal routing paths that minimize latency, maximize
throughput, and balance network load.
"""

import numpy as np
import random
import math
from typing import List, Dict, Tuple, Optional, Any, Set
import logging
import time
from dataclasses import dataclass
from collections import defaultdict

from .device_graph import DeviceGraph

logger = logging.getLogger(__name__)


@dataclass
class RoutingConstraints:
    """Constraints for packet routing optimization"""
    max_hops: int = 10
    max_latency_ms: float = 100.0
    min_bandwidth_mbps: float = 1.0
    avoid_nodes: Set[str] = None
    prefer_nodes: Set[str] = None
    priority_level: int = 1  # 1-10, higher = more important

    def __post_init__(self):
        if self.avoid_nodes is None:
            self.avoid_nodes = set()
        if self.prefer_nodes is None:
            self.prefer_nodes = set()


@dataclass
class RoutingPath:
    """Represents a routing path with metrics"""
    nodes: List[str]
    total_latency: float
    total_bandwidth: float
    hop_count: int
    reliability_score: float
    energy_cost: float
    fitness_score: float = 0.0


class QuantumAnnealingOptimizer:
    """
    Simulated Quantum Annealing for routing optimization

    Uses quantum-inspired annealing to explore the solution space
    and find optimal routing paths.
    """

    def __init__(self, temperature: float = 1.0, cooling_rate: float = 0.95,
                 max_iterations: int = 1000, quantum_fluctuation: float = 0.1):
        self.temperature = temperature
        self.cooling_rate = cooling_rate
        self.max_iterations = max_iterations
        self.quantum_fluctuation = quantum_fluctuation

    def optimize(self, cost_function: callable, initial_solution: Any,
                 constraints: RoutingConstraints) -> Any:
        """
        Perform quantum annealing optimization

        Args:
            cost_function: Function to evaluate solution cost
            initial_solution: Starting solution
            constraints: Routing constraints

        Returns:
            Optimized solution
        """
        current_solution = initial_solution
        current_cost = cost_function(current_solution, constraints)
        best_solution = current_solution
        best_cost = current_cost

        for iteration in range(self.max_iterations):
            # Generate quantum-fluctuated neighbor
            neighbor = self._generate_quantum_neighbor(current_solution, constraints)

            if neighbor is None:
                continue

            neighbor_cost = cost_function(neighbor, constraints)

            # Acceptance probability (quantum-inspired)
            delta_cost = neighbor_cost - current_cost
            quantum_factor = self.quantum_fluctuation * math.sqrt(self.temperature)

            if delta_cost < 0 or random.random() < math.exp(-delta_cost / (self.temperature + quantum_factor)):
                current_solution = neighbor
                current_cost = neighbor_cost

                if current_cost < best_cost:
                    best_solution = current_solution
                    best_cost = current_cost

            # Cool down
            self.temperature *= self.cooling_rate

            # Early stopping if temperature is too low
            if self.temperature < 0.01:
                break

        return best_solution

    def _generate_quantum_neighbor(self, solution: RoutingPath,
                                  constraints: RoutingConstraints) -> Optional[RoutingPath]:
        """Generate a quantum-fluctuated neighboring solution"""
        try:
            # Quantum tunneling: allow jumps to distant solutions
            if random.random() < self.quantum_fluctuation:
                return self._quantum_tunnel(solution, constraints)
            else:
                return self._classical_neighbor(solution, constraints)
        except Exception as e:
            logger.debug(f"Failed to generate quantum neighbor: {e}")
            return None

    def _quantum_tunnel(self, solution: RoutingPath,
                       constraints: RoutingConstraints) -> RoutingPath:
        """Quantum tunneling to distant solutions"""
        # Create a completely new random path
        start_node = solution.nodes[0]
        end_node = solution.nodes[-1]

        # Generate random intermediate nodes
        intermediate_count = random.randint(1, min(5, constraints.max_hops - 2))
        intermediate_nodes = [f"node_{random.randint(0, 100)}" for _ in range(intermediate_count)]

        new_path = RoutingPath(
            nodes=[start_node] + intermediate_nodes + [end_node],
            total_latency=0.0,  # Will be calculated
            total_bandwidth=0.0,
            hop_count=len(intermediate_nodes) + 1,
            reliability_score=0.5,
            energy_cost=0.0
        )

        return new_path

    def _classical_neighbor(self, solution: RoutingPath,
                           constraints: RoutingConstraints) -> RoutingPath:
        """Generate classical neighboring solution"""
        # Swap two random nodes or add/remove intermediate nodes
        new_nodes = solution.nodes.copy()

        if len(new_nodes) > 2 and random.random() < 0.5:
            # Swap two intermediate nodes
            idx1, idx2 = random.sample(range(1, len(new_nodes) - 1), 2)
            new_nodes[idx1], new_nodes[idx2] = new_nodes[idx2], new_nodes[idx1]
        elif random.random() < 0.3 and len(new_nodes) < constraints.max_hops:
            # Add random intermediate node
            insert_pos = random.randint(1, len(new_nodes) - 1)
            new_node = f"node_{random.randint(0, 100)}"
            new_nodes.insert(insert_pos, new_node)
        elif len(new_nodes) > 2 and random.random() < 0.2:
            # Remove random intermediate node
            remove_pos = random.randint(1, len(new_nodes) - 2)
            new_nodes.pop(remove_pos)

        return RoutingPath(
            nodes=new_nodes,
            total_latency=solution.total_latency,
            total_bandwidth=solution.total_bandwidth,
            hop_count=len(new_nodes) - 1,
            reliability_score=solution.reliability_score,
            energy_cost=solution.energy_cost
        )


class QuantumPacketOptimizer:
    """
    Quantum-inspired packet routing optimizer for mesh networks

    Uses quantum annealing and other quantum-inspired algorithms to find
    optimal routing paths that consider multiple objectives like latency,
    bandwidth, reliability, and energy efficiency.
    """

    def __init__(self, device_graph: DeviceGraph,
                 annealing_temp: float = 1.0,
                 max_iterations: int = 500):
        self.device_graph = device_graph
        self.annealer = QuantumAnnealingOptimizer(
            temperature=annealing_temp,
            max_iterations=max_iterations
        )

        # Multi-objective weights
        self.weights = {
            'latency': 0.4,
            'bandwidth': 0.3,
            'reliability': 0.2,
            'energy': 0.1
        }

        # Cache for computed paths
        self.path_cache: Dict[Tuple[str, str], RoutingPath] = {}
        self.cache_timeout = 300  # 5 minutes

        logger.info("Initialized Quantum Packet Optimizer")

    def optimize_route(self, source: str, destination: str,
                      constraints: RoutingConstraints) -> Optional[RoutingPath]:
        """
        Find optimal routing path using quantum optimization

        Args:
            source: Source node ID
            destination: Destination node ID
            constraints: Routing constraints

        Returns:
            Optimal routing path or None if no path found
        """
        try:
            # Check cache first
            cache_key = (source, destination, hash(str(constraints)))
            if cache_key in self.path_cache:
                cached_path = self.path_cache[cache_key]
                if time.time() - cached_path.fitness_score < self.cache_timeout:  # Using fitness_score as timestamp
                    return cached_path

            # Generate initial solution
            initial_path = self._generate_initial_path(source, destination, constraints)
            if initial_path is None:
                return None

            # Optimize using quantum annealing
            optimized_path = self.annealer.optimize(
                cost_function=self._evaluate_path_cost,
                initial_solution=initial_path,
                constraints=constraints
            )

            # Calculate final metrics
            self._calculate_path_metrics(optimized_path)

            # Cache result
            optimized_path.fitness_score = time.time()  # Store timestamp in fitness_score
            self.path_cache[cache_key] = optimized_path

            logger.info(f"Optimized route from {source} to {destination}: "
                       f"{len(optimized_path.nodes)} hops, "
                       f"latency: {optimized_path.total_latency:.2f}ms")

            return optimized_path

        except Exception as e:
            logger.error(f"Route optimization failed: {e}")
            return None

    def _generate_initial_path(self, source: str, destination: str,
                              constraints: RoutingConstraints) -> Optional[RoutingPath]:
        """Generate initial routing path"""
        try:
            # Use shortest path as initial solution
            shortest_path = self.device_graph.get_shortest_path(source, destination)
            if shortest_path is None:
                return None

            path = RoutingPath(
                nodes=shortest_path,
                total_latency=0.0,
                total_bandwidth=0.0,
                hop_count=len(shortest_path) - 1,
                reliability_score=0.8,
                energy_cost=0.0
            )

            self._calculate_path_metrics(path)
            return path

        except Exception as e:
            logger.debug(f"Failed to generate initial path: {e}")
            return None

    def _evaluate_path_cost(self, path: RoutingPath,
                           constraints: RoutingConstraints) -> float:
        """
        Evaluate the cost of a routing path

        Returns a multi-objective cost function combining latency, bandwidth,
        reliability, and energy efficiency.
        """
        try:
            # Calculate path metrics
            self._calculate_path_metrics(path)

            # Check constraints
            if path.hop_count > constraints.max_hops:
                return float('inf')
            if path.total_latency > constraints.max_latency_ms:
                return float('inf')
            if path.total_bandwidth < constraints.min_bandwidth_mbps:
                return float('inf')
            if any(node in constraints.avoid_nodes for node in path.nodes):
                return float('inf')

            # Multi-objective cost function
            latency_cost = path.total_latency / constraints.max_latency_ms
            bandwidth_cost = 1.0 - (path.total_bandwidth / 100.0)  # Assume 100 Mbps max
            reliability_cost = 1.0 - path.reliability_score
            energy_cost = path.energy_cost / 10.0  # Normalize

            # Apply preference bonuses
            preference_bonus = 0.0
            if constraints.prefer_nodes:
                preferred_count = sum(1 for node in path.nodes if node in constraints.prefer_nodes)
                preference_bonus = preferred_count / len(path.nodes) * 0.1

            # Priority scaling
            priority_scale = 1.0 / constraints.priority_level

            total_cost = (
                self.weights['latency'] * latency_cost +
                self.weights['bandwidth'] * bandwidth_cost +
                self.weights['reliability'] * reliability_cost +
                self.weights['energy'] * energy_cost -
                preference_bonus
            ) * priority_scale

            return max(0, total_cost)

        except Exception as e:
            logger.debug(f"Path evaluation failed: {e}")
            return float('inf')

    def _calculate_path_metrics(self, path: RoutingPath):
        """Calculate detailed metrics for a routing path"""
        try:
            total_latency = 0.0
            total_bandwidth = float('inf')
            total_energy = 0.0
            reliability_factors = []

            for i in range(len(path.nodes) - 1):
                node1, node2 = path.nodes[i], path.nodes[i + 1]

                # Get connection info from device graph
                # This is simplified - in practice would query network state
                latency = random.uniform(1, 10)  # Simulated latency in ms
                bandwidth = random.uniform(10, 100)  # Simulated bandwidth in Mbps
                energy = random.uniform(0.1, 1.0)  # Simulated energy cost
                reliability = random.uniform(0.8, 0.99)  # Simulated reliability

                total_latency += latency
                total_bandwidth = min(total_bandwidth, bandwidth)
                total_energy += energy
                reliability_factors.append(reliability)

            # Calculate overall reliability (product of individual reliabilities)
            path.reliability_score = math.prod(reliability_factors) if reliability_factors else 0.0
            path.total_latency = total_latency
            path.total_bandwidth = total_bandwidth
            path.energy_cost = total_energy
            path.hop_count = len(path.nodes) - 1

        except Exception as e:
            logger.debug(f"Metrics calculation failed: {e}")
            # Set default values
            path.total_latency = 100.0
            path.total_bandwidth = 1.0
            path.reliability_score = 0.5
            path.energy_cost = 1.0

    def optimize_multiple_routes(self, route_requests: List[Tuple[str, str, RoutingConstraints]],
                                max_parallel: int = 5) -> List[Optional[RoutingPath]]:
        """
        Optimize multiple routing requests in parallel

        Args:
            route_requests: List of (source, dest, constraints) tuples
            max_parallel: Maximum number of parallel optimizations

        Returns:
            List of optimized paths
        """
        results = []

        # Process in batches to avoid overwhelming the system
        for i in range(0, len(route_requests), max_parallel):
            batch = route_requests[i:i + max_parallel]
            batch_results = []

            for source, dest, constraints in batch:
                path = self.optimize_route(source, dest, constraints)
                batch_results.append(path)

            results.extend(batch_results)

        return results

    def update_network_state(self, link_updates: Dict[Tuple[str, str], Dict[str, float]]):
        """
        Update network state information for optimization

        Args:
            link_updates: Dictionary of (node1, node2) -> metrics
        """
        # This would update the device graph with real-time network metrics
        # For now, just log the updates
        logger.debug(f"Updated network state for {len(link_updates)} links")

    def get_optimizer_stats(self) -> Dict[str, Any]:
        """Get optimizer performance statistics"""
        return {
            'cache_size': len(self.path_cache),
            'cache_hit_rate': 0.0,  # Would need to track hits vs misses
            'average_path_length': np.mean([p.hop_count for p in self.path_cache.values()]) if self.path_cache else 0,
            'total_optimizations': len(self.path_cache)
        }


# Convenience functions
def create_quantum_optimizer(device_graph: DeviceGraph,
                           annealing_temp: float = 1.0) -> QuantumPacketOptimizer:
    """Factory function to create quantum packet optimizer"""
    return QuantumPacketOptimizer(device_graph, annealing_temp)


def optimize_packet_route(source: str, destination: str,
                         device_graph: DeviceGraph,
                         constraints: Optional[RoutingConstraints] = None) -> Optional[RoutingPath]:
    """Convenience function for single route optimization"""
    if constraints is None:
        constraints = RoutingConstraints()

    optimizer = QuantumPacketOptimizer(device_graph)
    return optimizer.optimize_route(source, destination, constraints)


# Example usage
if __name__ == "__main__":
    # Create a simple device graph for testing
    graph = DeviceGraph()

    # Add some test devices
    for i in range(10):
        graph.add_device(f"node_{i}", {"type": "router", "capacity": 100})

    # Add connections
    for i in range(9):
        graph.add_connection(f"node_{i}", f"node_{i+1}", weight=1.0)

    # Create optimizer
    optimizer = QuantumPacketOptimizer(graph)

    # Test optimization
    constraints = RoutingConstraints(max_hops=5, max_latency_ms=50.0)
    path = optimizer.optimize_route("node_0", "node_9", constraints)

    if path:
        print(f"Optimized path: {' -> '.join(path.nodes)}")
        print(f"Metrics: {path.total_latency:.2f}ms latency, "
              f"{path.total_bandwidth:.2f} Mbps bandwidth, "
              f"{path.reliability_score:.3f} reliability")
    else:
        print("No path found")

    # Test multiple route optimization
    route_requests = [
        ("node_0", "node_3", RoutingConstraints(max_hops=4)),
        ("node_1", "node_7", RoutingConstraints(max_hops=6)),
        ("node_2", "node_8", RoutingConstraints(max_hops=5))
    ]

    print("\nOptimizing multiple routes...")
    results = optimizer.optimize_multiple_routes(route_requests, max_parallel=2)

    for i, path in enumerate(results):
        if path:
            print(f"Route {i+1}: {' -> '.join(path.nodes)} "
                  f"(hops: {path.hop_count}, latency: {path.total_latency:.2f}ms)")
        else:
            print(f"Route {i+1}: No path found")

    # Print optimizer stats
    stats = optimizer.get_optimizer_stats()
    print(f"\nOptimizer Stats: {stats}")
