"""
Yandex Offline Cache System

Provides offline caching capabilities for Yandex Maps and related services:
- Map tiles caching with intelligent prefetching
- Geocoding results caching
- Transport data caching
- Route caching with offline routing
- Cache management and synchronization

This module enables offline operation by storing frequently accessed
Yandex data locally and providing fallback mechanisms.
"""

import asyncio
import sqlite3
import json
import logging
import os
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import hashlib
import gzip
import shutil
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor

from .yandex_connector import YandexConnector, YandexCredentials, RoutePoint, TransportInfo

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry metadata"""
    key: str
    service: str
    endpoint: str
    params_hash: str
    data: bytes
    compressed: bool
    timestamp: datetime
    expires: datetime
    access_count: int
    size_bytes: int

@dataclass
class MapTileCache:
    """Map tile cache entry"""
    x: int
    y: int
    z: int
    data: bytes
    format: str  # 'png', 'jpg', etc.
    timestamp: datetime
    expires: datetime

@dataclass
class GeocodeCache:
    """Geocoding cache entry"""
    query: str
    bounds: Optional[Tuple[float, float, float, float]]
    results: List[RoutePoint]
    timestamp: datetime
    expires: datetime

@dataclass
class RouteCache:
    """Route cache entry"""
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    transport_type: str
    route_data: Dict[str, Any]
    timestamp: datetime
    expires: datetime

class YandexCacheError(Exception):
    """Custom exception for cache operations"""
    pass

class YandexOfflineCache:
    """
    Offline cache system for Yandex services

    Provides persistent storage and intelligent caching strategies
    for offline operation of Yandex Maps and services.
    """

    def __init__(self, cache_dir: str = "./cache/yandex",
                 max_size_mb: int = 500,
                 default_ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.default_ttl = timedelta(hours=default_ttl_hours)

        # Database for metadata
        self.db_path = self.cache_dir / "cache.db"
        self.db_lock = threading.Lock()

        # Thread pool for compression/decompression
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'size_bytes': 0,
            'entries': 0
        }

        # Initialize cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for cache metadata"""
        with self.db_lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS cache_entries (
                        key TEXT PRIMARY KEY,
                        service TEXT NOT NULL,
                        endpoint TEXT NOT NULL,
                        params_hash TEXT NOT NULL,
                        compressed INTEGER NOT NULL,
                        timestamp TEXT NOT NULL,
                        expires TEXT NOT NULL,
                        access_count INTEGER DEFAULT 0,
                        size_bytes INTEGER NOT NULL,
                        data_path TEXT NOT NULL
                    )
                ''')

                # Create indexes for performance
                conn.execute('CREATE INDEX IF NOT EXISTS idx_service ON cache_entries(service)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_expires ON cache_entries(expires)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_access_count ON cache_entries(access_count)')

                # Map tiles table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS map_tiles (
                        x INTEGER NOT NULL,
                        y INTEGER NOT NULL,
                        z INTEGER NOT NULL,
                        format TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        expires TEXT NOT NULL,
                        data_path TEXT NOT NULL,
                        PRIMARY KEY (x, y, z)
                    )
                ''')

                # Geocoding table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS geocode_cache (
                        query TEXT NOT NULL,
                        bounds TEXT,
                        results TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        expires TEXT NOT NULL,
                        PRIMARY KEY (query, bounds)
                    )
                ''')

                # Routes table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS route_cache (
                        start_lat REAL NOT NULL,
                        start_lon REAL NOT NULL,
                        end_lat REAL NOT NULL,
                        end_lon REAL NOT NULL,
                        transport_type TEXT NOT NULL,
                        route_data TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        expires TEXT NOT NULL,
                        PRIMARY KEY (start_lat, start_lon, end_lat, end_lon, transport_type)
                    )
                ''')

                conn.commit()
                logger.info("Cache database initialized")

            finally:
                conn.close()

    def _get_data_path(self, key: str) -> Path:
        """Get file path for cache data"""
        # Use hash-based directory structure to avoid too many files in one directory
        hash_obj = hashlib.md5(key.encode())
        hash_str = hash_obj.hexdigest()
        dir_name = hash_str[:2]
        file_name = hash_str[2:]

        data_dir = self.cache_dir / "data" / dir_name
        data_dir.mkdir(parents=True, exist_ok=True)

        return data_dir / file_name

    async def _compress_data(self, data: bytes) -> bytes:
        """Compress data using gzip"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, gzip.compress, data)

    async def _decompress_data(self, data: bytes) -> bytes:
        """Decompress gzip data"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, gzip.decompress, data)

    def _calculate_size(self) -> int:
        """Calculate total cache size"""
        total_size = 0
        try:
            for file_path in self.cache_dir.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except OSError as e:
            logger.error(f"Error calculating cache size: {e}")
        return total_size

    async def _evict_old_entries(self, required_space: int = 0):
        """Evict old cache entries to free up space"""
        target_size = self.max_size_bytes - required_space

        with self.db_lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                # Get entries sorted by access count and age
                cursor = conn.execute('''
                    SELECT key, data_path, size_bytes
                    FROM cache_entries
                    ORDER BY access_count ASC, timestamp ASC
                ''')

                entries_to_delete = []
                freed_space = 0

                for key, data_path, size_bytes in cursor.fetchall():
                    if self._calculate_size() <= target_size:
                        break

                    entries_to_delete.append((key, data_path))
                    freed_space += size_bytes

                # Delete entries and files
                for key, data_path in entries_to_delete:
                    conn.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
                    try:
                        Path(data_path).unlink(missing_ok=True)
                    except OSError as e:
                        logger.error(f"Error deleting cache file {data_path}: {e}")

                conn.commit()
                logger.info(f"Evicted {len(entries_to_delete)} cache entries, freed {freed_space} bytes")

            finally:
                conn.close()

    async def store(self, service: str, endpoint: str,
                   params: Dict[str, Any], data: bytes,
                   ttl: Optional[timedelta] = None) -> str:
        """
        Store data in cache

        Args:
            service: Yandex service name
            endpoint: API endpoint
            params: Request parameters
            data: Data to cache
            ttl: Time to live (optional)

        Returns:
            Cache key
        """
        # Generate cache key
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        key = f"{service}:{endpoint}:{params_hash}"

        # Compress data if beneficial
        should_compress = len(data) > 1024  # Compress if > 1KB
        if should_compress:
            compressed_data = await self._compress_data(data)
            if len(compressed_data) < len(data):
                data = compressed_data
            else:
                should_compress = False

        # Check if we need to evict old entries
        data_size = len(data)
        if self._calculate_size() + data_size > self.max_size_bytes:
            await self._evict_old_entries(data_size)

        # Store data to file
        data_path = self._get_data_path(key)
        try:
            with open(data_path, 'wb') as f:
                f.write(data)
        except OSError as e:
            raise YandexCacheError(f"Failed to write cache file: {e}")

        # Store metadata
        expires = datetime.now() + (ttl or self.default_ttl)

        with self.db_lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                conn.execute('''
                    INSERT OR REPLACE INTO cache_entries
                    (key, service, endpoint, params_hash, compressed, timestamp, expires, size_bytes, data_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    key, service, endpoint, params_hash, should_compress,
                    datetime.now().isoformat(), expires.isoformat(),
                    data_size, str(data_path)
                ))
                conn.commit()

                self.stats['entries'] += 1
                self.stats['size_bytes'] += data_size

            finally:
                conn.close()

        logger.debug(f"Cached {service}:{endpoint}, key: {key}")
        return key

    async def retrieve(self, service: str, endpoint: str,
                      params: Dict[str, Any]) -> Optional[bytes]:
        """
        Retrieve data from cache

        Args:
            service: Yandex service name
            endpoint: API endpoint
            params: Request parameters

        Returns:
            Cached data or None
        """
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        key = f"{service}:{endpoint}:{params_hash}"

        with self.db_lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.execute('''
                    SELECT compressed, data_path, expires, access_count
                    FROM cache_entries
                    WHERE key = ? AND expires > ?
                ''', (key, datetime.now().isoformat()))

                row = cursor.fetchone()
                if not row:
                    self.stats['misses'] += 1
                    return None

                compressed, data_path, expires, access_count = row

                # Update access count
                conn.execute('''
                    UPDATE cache_entries
                    SET access_count = ?
                    WHERE key = ?
                ''', (access_count + 1, key))
                conn.commit()

            finally:
                conn.close()

        # Read data from file
        try:
            with open(data_path, 'rb') as f:
                data = f.read()
        except OSError as e:
            logger.error(f"Failed to read cache file {data_path}: {e}")
            # Remove corrupted entry
            await self.delete(key)
            self.stats['misses'] += 1
            return None

        # Decompress if necessary
        if compressed:
            try:
                data = await self._decompress_data(data)
            except Exception as e:
                logger.error(f"Failed to decompress cache data: {e}")
                await self.delete(key)
                self.stats['misses'] += 1
                return None

        self.stats['hits'] += 1
        logger.debug(f"Cache hit for {service}:{endpoint}")
        return data

    async def delete(self, key: str):
        """Delete cache entry"""
        with self.db_lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.execute('SELECT data_path, size_bytes FROM cache_entries WHERE key = ?', (key,))
                row = cursor.fetchone()
                if row:
                    data_path, size_bytes = row
                    conn.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
                    conn.commit()

                    # Delete file
                    try:
                        Path(data_path).unlink(missing_ok=True)
                    except OSError as e:
                        logger.error(f"Error deleting cache file {data_path}: {e}")

                    self.stats['entries'] -= 1
                    self.stats['size_bytes'] -= size_bytes

            finally:
                conn.close()

    async def clear_expired(self):
        """Clear expired cache entries"""
        now = datetime.now().isoformat()

        with self.db_lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.execute('''
                    SELECT key, data_path, size_bytes
                    FROM cache_entries
                    WHERE expires <= ?
                ''', (now,))

                expired_entries = cursor.fetchall()

                for key, data_path, size_bytes in expired_entries:
                    conn.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
                    try:
                        Path(data_path).unlink(missing_ok=True)
                    except OSError as e:
                        logger.error(f"Error deleting expired cache file {data_path}: {e}")

                    self.stats['entries'] -= 1
                    self.stats['size_bytes'] -= size_bytes

                conn.commit()
                logger.info(f"Cleared {len(expired_entries)} expired cache entries")

            finally:
                conn.close()

    # Map tiles specific methods
    async def store_map_tile(self, x: int, y: int, z: int,
                           data: bytes, format: str = 'png',
                           ttl: Optional[timedelta] = None):
        """Store map tile in cache"""
        expires = datetime.now() + (ttl or self.default_ttl)

        # Store data to file
        tile_key = f"tile_{z}_{x}_{y}"
        data_path = self._get_data_path(tile_key)

        try:
            with open(data_path, 'wb') as f:
                f.write(data)
        except OSError as e:
            raise YandexCacheError(f"Failed to write tile file: {e}")

        with self.db_lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                conn.execute('''
                    INSERT OR REPLACE INTO map_tiles
                    (x, y, z, format, timestamp, expires, data_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    x, y, z, format,
                    datetime.now().isoformat(),
                    expires.isoformat(),
                    str(data_path)
                ))
                conn.commit()
            finally:
                conn.close()

    async def get_map_tile(self, x: int, y: int, z: int) -> Optional[bytes]:
        """Retrieve map tile from cache"""
        with self.db_lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.execute('''
                    SELECT data_path, expires FROM map_tiles
                    WHERE x = ? AND y = ? AND z = ? AND expires > ?
                ''', (x, y, z, datetime.now().isoformat()))

                row = cursor.fetchone()
                if not row:
                    return None

                data_path, expires = row

            finally:
                conn.close()

        try:
            with open(data_path, 'rb') as f:
                return f.read()
        except OSError:
            return None

    async def prefetch_map_tiles(self, center_lat: float, center_lon: float,
                               zoom: int, radius: int = 2,
                               connector: Optional[YandexConnector] = None):
        """
        Prefetch map tiles around a center point

        Args:
            center_lat, center_lon: Center coordinates
            zoom: Zoom level
            radius: Radius in tiles to prefetch
            connector: Yandex connector for fetching tiles
        """
        if not connector:
            logger.warning("No connector provided for tile prefetching")
            return

        # Convert lat/lon to tile coordinates
        # This is a simplified conversion - real implementation would use proper formulas
        center_x = int((center_lon + 180) / 360 * (1 << zoom))
        center_y = int((1 - math.log(math.tan(math.radians(center_lat)) + 1 / math.cos(math.radians(center_lat))) / math.pi) / 2 * (1 << zoom))

        tasks = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                x, y = center_x + dx, center_y + dy
                if 0 <= x < (1 << zoom) and 0 <= y < (1 << zoom):
                    tasks.append(self._prefetch_single_tile(x, y, zoom, connector))

        await asyncio.gather(*tasks, return_exceptions=True)

    async def _prefetch_single_tile(self, x: int, y: int, z: int, connector: YandexConnector):
        """Prefetch a single map tile"""
        # Check if already cached
        if await self.get_map_tile(x, y, z):
            return

        try:
            # This would call the actual Yandex Maps API to get tile data
            # Placeholder implementation
            tile_data = b"placeholder_tile_data"
            await self.store_map_tile(x, y, z, tile_data)
        except Exception as e:
            logger.error(f"Failed to prefetch tile {z}/{x}/{y}: {e}")

    # Geocoding cache methods
    async def store_geocode(self, query: str, bounds: Optional[Tuple[float, float, float, float]],
                          results: List[RoutePoint], ttl: Optional[timedelta] = None):
        """Store geocoding results"""
        expires = datetime.now() + (ttl or self.default_ttl)
        results_json = json.dumps([asdict(point) for point in results])

        bounds_str = f"{bounds[0]},{bounds[1]},{bounds[2]},{bounds[3]}" if bounds else None

        with self.db_lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                conn.execute('''
                    INSERT OR REPLACE INTO geocode_cache
                    (query, bounds, results, timestamp, expires)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    query, bounds_str, results_json,
                    datetime.now().isoformat(), expires.isoformat()
                ))
                conn.commit()
            finally:
                conn.close()

    async def get_geocode(self, query: str, bounds: Optional[Tuple[float, float, float, float]]) -> Optional[List[RoutePoint]]:
        """Retrieve geocoding results"""
        bounds_str = f"{bounds[0]},{bounds[1]},{bounds[2]},{bounds[3]}" if bounds else None

        with self.db_lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.execute('''
                    SELECT results, expires FROM geocode_cache
                    WHERE query = ? AND bounds IS ? AND expires > ?
                ''', (query, bounds_str, datetime.now().isoformat()))

                row = cursor.fetchone()
                if not row:
                    return None

                results_json, expires = row

            finally:
                conn.close()

        try:
            results_data = json.loads(results_json)
            return [RoutePoint(**point) for point in results_data]
        except (json.JSONDecodeError, KeyError):
            return None

    # Route cache methods
    async def store_route(self, start_lat: float, start_lon: float,
                        end_lat: float, end_lon: float, transport_type: str,
                        route_data: Dict[str, Any], ttl: Optional[timedelta] = None):
        """Store route data"""
        expires = datetime.now() + (ttl or self.default_ttl)
        route_json = json.dumps(route_data)

        with self.db_lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                conn.execute('''
                    INSERT OR REPLACE INTO route_cache
                    (start_lat, start_lon, end_lat, end_lon, transport_type, route_data, timestamp, expires)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    start_lat, start_lon, end_lat, end_lon, transport_type,
                    route_json, datetime.now().isoformat(), expires.isoformat()
                ))
                conn.commit()
            finally:
                conn.close()

    async def get_route(self, start_lat: float, start_lon: float,
                       end_lat: float, end_lon: float, transport_type: str) -> Optional[Dict[str, Any]]:
        """Retrieve route data"""
        with self.db_lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.execute('''
                    SELECT route_data, expires FROM route_cache
                    WHERE start_lat = ? AND start_lon = ? AND end_lat = ? AND end_lon = ? AND transport_type = ? AND expires > ?
                ''', (start_lat, start_lon, end_lat, end_lon, transport_type, datetime.now().isoformat()))

                row = cursor.fetchone()
                if not row:
                    return None

                route_json, expires = row

            finally:
                conn.close()

        try:
            return json.loads(route_json)
        except json.JSONDecodeError:
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        hit_rate = 0
        if self.stats['hits'] + self.stats['misses'] > 0:
            hit_rate = self.stats['hits'] / (self.stats['hits'] + self.stats['misses'])

        return {
            **self.stats,
            'hit_rate': hit_rate,
            'max_size_mb': self.max_size_bytes / (1024 * 1024),
            'current_size_mb': self._calculate_size() / (1024 * 1024)
        }

    async def cleanup(self):
        """Clean up expired entries and optimize cache"""
        await self.clear_expired()

        # Reclaim space if over limit
        current_size = self._calculate_size()
        if current_size > self.max_size_bytes:
            await self._evict_old_entries()

    async def clear_all(self):
        """Clear all cache data"""
        # Close database connection first
        with self.db_lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                # Drop all tables
                conn.execute('DROP TABLE IF EXISTS cache_entries')
                conn.execute('DROP TABLE IF EXISTS map_tiles')
                conn.execute('DROP TABLE IF EXISTS geocode_cache')
                conn.execute('DROP TABLE IF EXISTS route_cache')
                conn.commit()
            finally:
                conn.close()

        # Remove all files
        try:
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Error clearing cache directory: {e}")

        # Reinitialize
        self._init_database()
        self.stats = {'hits': 0, 'misses': 0, 'size_bytes': 0, 'entries': 0}

        logger.info("Cache cleared completely")

