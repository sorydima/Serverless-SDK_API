"""
Device Discovery for Mesh Networks

This module handles automatic discovery of devices in mesh networks
using various protocols and mechanisms.
"""

import asyncio
from typing import Dict, List, Optional, Set
import logging
import socket
import json
import time
import random

logger = logging.getLogger(__name__)


class DeviceDiscovery:
    """
    Handles device discovery in mesh networks using multicast and broadcast.
    """

    MULTICAST_GROUP = '224.0.0.251'  # Link-local multicast
    DISCOVERY_PORT = 5353  # LLMNR port, commonly used for service discovery
    BROADCAST_PORT = 5354

    def __init__(self, device_id: str, device_info: Dict = None):
        self.device_id = device_id
        self.device_info = device_info or {}
        self.discovered_devices: Dict[str, Dict] = {}
        self.neighbors: Set[str] = set()
        self.running = False

        # Network sockets
        self.multicast_sock = None
        self.broadcast_sock = None

    async def start_discovery(self):
        """Start device discovery process."""
        self.running = True

        # Start multicast discovery
        asyncio.create_task(self._multicast_discovery())

        # Start broadcast discovery as fallback
        asyncio.create_task(self._broadcast_discovery())

        # Periodic cleanup of stale devices
        asyncio.create_task(self._cleanup_stale_devices())

        logger.info(f"Started device discovery for {self.device_id}")

    async def stop_discovery(self):
        """Stop device discovery process."""
        self.running = False

        if self.multicast_sock:
            self.multicast_sock.close()
        if self.broadcast_sock:
            self.broadcast_sock.close()

        logger.info("Stopped device discovery")

    async def _multicast_discovery(self):
        """Handle multicast-based device discovery."""
        try:
            # Create UDP socket for multicast
            self.multicast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.multicast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind to port
            self.multicast_sock.bind(('', self.DISCOVERY_PORT))

            # Join multicast group
            group = socket.inet_aton(self.MULTICAST_GROUP)
            mreq = group + socket.inet_aton('0.0.0.0')
            self.multicast_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

            # Set timeout for non-blocking receive
            self.multicast_sock.settimeout(1.0)

            while self.running:
                try:
                    data, addr = self.multicast_sock.recvfrom(1024)
                    await self._process_discovery_message(data.decode(), addr)
                except socket.timeout:
                    pass
                except Exception as e:
                    logger.error(f"Error in multicast discovery: {e}")

                # Send periodic announcements
                await self._send_multicast_announcement()
                await asyncio.sleep(random.uniform(5, 15))  # Random interval

        except Exception as e:
            logger.error(f"Failed to start multicast discovery: {e}")

    async def _broadcast_discovery(self):
        """Handle broadcast-based device discovery as fallback."""
        try:
            self.broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.broadcast_sock.bind(('', self.BROADCAST_PORT))
            self.broadcast_sock.settimeout(1.0)

            while self.running:
                try:
                    data, addr = self.broadcast_sock.recvfrom(1024)
                    await self._process_discovery_message(data.decode(), addr)
                except socket.timeout:
                    pass
                except Exception as e:
                    logger.error(f"Error in broadcast discovery: {e}")

                # Send periodic broadcast announcements
                await self._send_broadcast_announcement()
                await asyncio.sleep(random.uniform(10, 20))  # Less frequent than multicast

        except Exception as e:
            logger.error(f"Failed to start broadcast discovery: {e}")

    async def _send_multicast_announcement(self):
        """Send multicast announcement of this device."""
        try:
            announcement = {
                'type': 'device_announcement',
                'device_id': self.device_id,
                'device_info': self.device_info,
                'timestamp': time.time(),
                'capabilities': ['mesh_routing', 'blockchain_sync', 'ai_processing']
            }

            data = json.dumps(announcement).encode()
            self.multicast_sock.sendto(data, (self.MULTICAST_GROUP, self.DISCOVERY_PORT))

        except Exception as e:
            logger.error(f"Failed to send multicast announcement: {e}")

    async def _send_broadcast_announcement(self):
        """Send broadcast announcement of this device."""
        try:
            announcement = {
                'type': 'device_announcement',
                'device_id': self.device_id,
                'device_info': self.device_info,
                'timestamp': time.time(),
                'capabilities': ['mesh_routing', 'blockchain_sync', 'ai_processing']
            }

            data = json.dumps(announcement).encode()
            self.broadcast_sock.sendto(data, ('<broadcast>', self.BROADCAST_PORT))

        except Exception as e:
            logger.error(f"Failed to send broadcast announcement: {e}")

    async def _process_discovery_message(self, data: str, addr: tuple):
        """Process incoming discovery messages."""
        try:
            message = json.loads(data)

            if message.get('type') == 'device_announcement':
                device_id = message.get('device_id')
                if device_id and device_id != self.device_id:
                    # Update discovered devices
                    self.discovered_devices[device_id] = {
                        'info': message.get('device_info', {}),
                        'address': addr[0],
                        'port': addr[1],
                        'capabilities': message.get('capabilities', []),
                        'last_seen': message.get('timestamp', time.time()),
                        'distance': self._estimate_distance(addr[0])
                    }

                    # Add to neighbors if close enough
                    if self.discovered_devices[device_id]['distance'] < 100:  # Within 100m
                        self.neighbors.add(device_id)

                    logger.info(f"Discovered device {device_id} at {addr[0]}")

        except json.JSONDecodeError:
            logger.warning(f"Invalid discovery message from {addr}")
        except Exception as e:
            logger.error(f"Error processing discovery message: {e}")

    def _estimate_distance(self, ip_address: str) -> float:
        """Estimate physical distance to device based on IP (simplified)."""
        # In a real implementation, this would use signal strength, GPS, etc.
        # For now, return a random distance for simulation
        return random.uniform(1, 1000)

    async def _cleanup_stale_devices(self):
        """Remove devices that haven't been seen recently."""
        while self.running:
            current_time = time.time()
            stale_devices = []

            for device_id, info in self.discovered_devices.items():
                if current_time - info['last_seen'] > 300:  # 5 minutes
                    stale_devices.append(device_id)

            for device_id in stale_devices:
                del self.discovered_devices[device_id]
                self.neighbors.discard(device_id)
                logger.info(f"Removed stale device {device_id}")

            await asyncio.sleep(60)  # Check every minute

    def get_discovered_devices(self) -> Dict[str, Dict]:
        """Get list of currently discovered devices."""
        return self.discovered_devices.copy()

    def get_neighbors(self) -> Set[str]:
        """Get set of neighboring devices."""
        return self.neighbors.copy()

    def find_devices_by_capability(self, capability: str) -> List[str]:
        """Find devices that have a specific capability."""
        return [
            device_id for device_id, info in self.discovered_devices.items()
            if capability in info.get('capabilities', [])
        ]

    def get_discovery_stats(self) -> Dict[str, int]:
        """Get discovery statistics."""
        return {
            'total_discovered': len(self.discovered_devices),
            'neighbors': len(self.neighbors),
            'multicast_active': self.multicast_sock is not None,
            'broadcast_active': self.broadcast_sock is not None
        }


class BLEDeviceDiscovery(DeviceDiscovery):
    """
    Bluetooth Low Energy based device discovery for close-range mesh networks.
    """

    def __init__(self, device_id: str, device_info: Dict = None):
        super().__init__(device_id, device_info)
        self.ble_devices: Dict[str, Dict] = {}

    async def start_ble_discovery(self):
        """Start BLE-based discovery."""
        # Note: This would require platform-specific BLE libraries
        # For now, simulate BLE discovery
        logger.info("BLE discovery not implemented - requires platform-specific libraries")
        pass

    async def _simulate_ble_discovery(self):
        """Simulate BLE device discovery for testing."""
        while self.running:
            # Simulate finding nearby BLE devices
            fake_device_id = f"ble_{random.randint(1000, 9999)}"
            self.ble_devices[fake_device_id] = {
                'rssi': random.randint(-90, -30),
                'last_seen': time.time()
            }
            await asyncio.sleep(random.uniform(5, 20))
