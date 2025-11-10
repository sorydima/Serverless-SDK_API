"""
AI Quantum Core Module for SynapseSDK

This module provides quantum-inspired AI capabilities for the REChain network,
including graph neural networks for device relationship modeling and
federated learning across mesh networks.
"""

__version__ = "1.0.0"
__author__ = "REChain AI Solutions"

from .device_graph import DeviceGraph
from .quantum_optimizer import QuantumPacketOptimizer, RoutingConstraints, RoutingPath

# Optional imports - only load if dependencies are available
try:
    from .graph_trainer import QuantumGraphTrainer
    _HAS_TORCH = True
except ImportError:
    _HAS_TORCH = False
    QuantumGraphTrainer = None

__all__ = ['DeviceGraph', 'QuantumPacketOptimizer', 'RoutingConstraints', 'RoutingPath']

if _HAS_TORCH:
    __all__.append('QuantumGraphTrainer')
