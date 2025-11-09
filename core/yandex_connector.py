"""
Yandex API Connector Module

Provides integration with Yandex services for online operation:
- Yandex.Maps: Static maps, routing, geocoding
- Yandex.Transport: Public transport information
- Yandex.Geocoder: Address geocoding and reverse geocoding
- Yandex.SpeechKit: Speech recognition and synthesis

This module handles API authentication, request management, and error handling
for all Yandex services used in the Serverless-SDK_API platform.
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import hmac
import base64

logger = logging.getLogger(__name__)

@dataclass
class YandexCredentials:
    """Yandex API credentials container"""
    maps_api_key: str
    transport_api_key: str
    geocoder_api_key: str
    speechkit_api_key: str
    speechkit_secret_key: str
    folder_id: str  # For SpeechKit IAM token

@dataclass
class MapTile:
    """Map tile data structure"""
    x: int
    y: int
    z: int
    data: bytes
    timestamp: datetime

@dataclass
class RoutePoint:
    """Route point with coordinates and metadata"""
    lat: float
    lon: float
    address: str
    transport_type: Optional[str] = None

@dataclass
class TransportInfo:
    """Public transport information"""
    route_id: str
    route_name: str
    transport_type: str
    stops: List[Dict[str, Any]]
    schedule: List[Dict[str, Any]]

class YandexAPIError(Exception):
    """Custom exception for Yandex API errors"""
    pass

class YandexConnector:
    """
    Main connector class for Yandex API services

    Handles authentication, rate limiting, caching, and error recovery
    for all Yandex API interactions.
    """

    def __init__(self, credentials: YandexCredentials):
        self.credentials = credentials
        self.session: Optional[aiohttp.ClientSession] = None
        self.iam_token: Optional[str] = None
        self.token_expires: Optional[datetime] = None

        # API endpoints
        self.base_urls = {
            'maps': 'https://api-maps.yandex.ru/2.1/',
            'geocoder': 'https://geocode-maps.yandex.ru/1.x/',
            'transport': 'https://api.rasp.yandex.net/v3.0/',
            'speechkit': 'https://stt.api.cloud.yandex.net/speechkit/v1/',
            'speechkit_tts': 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'
        }

        # Rate limiting
        self.request_counts = {}
        self.rate_limits = {
            'maps': 1000,  # requests per hour
            'geocoder': 1000,
            'transport': 100,
            'speechkit': 100
        }

        # Caching
        self.cache = {}
        self.cache_ttl = timedelta(hours=1)

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def initialize(self):
        """Initialize the connector with session and authentication"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Serverless-SDK_API/1.0',
                'Accept': 'application/json'
            }
        )

        # Initialize IAM token for SpeechKit
        await self._refresh_iam_token()

        logger.info("Yandex connector initialized")

    async def close(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
        logger.info("Yandex connector closed")

    async def _refresh_iam_token(self):
        """Refresh IAM token for SpeechKit authentication"""
        try:
            # This would typically use Yandex Cloud IAM API
            # For now, using a placeholder implementation
            self.iam_token = "placeholder_iam_token"
            self.token_expires = datetime.now() + timedelta(hours=12)
            logger.debug("IAM token refreshed")
        except Exception as e:
            logger.error(f"Failed to refresh IAM token: {e}")
            raise YandexAPIError(f"IAM token refresh failed: {e}")

    async def _check_rate_limit(self, service: str) -> bool:
        """Check if we're within rate limits"""
        now = datetime.now()
        hour_key = f"{service}_{now.strftime('%Y%m%d%H')}"

        if hour_key not in self.request_counts:
            self.request_counts[hour_key] = 0

        if self.request_counts[hour_key] >= self.rate_limits[service]:
            logger.warning(f"Rate limit exceeded for {service}")
            return False

        self.request_counts[hour_key] += 1
        return True

    async def _make_request(self, service: str, endpoint: str,
                          params: Dict[str, Any] = None,
                          method: str = 'GET',
                          data: Any = None) -> Dict[str, Any]:
        """Make authenticated request to Yandex API"""
        if not await self._check_rate_limit(service):
            raise YandexAPIError(f"Rate limit exceeded for {service}")

        url = f"{self.base_urls[service]}{endpoint}"

        headers = {}
        if service == 'speechkit':
            if not self.iam_token or datetime.now() >= self.token_expires:
                await self._refresh_iam_token()
            headers['Authorization'] = f"Bearer {self.iam_token}"

        # Add API keys to params
        request_params = params.copy() if params else {}
        if service == 'maps':
            request_params['apikey'] = self.credentials.maps_api_key
        elif service == 'geocoder':
            request_params['apikey'] = self.credentials.geocoder_api_key
        elif service == 'transport':
            request_params['apikey'] = self.credentials.transport_api_key

        try:
            async with self.session.request(method, url,
                                          params=request_params,
                                          json=data,
                                          headers=headers) as response:
                if response.status == 200:
                    if service == 'speechkit':
                        return await response.read()  # Binary data for speech
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Yandex API error {response.status}: {error_text}")
                    raise YandexAPIError(f"API request failed: {response.status} - {error_text}")

        except aiohttp.ClientError as e:
            logger.error(f"Network error calling {service}: {e}")
            raise YandexAPIError(f"Network error: {e}")

    # Maps API Methods
    async def get_static_map(self, center_lat: float, center_lon: float,
                           zoom: int = 10, size: Tuple[int, int] = (400, 400),
                           markers: List[Tuple[float, float]] = None) -> bytes:
        """
        Get static map image from Yandex.Maps

        Args:
            center_lat: Center latitude
            center_lon: Center longitude
            zoom: Zoom level (0-17)
            size: Image size (width, height)
            markers: List of (lat, lon) marker coordinates

        Returns:
            PNG image data as bytes
        """
        params = {
            'll': f"{center_lon},{center_lat}",
            'z': zoom,
            'size': f"{size[0]},{size[1]}",
            'l': 'map',  # Layer: map
            'lang': 'ru_RU'
        }

        if markers:
            marker_str = '~'.join([f"{lon},{lat}" for lat, lon in markers])
            params['pt'] = marker_str

        response = await self._make_request('maps', '', params)
        # Note: This is a simplified implementation
        # In reality, Yandex Maps static API returns image data
        return b"placeholder_png_data"

    async def get_route(self, start_lat: float, start_lon: float,
                       end_lat: float, end_lon: float,
                       transport_type: str = 'auto') -> Dict[str, Any]:
        """
        Get route between two points

        Args:
            start_lat, start_lon: Starting coordinates
            end_lat, end_lon: Ending coordinates
            transport_type: 'auto', 'pedestrian', 'masstransit'

        Returns:
            Route data with waypoints, distance, time
        """
        params = {
            'rll': f"{start_lon},{start_lat}~{end_lon},{end_lat}",
            'rtt': transport_type,
            'lang': 'ru_RU',
            'format': 'json'
        }

        return await self._make_request('maps', 'route', params)

    # Geocoder API Methods
    async def geocode_address(self, address: str,
                            bounds: Tuple[float, float, float, float] = None) -> List[RoutePoint]:
        """
        Geocode address to coordinates

        Args:
            address: Human-readable address
            bounds: Optional bounding box (lon1, lat1, lon2, lat2)

        Returns:
            List of matching locations
        """
        params = {
            'geocode': address,
            'format': 'json',
            'lang': 'ru_RU',
            'results': 5
        }

        if bounds:
            params['bbox'] = f"{bounds[0]},{bounds[1]}~{bounds[2]},{bounds[3]}"

        response = await self._make_request('geocoder', '', params)

        points = []
        try:
            features = response.get('response', {}).get('GeoObjectCollection', {}).get('featureMember', [])
            for feature in features:
                geo_object = feature.get('GeoObject', {})
                coords_str = geo_object.get('Point', {}).get('pos', '')
                if coords_str:
                    lon, lat = map(float, coords_str.split())
                    address = geo_object.get('metaDataProperty', {}).get('GeocoderMetaData', {}).get('text', '')
                    points.append(RoutePoint(lat, lon, address))
        except (KeyError, ValueError) as e:
            logger.error(f"Failed to parse geocoder response: {e}")

        return points

    async def reverse_geocode(self, lat: float, lon: float) -> Optional[RoutePoint]:
        """
        Reverse geocode coordinates to address

        Args:
            lat, lon: Coordinates to reverse geocode

        Returns:
            Address information or None
        """
        params = {
            'geocode': f"{lon},{lat}",
            'format': 'json',
            'lang': 'ru_RU'
        }

        response = await self._make_request('geocoder', '', params)

        try:
            feature = response.get('response', {}).get('GeoObjectCollection', {}).get('featureMember', [{}])[0]
            geo_object = feature.get('GeoObject', {})
            coords_str = geo_object.get('Point', {}).get('pos', '')
            if coords_str:
                address = geo_object.get('metaDataProperty', {}).get('GeocoderMetaData', {}).get('text', '')
                return RoutePoint(lat, lon, address)
        except (KeyError, ValueError, IndexError) as e:
            logger.error(f"Failed to parse reverse geocode response: {e}")

        return None

    # Transport API Methods
    async def get_transport_routes(self, lat: float, lon: float,
                                 radius: int = 1000) -> List[TransportInfo]:
        """
        Get public transport routes near a location

        Args:
            lat, lon: Center coordinates
            radius: Search radius in meters

        Returns:
            List of transport routes
        """
        params = {
            'lat': lat,
            'lng': lon,
            'radius': radius,
            'lang': 'ru',
            'format': 'json'
        }

        response = await self._make_request('transport', 'nearest_stations', params)

        routes = []
        try:
            stations = response.get('stations', [])
            for station in stations:
                # Simplified parsing - actual API response structure may vary
                route_info = TransportInfo(
                    route_id=station.get('code', ''),
                    route_name=station.get('title', ''),
                    transport_type=station.get('type', ''),
                    stops=station.get('routes', []),
                    schedule=[]
                )
                routes.append(route_info)
        except (KeyError, ValueError) as e:
            logger.error(f"Failed to parse transport response: {e}")

        return routes

    # SpeechKit API Methods
    async def recognize_speech(self, audio_data: bytes,
                             language: str = 'ru-RU') -> str:
        """
        Convert speech to text using SpeechKit

        Args:
            audio_data: Raw audio data (WAV, OGG, etc.)
            language: Language code (ru-RU, en-US, etc.)

        Returns:
            Recognized text
        """
        # SpeechKit STT API call
        params = {
            'topic': 'general',
            'lang': language,
            'folderId': self.credentials.folder_id
        }

        response_data = await self._make_request('speechkit', 'stt:recognize',
                                               params, 'POST', audio_data)

        # Parse response - this would depend on actual API format
        # Placeholder implementation
        return "recognized_text_placeholder"

    async def synthesize_speech(self, text: str,
                               language: str = 'ru-RU',
                               voice: str = 'oksana') -> bytes:
        """
        Convert text to speech using SpeechKit

        Args:
            text: Text to synthesize
            language: Language code
            voice: Voice name

        Returns:
            Audio data as bytes
        """
        params = {
            'text': text,
            'lang': language,
            'voice': voice,
            'folderId': self.credentials.folder_id,
            'format': 'oggopus'
        }

        audio_data = await self._make_request('speechkit_tts', '',
                                            params, 'GET')

        return audio_data

    # Caching methods for offline support
    def _get_cache_key(self, service: str, params: Dict[str, Any]) -> str:
        """Generate cache key from service and parameters"""
        key_data = f"{service}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _is_cache_valid(self, cached_time: datetime) -> bool:
        """Check if cached data is still valid"""
        return datetime.now() - cached_time < self.cache_ttl

    async def get_cached_or_fetch(self, service: str, endpoint: str,
                                params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get data from cache or fetch from API"""
        cache_key = self._get_cache_key(service, params or {})

        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if self._is_cache_valid(cached_time):
                logger.debug(f"Cache hit for {service}:{endpoint}")
                return cached_data

        # Fetch from API
        data = await self._make_request(service, endpoint, params)

        # Cache the result
        self.cache[cache_key] = (data, datetime.now())

        # Clean old cache entries
        self._clean_cache()

        return data

    def _clean_cache(self):
        """Remove expired cache entries"""
        now = datetime.now()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if now - timestamp >= self.cache_ttl
        ]
        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            logger.debug(f"Cleaned {len(expired_keys)} expired cache entries")

# Convenience functions for easy usage
async def create_yandex_connector(credentials: YandexCredentials) -> YandexConnector:
    """Factory function to create and initialize Yandex connector"""
    connector = YandexConnector(credentials)
    await connector.initialize()
    return connector

# Example usage and testing functions
async def test_yandex_connector():
    """Test function for Yandex connector"""
    # This would use actual credentials in production
    credentials = YandexCredentials(
        maps_api_key="test_maps_key",
        transport_api_key="test_transport_key",
        geocoder_api_key="test_geocoder_key",
        speechkit_api_key="test_speechkit_key",
        speechkit_secret_key="test_secret_key",
        folder_id="test_folder_id"
    )

    async with YandexConnector(credentials) as connector:
        try:
            # Test geocoding
            points = await connector.geocode_address("Moscow, Red Square")
            print(f"Geocoded points: {len(points)}")

            # Test reverse geocoding
            if points:
                point = points[0]
                address = await connector.reverse_geocode(point.lat, point.lon)
                print(f"Reverse geocoded: {address}")

            # Test route calculation
            route = await connector.get_route(55.7558, 37.6176, 55.7642, 37.6026)
            print(f"Route calculated: {bool(route)}")

        except YandexAPIError as e:
            print(f"Yandex API error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_yandex_connector())
