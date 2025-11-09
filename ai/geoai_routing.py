"""
GeoAI Routing Module

AI-powered route prediction and optimization using Yandex data and mesh networks:
- Machine learning models for route prediction
- Real-time traffic integration from Yandex.Transport
- Mesh network topology awareness
- Multi-modal routing (car, pedestrian, public transport)
- Predictive analytics for route optimization
- Offline route calculation with cached data

This module provides intelligent routing capabilities that combine
traditional navigation with AI-driven predictions and mesh network awareness.
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import math
import heapq
from collections import defaultdict
import pickle
import os
from pathlib import Path

# Import dependencies
from ..core.yandex_connector import YandexConnector, RoutePoint, TransportInfo
from ..core.yandex_cache import YandexOfflineCache
from ..mesh.routing import MeshRouter, Route as MeshRoute

logger = logging.getLogger(__name__)

@dataclass
class RouteSegment:
    """Route segment with detailed information"""
    start_point: Tuple[float, float]
    end_point: Tuple[float, float]
    distance_meters: float
    duration_seconds: int
    transport_mode: str  # 'car', 'pedestrian', 'public_transport', 'mesh'
    instructions: str
    traffic_level: int  # 0-10, higher means more traffic
    mesh_nodes: List[str] = field(default_factory=list)  # Mesh nodes along route

@dataclass
class Route:
    """Complete route with multiple segments"""
    route_id: str
    segments: List[RouteSegment]
    total_distance: float
    total_duration: int
    confidence_score: float  # 0.0-1.0
    predicted_traffic: Dict[str, int]
    mesh_coverage: float  # Percentage of route covered by mesh
    alternatives: List['Route'] = field(default_factory=list)

@dataclass
class TrafficPrediction:
    """Traffic prediction data"""
    segment_id: str
    timestamp: datetime
    predicted_level: int
    confidence: float
    factors: Dict[str, Any]  # Contributing factors

@dataclass
class RoutingContext:
    """Context for routing decisions"""
    start_location: Tuple[float, float]
    end_location: Tuple[float, float]
    departure_time: datetime
    preferences: Dict[str, Any]  # user preferences
    constraints: Dict[str, Any]  # routing constraints
    available_modes: Set[str]  # available transport modes

class GeoAIRoutingError(Exception):
    """Custom exception for GeoAI routing"""
    pass

class TrafficPredictor:
    """
    Machine learning model for traffic prediction

    Uses historical data and real-time information to predict
    traffic conditions along routes.
    """

    def __init__(self, model_path: str = "./models/traffic_predictor.pkl"):
        self.model_path = Path(model_path)
        self.model = None
        self.is_trained = False

        # Feature engineering
        self.feature_columns = [
            'hour_of_day', 'day_of_week', 'month', 'is_weekend',
            'is_rush_hour', 'temperature', 'precipitation',
            'historical_avg_traffic', 'current_traffic', 'trend'
        ]

        self._load_or_create_model()

    def _load_or_create_model(self):
        """Load existing model or create new one"""
        if self.model_path.exists():
            try:
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                self.is_trained = True
                logger.info("Loaded existing traffic prediction model")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                self._create_new_model()
        else:
            self._create_new_model()

    def _create_new_model(self):
        """Create new traffic prediction model"""
        # Simple linear model as placeholder
        # In production, this would be a more sophisticated ML model
        self.model = {
            'weights': np.random.randn(len(self.feature_columns)),
            'bias': 0.0,
            'feature_means': np.zeros(len(self.feature_columns)),
            'feature_stds': np.ones(len(self.feature_columns))
        }
        self.is_trained = False
        logger.info("Created new traffic prediction model")

    def _extract_features(self, segment_id: str, timestamp: datetime,
                         weather_data: Dict[str, Any] = None,
                         historical_data: List[int] = None) -> np.ndarray:
        """Extract features for prediction"""
        features = []

        # Time-based features
        features.append(timestamp.hour)
        features.append(timestamp.weekday())
        features.append(timestamp.month)
        features.append(1 if timestamp.weekday() >= 5 else 0)  # is_weekend
        features.append(1 if (timestamp.hour >= 7 and timestamp.hour <= 9) or
                       (timestamp.hour >= 17 and timestamp.hour <= 19) else 0)  # rush_hour

        # Weather features (placeholders)
        features.append(weather_data.get('temperature', 20) if weather_data else 20)
        features.append(weather_data.get('precipitation', 0) if weather_data else 0)

        # Historical data
        if historical_data:
            features.append(np.mean(historical_data))
        else:
            features.append(5)  # default average traffic

        # Current traffic (placeholder)
        features.append(5)

        # Trend (placeholder)
        features.append(0)

        return np.array(features)

    def predict_traffic(self, segment_id: str, timestamp: datetime,
                       weather_data: Dict[str, Any] = None,
                       historical_data: List[int] = None) -> TrafficPrediction:
        """Predict traffic level for a route segment"""
        try:
            features = self._extract_features(segment_id, timestamp, weather_data, historical_data)

            if not self.is_trained:
                # Return baseline prediction
                predicted_level = min(10, max(0, int(np.random.normal(5, 2))))
                confidence = 0.5
            else:
                # Normalize features
                features_norm = (features - self.model['feature_means']) / self.model['feature_stds']

                # Make prediction
                score = np.dot(features_norm, self.model['weights']) + self.model['bias']
                predicted_level = min(10, max(0, int(score)))
                confidence = 0.8  # Placeholder confidence

            return TrafficPrediction(
                segment_id=segment_id,
                timestamp=timestamp,
                predicted_level=predicted_level,
                confidence=confidence,
                factors={
                    'time_of_day': timestamp.hour,
                    'day_of_week': timestamp.weekday(),
                    'weather_impact': weather_data.get('precipitation', 0) if weather_data else 0
                }
            )

        except Exception as e:
            logger.error(f"Traffic prediction failed: {e}")
            # Return safe default
            return TrafficPrediction(
                segment_id=segment_id,
                timestamp=timestamp,
                predicted_level=5,
                confidence=0.0,
                factors={'error': str(e)}
            )

    def update_model(self, segment_id: str, actual_traffic: int,
                    timestamp: datetime, features: Dict[str, Any]):
        """Update model with new training data"""
        # This would implement online learning
        # For now, just log the update
        logger.debug(f"Model update: {segment_id} = {actual_traffic} at {timestamp}")

class RouteOptimizer:
    """
    AI-powered route optimization engine

    Combines multiple routing algorithms with machine learning
    to find optimal routes considering traffic, mesh coverage, and user preferences.
    """

    def __init__(self, traffic_predictor: TrafficPredictor,
                 yandex_connector: Optional[YandexConnector] = None,
                 cache: Optional[YandexOfflineCache] = None):
        self.traffic_predictor = traffic_predictor
        self.yandex_connector = yandex_connector
        self.cache = cache

        # Routing algorithms
        self.algorithms = {
            'dijkstra': self._dijkstra_routing,
            'a_star': self._a_star_routing,
            'mesh_aware': self._mesh_aware_routing
        }

        # Cost functions for different modes
        self.cost_functions = {
            'car': self._car_cost_function,
            'pedestrian': self._pedestrian_cost_function,
            'public_transport': self._public_transport_cost_function,
            'mesh': self._mesh_cost_function
        }

    def _car_cost_function(self, segment: RouteSegment, context: RoutingContext) -> float:
        """Cost function for car routing"""
        base_cost = segment.distance_meters

        # Traffic multiplier (higher traffic = higher cost)
        traffic_multiplier = 1 + (segment.traffic_level / 10) * 0.5

        # Time preference
        if context.preferences.get('prefer_fastest', False):
            time_weight = 2.0
        else:
            time_weight = 1.0

        # Mesh coverage bonus (prefer mesh-covered routes)
        mesh_bonus = 1 - (len(segment.mesh_nodes) / max(1, segment.distance_meters / 1000)) * 0.1

        return base_cost * traffic_multiplier * time_weight * mesh_bonus

    def _pedestrian_cost_function(self, segment: RouteSegment, context: RoutingContext) -> float:
        """Cost function for pedestrian routing"""
        # Pedestrians prefer shorter distances and avoid high-traffic areas
        base_cost = segment.distance_meters

        # Traffic avoidance for pedestrians
        traffic_penalty = (segment.traffic_level / 10) * 0.3

        # Prefer routes with mesh coverage for safety
        mesh_bonus = 1 - (len(segment.mesh_nodes) / max(1, segment.distance_meters / 100)) * 0.2

        return base_cost * (1 + traffic_penalty) * mesh_bonus

    def _public_transport_cost_function(self, segment: RouteSegment, context: RoutingContext) -> float:
        """Cost function for public transport routing"""
        # Public transport considers waiting time + travel time
        base_cost = segment.duration_seconds

        # Mesh integration bonus (real-time updates via mesh)
        mesh_bonus = 0.9 if segment.mesh_nodes else 1.0

        return base_cost * mesh_bonus

    def _mesh_cost_function(self, segment: RouteSegment, context: RoutingContext) -> float:
        """Cost function for mesh network routing"""
        # Mesh routing prioritizes network efficiency
        base_cost = segment.distance_meters

        # Node density bonus
        node_density = len(segment.mesh_nodes) / max(1, segment.distance_meters / 100)
        density_bonus = max(0.5, 1 - node_density * 0.1)

        return base_cost * density_bonus

    def _dijkstra_routing(self, start: Tuple[float, float], end: Tuple[float, float],
                         context: RoutingContext) -> List[RouteSegment]:
        """Classic Dijkstra routing algorithm"""
        # Simplified implementation - in production would use road network graph
        # This is a placeholder that creates a simple route

        distance = self._haversine_distance(start, end)
        duration = int(distance / 50 * 3600)  # Assume 50 km/h average speed

        segment = RouteSegment(
            start_point=start,
            end_point=end,
            distance_meters=distance,
            duration_seconds=duration,
            transport_mode='car',
            instructions=f"Drive {distance:.0f} meters to destination",
            traffic_level=5
        )

        return [segment]

    def _a_star_routing(self, start: Tuple[float, float], end: Tuple[float, float],
                       context: RoutingContext) -> List[RouteSegment]:
        """A* routing with heuristic"""
        # Similar to Dijkstra but with heuristic
        # Placeholder implementation
        return self._dijkstra_routing(start, end, context)

    def _mesh_aware_routing(self, start: Tuple[float, float], end: Tuple[float, float],
                           context: RoutingContext) -> List[RouteSegment]:
        """Routing that considers mesh network topology"""
        # This would integrate with mesh routing to find routes that leverage mesh nodes
        # Placeholder implementation
        segments = self._dijkstra_routing(start, end, context)

        # Add mesh node information
        for segment in segments:
            # Simulate mesh nodes along the route
            num_nodes = int(segment.distance_meters / 500)  # Node every 500m
            segment.mesh_nodes = [f"mesh_node_{i}" for i in range(num_nodes)]

        return segments

    def _haversine_distance(self, point1: Tuple[float, float],
                           point2: Tuple[float, float]) -> float:
        """Calculate distance between two points using Haversine formula"""
        lat1, lon1 = point1
        lat2, lon2 = point2

        # Convert to radians
        lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
        lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        # Earth radius in meters
        R = 6371000
        return R * c

    async def find_optimal_route(self, context: RoutingContext,
                                algorithm: str = 'mesh_aware') -> Route:
        """Find optimal route using specified algorithm"""
        try:
            if algorithm not in self.algorithms:
                raise GeoAIRoutingError(f"Unknown routing algorithm: {algorithm}")

            # Get base route from algorithm
            segments = self.algorithms[algorithm](context.start_location,
                                                context.end_location, context)

            # Enhance with traffic predictions
            await self._add_traffic_predictions(segments, context.departure_time)

            # Calculate route metrics
            total_distance = sum(s.distance_meters for s in segments)
            total_duration = sum(s.duration_seconds for s in segments)

            # Calculate mesh coverage
            mesh_distance = sum(len(s.mesh_nodes) * 100 for s in segments)  # Assume 100m per node
            mesh_coverage = min(1.0, mesh_distance / total_distance) if total_distance > 0 else 0

            # Generate route ID
            route_id = f"route_{context.start_location}_{context.end_location}_{context.departure_time.timestamp()}"

            route = Route(
                route_id=route_id,
                segments=segments,
                total_distance=total_distance,
                total_duration=total_duration,
                confidence_score=0.85,  # Placeholder
                predicted_traffic={s.instructions: s.traffic_level for s in segments},
                mesh_coverage=mesh_coverage
            )

            # Generate alternatives
            route.alternatives = await self._generate_alternatives(route, context)

            return route

        except Exception as e:
            logger.error(f"Route optimization failed: {e}")
            raise GeoAIRoutingError(f"Failed to find optimal route: {e}")

    async def _add_traffic_predictions(self, segments: List[RouteSegment],
                                     departure_time: datetime):
        """Add traffic predictions to route segments"""
        for segment in segments:
            # Create segment ID (simplified)
            segment_id = f"{segment.start_point}_{segment.end_point}"

            # Get traffic prediction
            prediction = self.traffic_predictor.predict_traffic(
                segment_id, departure_time
            )

            segment.traffic_level = prediction.predicted_level

    async def _generate_alternatives(self, main_route: Route,
                                   context: RoutingContext) -> List[Route]:
        """Generate alternative routes"""
        alternatives = []

        # Try different algorithms
        for alt_algorithm in ['dijkstra', 'a_star']:
            if alt_algorithm != 'mesh_aware':  # Don't duplicate main route
                try:
                    alt_route = await self.find_optimal_route(context, alt_algorithm)
                    alternatives.append(alt_route)
                except Exception as e:
                    logger.debug(f"Failed to generate alternative route: {e}")

        return alternatives[:3]  # Limit to 3 alternatives

class GeoAIRouting:
    """
    Main GeoAI routing system

    Provides intelligent routing with AI predictions, real-time data,
    and mesh network integration.
    """

    def __init__(self, yandex_credentials: Optional[Dict[str, str]] = None,
                 cache_dir: str = "./cache/geoai"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.traffic_predictor = TrafficPredictor(self.cache_dir / "traffic_model.pkl")

        # Yandex integration
        self.yandex_connector = None
        self.cache = None

        if yandex_credentials:
            from ..core.yandex_connector import YandexCredentials
            creds = YandexCredentials(**yandex_credentials)
            self.yandex_connector = YandexConnector(creds)
            self.cache = YandexOfflineCache(str(self.cache_dir / "yandex"))

        self.route_optimizer = RouteOptimizer(
            self.traffic_predictor, self.yandex_connector, self.cache
        )

        # Route cache
        self.route_cache: Dict[str, Route] = {}
        self.cache_ttl = timedelta(hours=1)

        # Statistics
        self.stats = {
            'routes_calculated': 0,
            'cache_hits': 0,
            'api_calls': 0,
            'average_confidence': 0.0
        }

    async def __aenter__(self):
        if self.yandex_connector:
            await self.yandex_connector.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.yandex_connector:
            await self.yandex_connector.__aexit__(exc_type, exc_val, exc_tb)

    async def calculate_route(self, start_lat: float, start_lon: float,
                            end_lat: float, end_lon: float,
                            departure_time: Optional[datetime] = None,
                            preferences: Dict[str, Any] = None,
                            transport_modes: Set[str] = None) -> Route:
        """
        Calculate optimal route with AI predictions

        Args:
            start_lat, start_lon: Starting coordinates
            end_lat, end_lon: Ending coordinates
            departure_time: When to start the route
            preferences: User preferences (avoid_highways, prefer_fastest, etc.)
            transport_modes: Available transport modes

        Returns:
            Optimized route with predictions
        """
        try:
            if departure_time is None:
                departure_time = datetime.now()

            if preferences is None:
                preferences = {}

            if transport_modes is None:
                transport_modes = {'car', 'pedestrian'}

            # Create routing context
            context = RoutingContext(
                start_location=(start_lat, start_lon),
                end_location=(end_lat, end_lon),
                departure_time=departure_time,
                preferences=preferences,
                constraints={},  # Could include time limits, etc.
                available_modes=transport_modes
            )

            # Check cache first
            cache_key = self._get_cache_key(context)
            if cache_key in self.route_cache:
                cached_route = self.route_cache[cache_key]
                if datetime.now() - cached_route.segments[0].timestamp < self.cache_ttl:
                    self.stats['cache_hits'] += 1
                    return cached_route

            # Calculate new route
            route = await self.route_optimizer.find_optimal_route(context)

            # Cache the result
            self.route_cache[cache_key] = route
            self.stats['routes_calculated'] += 1

            # Update average confidence
            self.stats['average_confidence'] = (
                (self.stats['average_confidence'] * (self.stats['routes_calculated'] - 1)) +
                route.confidence_score
            ) / self.stats['routes_calculated']

            return route

        except Exception as e:
            logger.error(f"Route calculation failed: {e}")
            raise GeoAIRoutingError(f"Failed to calculate route: {e}")

    def _get_cache_key(self, context: RoutingContext) -> str:
        """Generate cache key for routing context"""
        key_parts = [
            f"{context.start_location[0]:.4f},{context.start_location[1]:.4f}",
            f"{context.end_location[0]:.4f},{context.end_location[1]:.4f}",
            context.departure_time.strftime("%Y%m%d%H%M"),
            str(sorted(context.preferences.items())),
            str(sorted(context.available_modes))
        ]
        return "|".join(key_parts)

    async def get_real_time_updates(self, route: Route) -> Dict[str, Any]:
        """Get real-time updates for a route"""
        updates = {
            'traffic_changes': [],
            'delays': [],
            'alternatives': [],
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Check for traffic changes
            for segment in route.segments:
                segment_id = f"{segment.start_point}_{segment.end_point}"
                current_prediction = self.traffic_predictor.predict_traffic(
                    segment_id, datetime.now()
                )

                if abs(current_prediction.predicted_level - segment.traffic_level) > 2:
                    updates['traffic_changes'].append({
                        'segment': segment.instructions,
                        'old_level': segment.traffic_level,
                        'new_level': current_prediction.predicted_level,
                        'change': current_prediction.predicted_level - segment.traffic_level
                    })

            # Check for delays (simplified)
            total_delay = sum(change['change'] * 60 for change in updates['traffic_changes'])  # minutes
            if total_delay > 5:
                updates['delays'].append({
                    'total_delay_minutes': total_delay,
                    'affected_segments': len(updates['traffic_changes'])
                })

        except Exception as e:
            logger.error(f"Failed to get real-time updates: {e}")

        return updates

    async def optimize_for_mesh(self, route: Route, mesh_router: MeshRouter) -> Route:
        """Optimize route for mesh network coverage"""
        try:
            # Get mesh network topology
            mesh_nodes = await mesh_router.get_available_nodes()

            # Find segments that can be optimized with mesh
            optimized_segments = []
            for segment in route.segments:
                # Check if mesh nodes are available along this segment
                nearby_nodes = [
                    node for node in mesh_nodes
                    if self._distance_to_segment(node.location, segment) < 100  # 100m threshold
                ]

                if nearby_nodes:
                    # Create mesh-optimized segment
                    optimized_segment = RouteSegment(
                        start_point=segment.start_point,
                        end_point=segment.end_point,
                        distance_meters=segment.distance_meters,
                        duration_seconds=int(segment.duration_seconds * 0.9),  # 10% faster with mesh
                        transport_mode=segment.transport_mode,
                        instructions=f"{segment.instructions} (Mesh-optimized)",
                        traffic_level=segment.traffic_level,
                        mesh_nodes=[node.node_id for node in nearby_nodes]
                    )
                    optimized_segments.append(optimized_segment)
                else:
                    optimized_segments.append(segment)

            # Recalculate totals
            total_distance = sum(s.distance_meters for s in optimized_segments)
            total_duration = sum(s.duration_seconds for s in optimized_segments)
            mesh_distance = sum(len(s.mesh_nodes) * 100 for s in optimized_segments)
            mesh_coverage = min(1.0, mesh_distance / total_distance) if total_distance > 0 else 0

            optimized_route = Route(
                route_id=f"{route.route_id}_mesh_optimized",
                segments=optimized_segments,
                total_distance=total_distance,
                total_duration=total_duration,
                confidence_score=min(1.0, route.confidence_score + 0.1),  # Slight boost
                predicted_traffic=route.predicted_traffic,
                mesh_coverage=mesh_coverage,
                alternatives=route.alternatives
            )

            return optimized_route

        except Exception as e:
            logger.error(f"Mesh optimization failed: {e}")
            return route  # Return original route if optimization fails

    def _distance_to_segment(self, point: Tuple[float, float],
                           segment: RouteSegment) -> float:
        """Calculate distance from point to line segment"""
        # Simplified implementation - distance to start point
        return self.route_optimizer._haversine_distance(point, segment.start_point)

    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        return {
            **self.stats,
            'cache_size': len(self.route_cache),
            'cache_hit_rate': self.stats['cache_hits'] / max(1, self.stats['routes_calculated'])
        }

    async def cleanup(self):
        """Clean up expired cache entries"""
        now = datetime.now()
        expired_keys = [
            key for key, route in self.route_cache.items()
            if now - route.segments[0].timestamp > self.cache_ttl
        ]

        for key in expired_keys:
            del self.route_cache[key]

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired route cache entries")

# Convenience functions
async def create_geoai_routing(yandex_credentials: Optional[Dict[str, str]] = None) -> GeoAIRouting:
    """Factory function to create GeoAI routing system"""
    routing = GeoAIRouting(yandex_credentials)
    return routing

# Example usage and testing
async def test_geoai_routing():
    """Test the GeoAI routing system"""
    routing = GeoAIRouting()

    async with routing:
        try:
            # Test route calculation
            route = await routing.calculate_route(
                start_lat=55.7558, start_lon=37.6176,  # Moscow center
                end_lat=55.7642, end_lon=37.6026,     # Nearby location
                preferences={'prefer_fastest': True},
                transport_modes={'car', 'pedestrian'}
            )

            print(f"Route calculated: {route.total_distance:.0f}m, {route.total_duration}s")
            print(f"Mesh coverage: {route.mesh_coverage:.1%}")
            print(f"Confidence: {route.confidence_score:.2f}")

            # Test real-time updates
            updates = await routing.get_real_time_updates(route)
            print(f"Real-time updates: {len(updates['traffic_changes'])} changes")

        except GeoAIRoutingError as e:
            print(f"Routing error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_geoai_routing())
