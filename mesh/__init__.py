"""
Mesh Networking Module for Offline and Decentralized Communication

This module provides comprehensive mesh networking capabilities including:
- Bluetooth LE mesh for offline message transmission
- Wi-Fi Direct peer-to-peer communication
- UDP multicast discovery and topology management
- Offline voting applications with consensus
- Data synchronization protocols for offline nodes

The mesh networking layer enables decentralized, offline-first communication
between devices without relying on traditional internet infrastructure.
"""

try:
    from .bluetooth_mesh import BLEMeshNode, BLEMeshNetwork, BLEEncryption
    BLUETOOTH_AVAILABLE = True
except ImportError:
    BLUETOOTH_AVAILABLE = False
    BLEMeshNode = None
    BLEMeshNetwork = None
    BLEEncryption = None

try:
    from .wifi_direct_mesh import WiFiDirectMeshNode, WiFiDirectMeshNetwork, WiFiDirectGroup
    WIFI_DIRECT_AVAILABLE = True
except ImportError:
    WIFI_DIRECT_AVAILABLE = False
    WiFiDirectMeshNode = None
    WiFiDirectMeshNetwork = None
    WiFiDirectGroup = None

try:
    from .multicast_discovery import MulticastDiscoveryService, MulticastDiscoveryNetwork, TopologyManager
    MULTICAST_AVAILABLE = True
except ImportError:
    MULTICAST_AVAILABLE = False
    MulticastDiscoveryService = None
    MulticastDiscoveryNetwork = None
    TopologyManager = None

try:
    from .voting_app import MeshVotingApp, MeshVotingNetwork, VotingSession, Vote
    VOTING_AVAILABLE = True
except ImportError:
    VOTING_AVAILABLE = False
    MeshVotingApp = None
    MeshVotingNetwork = None
    VotingSession = None
    Vote = None

try:
    from .sync_protocol import MeshSyncProtocol, MeshSyncNetwork, SyncSession, DataChunk
    SYNC_AVAILABLE = True
except ImportError:
    SYNC_AVAILABLE = False
    MeshSyncProtocol = None
    MeshSyncNetwork = None
    SyncSession = None
    DataChunk = None

from .routing import MeshRouter
from .discovery import DeviceDiscovery

__all__ = [
    # Bluetooth LE Mesh (if available)
    'BLEMeshNode' if BLUETOOTH_AVAILABLE else None,
    'BLEMeshNetwork' if BLUETOOTH_AVAILABLE else None,
    'BLEEncryption' if BLUETOOTH_AVAILABLE else None,

    # Wi-Fi Direct Mesh (if available)
    'WiFiDirectMeshNode' if WIFI_DIRECT_AVAILABLE else None,
    'WiFiDirectMeshNetwork' if WIFI_DIRECT_AVAILABLE else None,
    'WiFiDirectGroup' if WIFI_DIRECT_AVAILABLE else None,

    # Multicast Discovery (if available)
    'MulticastDiscoveryService' if MULTICAST_AVAILABLE else None,
    'MulticastDiscoveryNetwork' if MULTICAST_AVAILABLE else None,
    'TopologyManager' if MULTICAST_AVAILABLE else None,

    # Voting Application (if available)
    'MeshVotingApp' if VOTING_AVAILABLE else None,
    'MeshVotingNetwork' if VOTING_AVAILABLE else None,
    'VotingSession' if VOTING_AVAILABLE else None,
    'Vote' if VOTING_AVAILABLE else None,

    # Sync Protocol (if available)
    'MeshSyncProtocol' if SYNC_AVAILABLE else None,
    'MeshSyncNetwork' if SYNC_AVAILABLE else None,
    'SyncSession' if SYNC_AVAILABLE else None,
    'DataChunk' if SYNC_AVAILABLE else None,

    # Legacy components (always available)
    'MeshRouter',
    'DeviceDiscovery'
]

# Filter out None values
__all__ = [item for item in __all__ if item is not None]

__version__ = "1.0.0"
__author__ = "REChain Network"
__description__ = "Decentralized mesh networking for offline communication and data synchronization"

def get_available_features():
    """Get list of available mesh networking features."""
    features = []
    if BLUETOOTH_AVAILABLE:
        features.append("bluetooth_mesh")
    if WIFI_DIRECT_AVAILABLE:
        features.append("wifi_direct_mesh")
    if MULTICAST_AVAILABLE:
        features.append("multicast_discovery")
    if VOTING_AVAILABLE:
        features.append("voting_app")
    if SYNC_AVAILABLE:
        features.append("sync_protocol")
    features.extend(["routing", "discovery"])  # Always available
    return features
