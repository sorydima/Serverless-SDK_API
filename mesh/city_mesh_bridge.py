"""
City Mesh Bridge Module

Provides integration between the app's mesh networking and city IoT infrastructure:
- MQTT communication with city IoT devices
- CoAP protocol support for constrained devices
- LoRaWAN gateway integration
- Smart city sensor data aggregation
- Traffic light and infrastructure control
- Emergency broadcast systems

This module acts as a bridge between decentralized mesh networks
and centralized city IoT systems for enhanced urban connectivity.
"""

import asyncio
import json
import logging
import struct
from typing import Dict, List, Optional, Tuple, Any, Callable, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import socket
import threading
from concurrent.futures import ThreadPoolExecutor
import paho.mqtt.client as mqtt
import ssl
import hashlib
import hmac
import base64

# Import mesh components
from .bluetooth_mesh import BluetoothMesh
from .wifi_direct_mesh import WiFiDirectMesh
from .multicast_discovery import MulticastDiscovery
from .routing import MeshRouter

logger = logging.getLogger(__name__)

@dataclass
class IoTDevice:
    """IoT device information"""
    device_id: str
    device_type: str  # 'sensor', 'actuator', 'gateway', 'beacon'
    protocol: str  # 'mqtt', 'coap', 'lora', 'zigbee'
    location: Tuple[float, float]  # lat, lon
    capabilities: List[str]
    last_seen: datetime
    status: str  # 'online', 'offline', 'maintenance'
    metadata: Dict[str, Any]

@dataclass
class CityService:
    """City service endpoint"""
    service_id: str
    service_type: str  # 'traffic', 'emergency', 'utilities', 'transport'
    endpoint: str
    protocol: str
    authentication: Dict[str, Any]
    capabilities: List[str]

@dataclass
class SensorData:
    """Sensor data packet"""
    device_id: str
    sensor_type: str
    value: Any
    unit: str
    timestamp: datetime
    location: Optional[Tuple[float, float]]
    quality: float  # 0.0 to 1.0
    metadata: Dict[str, Any]

@dataclass
class ControlCommand:
    """Control command for actuators"""
    command_id: str
    device_id: str
    action: str
    parameters: Dict[str, Any]
    priority: int  # 0-10, higher is more urgent
    timeout: int  # seconds
    source: str

class CityMeshBridgeError(Exception):
    """Custom exception for bridge operations"""
    pass