# Integration with YandexConnector
class CachedYandexConnector:
    """
    Yandex connector with offline caching capabilities

    Wraps YandexConnector and adds caching layer for offline operation.
    """

    def __init__(self, credentials: YandexCredentials, cache_dir: str = "./cache/yandex"):
        self.connector = YandexConnector(credentials)
        self.cache = YandexOfflineCache(cache_dir)

    async def __aenter__(self):
        await self.connector.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.connector.__aexit__(exc_type, exc_val, exc_tb)

    async def get_cached_or_fetch(self, service: str, endpoint: str,
                                params: Dict[str, Any] = None,
                                use_cache: bool = True) -> Dict[str, Any]:
        """
        Get data from cache or fetch from API

        Args:
            service: Yandex service name
            endpoint: API endpoint
            params: Request parameters
            use_cache: Whether to use cache

        Returns:
            API response data
        """
        if not use_cache:
            return await self.connector._make_request(service, endpoint, params)

        # Try cache first
        cached_data = await self.cache.retrieve(service, endpoint, params or {})
        if cached_data:
            try:
                return json.loads(cached_data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                logger.warning("Failed to decode cached data, fetching from API")

        # Fetch from API
        try:
            data = await self.connector._make_request(service, endpoint, params)
            # Cache the result
            data_bytes = json.dumps(data).encode('utf-8')
            await self.cache.store(service, endpoint, params or {}, data_bytes)
            return data
        except Exception as e:
            # If API fails and we have cached data (even if expired), use it
            if cached_data:
                try:
                    logger.warning(f"API failed, using expired cached data: {e}")
                    return json.loads(cached_data.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass
            raise

# Example usage
async def test_yandex_cache():
    """Test the offline cache system"""
    cache = YandexOfflineCache()

    # Test basic caching
    test_data = b"Hello, World!"
    key = await cache.store("test", "endpoint", {"param": "value"}, test_data)

    retrieved = await cache.retrieve("test", "endpoint", {"param": "value"})
    assert retrieved == test_data, "Cache retrieval failed"

    # Test geocoding cache
    from .yandex_connector import RoutePoint
    points = [RoutePoint(55.7558, 37.6176, "Moscow, Red Square")]
    await cache.store_geocode("Moscow", None, points)

    cached_points = await cache.get_geocode("Moscow", None)
    assert cached_points is not None and len(cached_points) == 1

    print("Yandex cache tests passed")

if __name__ == "__main__":
    import math  # For tile calculations
    asyncio.run(test_yandex_cache())