class MQTTClient:
    """MQTT client for city IoT communication"""

    def __init__(self, broker_host: str, broker_port: int = 1883,
                 client_id: str = None, tls: bool = False,
                 username: str = None, password: str = None):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id or f"mesh_bridge_{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}"
        self.tls = tls
        self.username = username
        self.password = password

        self.client = mqtt.Client(client_id=self.client_id)
        self.connected = False
        self.subscriptions: Dict[str, Callable] = {}

        # Setup authentication
        if username and password:
            self.client.username_pw_set(username, password)

        # Setup TLS
        if tls:
            self.client.tls_set(cert_reqs=ssl.CERT_NONE)
            self.client.tls_insecure_set(True)

        # Setup callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.connected = True
            logger.info(f"MQTT connected to {self.broker_host}:{self.broker_port}")
            # Resubscribe to topics
            for topic in self.subscriptions:
                self.client.subscribe(topic)
        else:
            logger.error(f"MQTT connection failed: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.connected = False
        logger.info(f"MQTT disconnected: {rc}")

    def _on_message(self, client, userdata, message):
        """MQTT message callback"""
        try:
            topic = message.topic
            payload = message.payload.decode('utf-8')

            if topic in self.subscriptions:
                # Parse JSON payload
                try:
                    data = json.loads(payload)
                except json.JSONDecodeError:
                    data = payload

                # Call callback
                asyncio.create_task(self.subscriptions[topic](data, topic))

        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    async def connect(self):
        """Connect to MQTT broker"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.client.connect,
                                 self.broker_host, self.broker_port, 60)
        self.client.loop_start()

    async def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        await asyncio.get_event_loop().run_in_executor(None, self.client.disconnect)

    async def publish(self, topic: str, payload: Any, qos: int = 0, retain: bool = False):
        """Publish message to topic"""
        if isinstance(payload, (dict, list)):
            payload = json.dumps(payload)

        await asyncio.get_event_loop().run_in_executor(
            None, self.client.publish, topic, payload, qos, retain
        )

    async def subscribe(self, topic: str, callback: Callable):
        """Subscribe to topic"""
        self.subscriptions[topic] = callback
        if self.connected:
            await asyncio.get_event_loop().run_in_executor(
                None, self.client.subscribe, topic
            )

class CoAPClient:
    """CoAP client for constrained IoT devices"""

    def __init__(self, host: str, port: int = 5683):
        self.host = host
        self.port = port
        # Note: This would require aiocoap library
        # self.client = aiocoap.ClientSession()

    async def get(self, path: str) -> Dict[str, Any]:
        """GET request"""
        # Placeholder implementation
        # In real implementation, this would use aiocoap
        logger.warning("CoAP client not fully implemented - requires aiocoap library")
        return {}

    async def post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """POST request"""
        # Placeholder implementation
        logger.warning("CoAP client not fully implemented - requires aiocoap library")
        return {}

class LoRaWANClient:
    """LoRaWAN client for long-range IoT communication"""

    def __init__(self, gateway_host: str, app_key: str, dev_eui: str):
        self.gateway_host = gateway_host
        self.app_key = app_key
        self.dev_eui = dev_eui
        # This would integrate with LoRaWAN libraries like lora-python

    async def send_uplink(self, data: bytes, port: int = 1):
        """Send uplink message"""
        # Placeholder implementation
        logger.warning("LoRaWAN client not fully implemented")
        pass

    async def receive_downlink(self) -> Optional[bytes]:
        """Receive downlink message"""
        # Placeholder implementation
        return None

class CityMeshBridge:
    """
    Bridge between mesh networks and city IoT infrastructure

    Provides seamless integration between decentralized mesh networking
    and centralized city IoT systems for enhanced urban connectivity.
    """

    def __init__(self, mesh_router: MeshRouter):
        self.mesh_router = mesh_router

        # IoT device registry
        self.devices: Dict[str, IoTDevice] = {}
        self.city_services: Dict[str, CityService] = {}

        # Protocol clients
        self.mqtt_clients: Dict[str, MQTTClient] = {}
        self.coap_clients: Dict[str, CoAPClient] = {}
        self.lorawan_clients: Dict[str, LoRaWANClient] = {}

        # Data processing
        self.executor = ThreadPoolExecutor(max_workers=8)
        self.data_queue = asyncio.Queue()
        self.command_queue = asyncio.Queue()

        # Statistics
        self.stats = {
            'messages_processed': 0,
            'commands_executed': 0,
            'devices_online': 0,
            'data_points': 0
        }

        # Configuration
        self.device_timeout = timedelta(minutes=5)
        self.max_retry_attempts = 3
        self.command_timeout = 30  # seconds

    async def initialize(self):
        """Initialize the bridge"""
        logger.info("Initializing City Mesh Bridge")

        # Load city services configuration
        await self._load_city_services()

        # Start background tasks
        asyncio.create_task(self._process_data_queue())
        asyncio.create_task(self._process_command_queue())
        asyncio.create_task(self._device_health_monitor())

        logger.info("City Mesh Bridge initialized")

    async def shutdown(self):
        """Shutdown the bridge"""
        logger.info("Shutting down City Mesh Bridge")

        # Disconnect all clients
        for client in self.mqtt_clients.values():
            await client.disconnect()

        self.executor.shutdown(wait=True)

        logger.info("City Mesh Bridge shutdown complete")

    async def _load_city_services(self):
        """Load city service configurations"""
        # This would load from configuration files or APIs
        # Placeholder implementation
        self.city_services = {
            'traffic_lights': CityService(
                service_id='traffic_control',
                service_type='traffic',
                endpoint='mqtt://traffic.city.gov:1883/traffic',
                protocol='mqtt',
                authentication={'username': 'mesh_bridge', 'password': 'secret'},
                capabilities=['control_signals', 'get_status']
            ),
            'emergency_broadcast': CityService(
                service_id='emergency_system',
                service_type='emergency',
                endpoint='mqtt://emergency.city.gov:1883/alerts',
                protocol='mqtt',
                authentication={'username': 'mesh_bridge', 'password': 'secret'},
                capabilities=['broadcast_alert', 'receive_alerts']
            ),
            'utilities_monitor': CityService(
                service_id='power_grid',
                service_type='utilities',
                endpoint='coap://utilities.city.gov:5683/power',
                protocol='coap',
                authentication={},
                capabilities=['get_consumption', 'report_outage']
            )
        }

        # Initialize clients for services
        for service in self.city_services.values():
            await self._init_service_client(service)

    async def _init_service_client(self, service: CityService):
        """Initialize client for city service"""
        try:
            if service.protocol == 'mqtt':
                # Parse MQTT endpoint
                # endpoint format: mqtt://host:port/topic
                parts = service.endpoint.replace('mqtt://', '').split('/')
                host_port = parts[0].split(':')
                host = host_port[0]
                port = int(host_port[1]) if len(host_port) > 1 else 1883

                client = MQTTClient(
                    host, port,
                    username=service.authentication.get('username'),
                    password=service.authentication.get('password')
                )
                await client.connect()
                self.mqtt_clients[service.service_id] = client

            elif service.protocol == 'coap':
                # Parse CoAP endpoint
                parts = service.endpoint.replace('coap://', '').split(':')
                host = parts[0]
                port = int(parts[1]) if len(parts) > 1 else 5683

                client = CoAPClient(host, port)
                self.coap_clients[service.service_id] = client

        except Exception as e:
            logger.error(f"Failed to initialize client for {service.service_id}: {e}")

    async def register_device(self, device: IoTDevice):
        """Register an IoT device with the bridge"""
        self.devices[device.device_id] = device
        logger.info(f"Registered device: {device.device_id} ({device.device_type})")

        # Subscribe to device topics if MQTT
        if device.protocol == 'mqtt' and device.device_id in self.mqtt_clients:
            client = self.mqtt_clients[device.device_id]
            topic = f"devices/{device.device_id}/data"
            await client.subscribe(topic, self._handle_device_data)

    async def unregister_device(self, device_id: str):
        """Unregister an IoT device"""
        if device_id in self.devices:
            del self.devices[device_id]
            logger.info(f"Unregistered device: {device_id}")

    async def _handle_device_data(self, data: Any, topic: str):
        """Handle incoming device data"""
        try:
            # Parse topic to get device ID
            parts = topic.split('/')
            if len(parts) >= 3:
                device_id = parts[1]

                if device_id in self.devices:
                    device = self.devices[device_id]

                    # Create sensor data object
                    sensor_data = SensorData(
                        device_id=device_id,
                        sensor_type=data.get('type', 'unknown'),
                        value=data.get('value'),
                        unit=data.get('unit', ''),
                        timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
                        location=device.location,
                        quality=data.get('quality', 1.0),
                        metadata=data.get('metadata', {})
                    )

                    # Queue for processing
                    await self.data_queue.put(sensor_data)
                    self.stats['messages_processed'] += 1

        except Exception as e:
            logger.error(f"Error handling device data: {e}")

    async def _process_data_queue(self):
        """Process incoming sensor data"""
        while True:
            try:
                data: SensorData = await self.data_queue.get()

                # Process based on data type
                if data.sensor_type == 'traffic_flow':
                    await self._process_traffic_data(data)
                elif data.sensor_type == 'air_quality':
                    await self._process_environment_data(data)
                elif data.sensor_type == 'emergency':
                    await self._process_emergency_data(data)
                else:
                    await self._process_generic_data(data)

                # Forward to mesh network
                await self._forward_to_mesh(data)

                self.data_queue.task_done()

            except Exception as e:
                logger.error(f"Error processing data queue: {e}")

    async def _process_traffic_data(self, data: SensorData):
        """Process traffic sensor data"""
        # Analyze traffic patterns and optimize routing
        logger.debug(f"Processing traffic data from {data.device_id}")

        # This could integrate with routing algorithms
        # to provide real-time traffic-aware navigation

    async def _process_environment_data(self, data: SensorData):
        """Process environmental sensor data"""
        logger.debug(f"Processing environment data from {data.device_id}")

        # Monitor air quality, temperature, etc.
        # Could trigger alerts or adjust city systems

    async def _process_emergency_data(self, data: SensorData):
        """Process emergency sensor data"""
        logger.debug(f"Processing emergency data from {data.device_id}")

        # High-priority processing for emergency situations
        # Could trigger emergency broadcasts or route changes

    async def _process_generic_data(self, data: SensorData):
        """Process generic sensor data"""
        logger.debug(f"Processing generic data from {data.device_id}")

    async def _forward_to_mesh(self, data: SensorData):
        """Forward sensor data to mesh network"""
        try:
            # Convert to mesh message format
            mesh_message = {
                'type': 'sensor_data',
                'data': asdict(data),
                'timestamp': datetime.now().isoformat()
            }

            # Carry VIBE/context if present in metadata (optional)
            try:
                vibe = data.metadata.get('vibe') if isinstance(data.metadata, dict) else None
                if vibe is not None:
                    mesh_message['vibe'] = vibe
                    # Attempt to persist VIBE snapshot for later analysis
                    try:
                        from ai.vibe.persistence import persist_vibe
                        # If vibe is already a dict, create Vibe object
                        if isinstance(vibe, dict):
                            from ai.vibe.vibe import Vibe
                            vobj = Vibe.from_dict(vibe) if hasattr(Vibe, 'from_dict') else Vibe(level=vibe.get('level', 0.0), tags=vibe.get('tags', {}), timestamp=vibe.get('timestamp'))
                        else:
                            vobj = vibe
                        persist_vibe(vobj)
                    except Exception:
                        # Do not fail forwarding on persistence errors
                        pass
            except Exception:
                # Be resilient to malformed metadata
                pass

            # Send via mesh router
            await self.mesh_router.broadcast_message(mesh_message)

        except Exception as e:
            logger.error(f"Error forwarding data to mesh: {e}")

    async def send_control_command(self, command: ControlCommand):
        """Send control command to device or city service"""
        await self.command_queue.put(command)

    async def _process_command_queue(self):
        """Process outgoing control commands"""
        while True:
            try:
                command: ControlCommand = await self.command_queue.get()

                success = await self._execute_command(command)
                if success:
                    self.stats['commands_executed'] += 1

                self.command_queue.task_done()

            except Exception as e:
                logger.error(f"Error processing command queue: {e}")

    async def _execute_command(self, command: ControlCommand) -> bool:
        """Execute a control command"""
        try:
            if command.device_id in self.devices:
                # Device command
                device = self.devices[command.device_id]
                return await self._execute_device_command(device, command)
            elif command.device_id in self.city_services:
                # City service command
                service = self.city_services[command.device_id]
                return await self._execute_service_command(service, command)
            else:
                logger.error(f"Unknown command target: {command.device_id}")
                return False

        except Exception as e:
            logger.error(f"Error executing command {command.command_id}: {e}")
            return False

    async def _execute_device_command(self, device: IoTDevice, command: ControlCommand) -> bool:
        """Execute command on IoT device"""
        try:
            if device.protocol == 'mqtt' and device.device_id in self.mqtt_clients:
                client = self.mqtt_clients[device.device_id]
                topic = f"devices/{device.device_id}/commands"
                payload = {
                    'command_id': command.command_id,
                    'action': command.action,
                    'parameters': command.parameters,
                    'timestamp': datetime.now().isoformat()
                }
                await client.publish(topic, payload, qos=1)
                return True

            elif device.protocol == 'coap' and device.device_id in self.coap_clients:
                client = self.coap_clients[device.device_id]
                path = f"/commands/{command.action}"
                await client.post(path, command.parameters)
                return True

            else:
                logger.error(f"Unsupported protocol for device {device.device_id}: {device.protocol}")
                return False

        except Exception as e:
            logger.error(f"Error executing device command: {e}")
            return False

    async def _execute_service_command(self, service: CityService, command: ControlCommand) -> bool:
        """Execute command on city service"""
        try:
            if service.protocol == 'mqtt' and service.service_id in self.mqtt_clients:
                client = self.mqtt_clients[service.service_id]
                topic = f"services/{service.service_id}/commands"
                payload = {
                    'command_id': command.command_id,
                    'action': command.action,
                    'parameters': command.parameters,
                    'timestamp': datetime.now().isoformat()
                }
                await client.publish(topic, payload, qos=1)
                return True

            else:
                logger.error(f"Unsupported protocol for service {service.service_id}: {service.protocol}")
                return False

        except Exception as e:
            logger.error(f"Error executing service command: {e}")
            return False

    async def _device_health_monitor(self):
        """Monitor device health and update status"""
        while True:
            try:
                now = datetime.now()
                offline_devices = []

                for device_id, device in self.devices.items():
                    if now - device.last_seen > self.device_timeout:
                        if device.status != 'offline':
                            device.status = 'offline'
                            offline_devices.append(device_id)
                            self.stats['devices_online'] -= 1

                if offline_devices:
                    logger.info(f"Devices went offline: {offline_devices}")

                # Check for devices that came back online
                # This would require additional heartbeat monitoring

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in device health monitor: {e}")
                await asyncio.sleep(60)

    async def get_city_status(self) -> Dict[str, Any]:
        """Get overall city infrastructure status"""
        return {
            'devices_online': sum(1 for d in self.devices.values() if d.status == 'online'),
            'total_devices': len(self.devices),
            'active_services': len([s for s in self.city_services.values()
                                  if s.service_id in self.mqtt_clients and
                                  self.mqtt_clients[s.service_id].connected]),
            'total_services': len(self.city_services),
            'stats': self.stats.copy()
        }

    async def broadcast_emergency_alert(self, alert_type: str, message: str,
                                      location: Tuple[float, float] = None,
                                      radius: float = None):
        """Broadcast emergency alert through city systems"""
        try:
            alert_data = {
                'type': alert_type,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'source': 'mesh_bridge'
            }

            if location:
                alert_data['location'] = {'lat': location[0], 'lon': location[1]}
            if radius:
                alert_data['radius'] = radius

            # Send to emergency service
            if 'emergency_broadcast' in self.city_services:
                service = self.city_services['emergency_broadcast']
                if service.service_id in self.mqtt_clients:
                    client = self.mqtt_clients[service.service_id]
                    topic = "alerts/emergency"
                    await client.publish(topic, alert_data, qos=2, retain=True)

            # Also broadcast through mesh network
            mesh_alert = {
                'type': 'emergency_alert',
                'data': alert_data,
                'priority': 'high'
            }
            await self.mesh_router.broadcast_message(mesh_alert)

            logger.info(f"Emergency alert broadcasted: {alert_type}")

        except Exception as e:
            logger.error(f"Error broadcasting emergency alert: {e}")

    async def request_traffic_control(self, intersection_id: str, action: str,
                                    duration: int = 30):
        """Request traffic light control"""
        try:
            command = ControlCommand(
                command_id=f"traffic_{intersection_id}_{datetime.now().timestamp()}",
                device_id='traffic_lights',
                action=action,  # 'green', 'red', 'yellow', 'emergency'
                parameters={'duration': duration, 'intersection': intersection_id},
                priority=7,
                timeout=10,
                source='mesh_bridge'
            )

            await self.send_control_command(command)
            logger.info(f"Traffic control requested for {intersection_id}: {action}")

        except Exception as e:
            logger.error(f"Error requesting traffic control: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get bridge statistics"""
        return {
            **self.stats,
            'devices': len(self.devices),
            'services': len(self.city_services),
            'mqtt_clients': len(self.mqtt_clients),
            'coap_clients': len(self.coap_clients)
        }

# Integration functions
async def create_city_mesh_bridge(mesh_router: MeshRouter) -> CityMeshBridge:
    """Factory function to create and initialize city mesh bridge"""
    bridge = CityMeshBridge(mesh_router)
    await bridge.initialize()
    return bridge

# Example usage and testing
async def test_city_mesh_bridge():
    """Test the city mesh bridge"""
    # This would require a mock mesh router
    # For now, just test basic functionality
    print("City Mesh Bridge test placeholder - requires mesh router integration")

if __name__ == "__main__":
    asyncio.run(test_city_mesh_bridge())
