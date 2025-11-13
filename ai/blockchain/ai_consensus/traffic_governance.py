"""
Decentralized AI Consensus for Mesh Traffic Governance

This module implements AI-driven consensus mechanisms for governing
mesh network traffic including routing decisions, bandwidth allocation,
and quality of service optimization.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import statistics
import random

logger = logging.getLogger(__name__)


@dataclass
class TrafficDecision:
    """Represents an AI consensus decision for traffic governance."""
    decision_id: str
    decision_type: str  # 'routing', 'bandwidth', 'qos', 'congestion'
    target_nodes: List[str]
    parameters: Dict[str, Any]
    confidence_score: float
    timestamp: float
    consensus_reached: bool
    participating_nodes: List[str]
    votes: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'decision_id': self.decision_id,
            'decision_type': self.decision_type,
            'target_nodes': self.target_nodes,
            'parameters': self.parameters,
            'confidence_score': self.confidence_score,
            'timestamp': self.timestamp,
            'consensus_reached': self.consensus_reached,
            'participating_nodes': self.participating_nodes,
            'votes': self.votes
        }


@dataclass
class NodeReputation:
    """Reputation score for mesh nodes."""
    node_id: str
    routing_reliability: float  # 0.0 - 1.0
    bandwidth_contribution: float
    consensus_participation: float
    traffic_quality: float
    last_updated: float

    @property
    def overall_score(self) -> float:
        """Calculate overall reputation score."""
        weights = {
            'routing_reliability': 0.4,
            'bandwidth_contribution': 0.3,
            'consensus_participation': 0.2,
            'traffic_quality': 0.1
        }

        score = sum(
            getattr(self, metric) * weight
            for metric, weight in weights.items()
        )

        return min(1.0, max(0.0, score))


@dataclass
class TrafficMetrics:
    """Real-time traffic metrics for decision making."""
    node_id: str
    bandwidth_usage: float  # Mbps
    latency: float  # ms
    packet_loss: float  # percentage
    queue_length: int
    active_connections: int
    timestamp: float


class AIDecisionEngine:
    """
    AI Decision Engine for Traffic Governance.

    Uses machine learning and consensus algorithms to make
    intelligent decisions about mesh network traffic management.
    """

    def __init__(self, node_id: str, min_consensus_threshold: float = 0.67):
        self.node_id = node_id
        self.min_consensus_threshold = min_consensus_threshold

        # Decision tracking
        self.pending_decisions: Dict[str, TrafficDecision] = {}
        self.completed_decisions: Dict[str, TrafficDecision] = {}

        # Node reputation system
        self.node_reputations: Dict[str, NodeReputation] = {}

        # Traffic metrics
        self.traffic_metrics: Dict[str, List[TrafficMetrics]] = {}

        # AI models (simplified placeholders)
        self.routing_model = None
        self.bandwidth_model = None
        self.qos_model = None

    async def propose_decision(self, decision_type: str, target_nodes: List[str],
                              parameters: Dict[str, Any], mesh_network) -> str:
        """
        Propose a new traffic governance decision.

        Args:
            decision_type: Type of decision
            target_nodes: Affected nodes
            parameters: Decision parameters
            mesh_network: Mesh network instance

        Returns:
            Decision ID
        """
        decision_id = f"decision_{decision_type}_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"

        # Analyze current traffic conditions
        traffic_analysis = await self._analyze_traffic_conditions(target_nodes)

        # Generate AI recommendation
        ai_recommendation = await self._generate_ai_recommendation(
            decision_type, parameters, traffic_analysis
        )

        # Create decision proposal
        decision = TrafficDecision(
            decision_id=decision_id,
            decision_type=decision_type,
            target_nodes=target_nodes,
            parameters={**parameters, **ai_recommendation},
            confidence_score=ai_recommendation.get('confidence', 0.5),
            timestamp=datetime.now().timestamp(),
            consensus_reached=False,
            participating_nodes=[self.node_id],
            votes={self.node_id: {'vote': 'approve', 'weight': 1.0}}
        )

        self.pending_decisions[decision_id] = decision

        # Broadcast to mesh network
        await self._broadcast_decision(decision, mesh_network)

        logger.info(f"Proposed {decision_type} decision {decision_id}")
        return decision_id

    async def vote_on_decision(self, decision_id: str, vote: str, weight: float = 1.0) -> bool:
        """
        Vote on a pending decision.

        Args:
            decision_id: Decision to vote on
            vote: 'approve', 'reject', or 'abstain'
            weight: Voting weight based on reputation

        Returns:
            True if vote recorded
        """
        if decision_id not in self.pending_decisions:
            return False

        decision = self.pending_decisions[decision_id]

        if self.node_id in decision.participating_nodes:
            return False  # Already voted

        decision.participating_nodes.append(self.node_id)
        decision.votes[self.node_id] = {
            'vote': vote,
            'weight': weight,
            'timestamp': datetime.now().timestamp()
        }

        # Check if consensus reached
        await self._check_consensus(decision_id)

        logger.info(f"Voted {vote} on decision {decision_id}")
        return True

    async def _check_consensus(self, decision_id: str):
        """Check if consensus has been reached for a decision."""
        decision = self.pending_decisions[decision_id]

        total_weight = sum(vote_data['weight'] for vote_data in decision.votes.values())
        approve_weight = sum(
            vote_data['weight'] for vote_data in decision.votes.values()
            if vote_data['vote'] == 'approve'
        )

        if total_weight > 0:
            consensus_ratio = approve_weight / total_weight

            if consensus_ratio >= self.min_consensus_threshold:
                decision.consensus_reached = True

                # Move to completed decisions
                self.completed_decisions[decision_id] = decision
                del self.pending_decisions[decision_id]

                # Execute the decision
                await self._execute_decision(decision)

                logger.info(f"Consensus reached for decision {decision_id} ({consensus_ratio:.2%})")

    async def _execute_decision(self, decision: TrafficDecision):
        """Execute a consensus-approved decision."""
        try:
            if decision.decision_type == 'routing':
                await self._execute_routing_decision(decision)
            elif decision.decision_type == 'bandwidth':
                await self._execute_bandwidth_decision(decision)
            elif decision.decision_type == 'qos':
                await self._execute_qos_decision(decision)
            elif decision.decision_type == 'congestion':
                await self._execute_congestion_decision(decision)

            logger.info(f"Executed {decision.decision_type} decision {decision.decision_id}")

        except Exception as e:
            logger.error(f"Failed to execute decision {decision.decision_id}: {e}")

    async def _execute_routing_decision(self, decision: TrafficDecision):
        """Execute routing optimization decision."""
        # Update routing tables based on decision parameters
        new_routes = decision.parameters.get('new_routes', {})
        # Implementation would update mesh routing tables
        pass

    async def _execute_bandwidth_decision(self, decision: TrafficDecision):
        """Execute bandwidth allocation decision."""
        allocations = decision.parameters.get('allocations', {})
        # Implementation would adjust bandwidth limits
        pass

    async def _execute_qos_decision(self, decision: TrafficDecision):
        """Execute quality of service decision."""
        qos_settings = decision.parameters.get('qos_settings', {})
        # Implementation would update QoS parameters
        pass

    async def _execute_congestion_decision(self, decision: TrafficDecision):
        """Execute congestion control decision."""
        control_actions = decision.parameters.get('control_actions', [])
        # Implementation would implement congestion control
        pass

    async def _analyze_traffic_conditions(self, target_nodes: List[str]) -> Dict[str, Any]:
        """Analyze current traffic conditions for decision making."""
        analysis = {
            'avg_bandwidth': 0.0,
            'avg_latency': 0.0,
            'congestion_level': 0.0,
            'node_health': {}
        }

        for node_id in target_nodes:
            if node_id in self.traffic_metrics:
                metrics_list = self.traffic_metrics[node_id][-10:]  # Last 10 measurements

                if metrics_list:
                    analysis['node_health'][node_id] = {
                        'bandwidth': statistics.mean(m.bandwidth_usage for m in metrics_list),
                        'latency': statistics.mean(m.latency for m in metrics_list),
                        'packet_loss': statistics.mean(m.packet_loss for m in metrics_list),
                        'connections': metrics_list[-1].active_connections
                    }

        # Calculate network-wide averages
        if analysis['node_health']:
            analysis['avg_bandwidth'] = statistics.mean(
                health['bandwidth'] for health in analysis['node_health'].values()
            )
            analysis['avg_latency'] = statistics.mean(
                health['latency'] for health in analysis['node_health'].values()
            )
            analysis['congestion_level'] = min(1.0, analysis['avg_latency'] / 100.0)  # Normalize

        return analysis

    async def _generate_ai_recommendation(self, decision_type: str,
                                        parameters: Dict[str, Any],
                                        traffic_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered recommendation for decision."""
        recommendation = {
            'confidence': 0.5,
            'reasoning': 'Basic analysis'
        }

        try:
            if decision_type == 'routing':
                recommendation.update(await self._ai_routing_recommendation(parameters, traffic_analysis))
            elif decision_type == 'bandwidth':
                recommendation.update(await self._ai_bandwidth_recommendation(parameters, traffic_analysis))
            elif decision_type == 'qos':
                recommendation.update(await self._ai_qos_recommendation(parameters, traffic_analysis))
            elif decision_type == 'congestion':
                recommendation.update(await self._ai_congestion_recommendation(parameters, traffic_analysis))

        except Exception as e:
            logger.error(f"AI recommendation failed: {e}")

        return recommendation

    async def _ai_routing_recommendation(self, parameters: Dict[str, Any],
                                       traffic_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """AI recommendation for routing decisions."""
        # Simplified AI logic - in practice, use ML models
        congestion_level = traffic_analysis.get('congestion_level', 0.0)

        if congestion_level > 0.7:
            # High congestion - recommend alternative routes
            return {
                'action': 'reroute_traffic',
                'alternative_paths': ['path_a', 'path_b'],
                'confidence': 0.8,
                'reasoning': 'High congestion detected, rerouting recommended'
            }
        else:
            return {
                'action': 'maintain_routes',
                'confidence': 0.6,
                'reasoning': 'Traffic conditions normal'
            }

    async def _ai_bandwidth_recommendation(self, parameters: Dict[str, Any],
                                         traffic_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """AI recommendation for bandwidth allocation."""
        avg_bandwidth = traffic_analysis.get('avg_bandwidth', 0.0)

        if avg_bandwidth > 80:  # 80% utilization
            return {
                'action': 'reduce_bandwidth',
                'reduction_percentage': 20,
                'confidence': 0.75,
                'reasoning': 'High bandwidth utilization detected'
            }
        else:
            return {
                'action': 'maintain_bandwidth',
                'confidence': 0.6,
                'reasoning': 'Bandwidth utilization normal'
            }

    async def _ai_qos_recommendation(self, parameters: Dict[str, Any],
                                   traffic_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """AI recommendation for QoS settings."""
        avg_latency = traffic_analysis.get('avg_latency', 0.0)

        if avg_latency > 50:  # High latency
            return {
                'action': 'prioritize_low_latency',
                'priority_queues': ['voice', 'video'],
                'confidence': 0.7,
                'reasoning': 'High latency detected, prioritizing real-time traffic'
            }
        else:
            return {
                'action': 'balanced_qos',
                'confidence': 0.6,
                'reasoning': 'Latency within acceptable range'
            }

    async def _ai_congestion_recommendation(self, parameters: Dict[str, Any],
                                          traffic_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """AI recommendation for congestion control."""
        congestion_level = traffic_analysis.get('congestion_level', 0.0)

        if congestion_level > 0.8:
            return {
                'action': 'implement_congestion_control',
                'control_mechanism': 'RED',  # Random Early Detection
                'threshold': 0.8,
                'confidence': 0.85,
                'reasoning': 'Severe congestion detected, control measures needed'
            }
        else:
            return {
                'action': 'monitor_only',
                'confidence': 0.6,
                'reasoning': 'Congestion levels acceptable'
            }

    async def update_traffic_metrics(self, metrics: TrafficMetrics):
        """Update traffic metrics for a node."""
        if metrics.node_id not in self.traffic_metrics:
            self.traffic_metrics[metrics.node_id] = []

        self.traffic_metrics[metrics.node_id].append(metrics)

        # Keep only recent metrics (last 100)
        if len(self.traffic_metrics[metrics.node_id]) > 100:
            self.traffic_metrics[metrics.node_id] = self.traffic_metrics[metrics.node_id][-100:]

    async def update_node_reputation(self, node_id: str, metrics: Dict[str, Any]):
        """Update reputation score for a node."""
        if node_id not in self.node_reputations:
            self.node_reputations[node_id] = NodeReputation(
                node_id=node_id,
                routing_reliability=0.5,
                bandwidth_contribution=0.5,
                consensus_participation=0.5,
                traffic_quality=0.5,
                last_updated=datetime.now().timestamp()
            )

        reputation = self.node_reputations[node_id]

        # Update metrics with exponential moving average
        alpha = 0.1  # Smoothing factor

        reputation.routing_reliability = (1 - alpha) * reputation.routing_reliability + alpha * metrics.get('routing_success', 0.5)
        reputation.bandwidth_contribution = (1 - alpha) * reputation.bandwidth_contribution + alpha * metrics.get('bandwidth_shared', 0.5)
        reputation.consensus_participation = (1 - alpha) * reputation.consensus_participation + alpha * metrics.get('votes_participated', 0.5)
        reputation.traffic_quality = (1 - alpha) * reputation.traffic_quality + alpha * metrics.get('quality_score', 0.5)

        reputation.last_updated = datetime.now().timestamp()

    async def _broadcast_decision(self, decision: TrafficDecision, mesh_network):
        """Broadcast decision to mesh network."""
        # Implementation would send decision to mesh network
        logger.debug(f"Broadcasting decision {decision.decision_id} to mesh network")

    def get_pending_decisions(self) -> List[str]:
        """Get list of pending decision IDs."""
        return list(self.pending_decisions.keys())

    def get_decision_status(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a decision."""
        if decision_id in self.pending_decisions:
            decision = self.pending_decisions[decision_id]
        elif decision_id in self.completed_decisions:
            decision = self.completed_decisions[decision_id]
        else:
            return None

        return {
            'decision_id': decision.decision_id,
            'type': decision.decision_type,
            'consensus_reached': decision.consensus_reached,
            'participants': len(decision.participating_nodes),
            'confidence': decision.confidence_score,
            'timestamp': decision.timestamp
        }

    def get_network_stats(self) -> Dict[str, Any]:
        """Get network-wide AI consensus statistics."""
        return {
            'pending_decisions': len(self.pending_decisions),
            'completed_decisions': len(self.completed_decisions),
            'tracked_nodes': len(self.node_reputations),
            'avg_reputation': statistics.mean(
                rep.overall_score for rep in self.node_reputations.values()
            ) if self.node_reputations else 0.0
        }


class MeshTrafficGovernor:
    """
    Mesh Traffic Governor using AI Consensus.

    Coordinates AI-driven traffic governance across the mesh network
    with decentralized decision making and reputation-based consensus.
    """

    def __init__(self, mesh_network):
        self.mesh_network = mesh_network
        self.decision_engines: Dict[str, AIDecisionEngine] = {}

    def add_node_engine(self, node_id: str) -> AIDecisionEngine:
        """Add decision engine for a node."""
        if node_id not in self.decision_engines:
            self.decision_engines[node_id] = AIDecisionEngine(node_id)
        return self.decision_engines[node_id]

    async def optimize_routing(self, source_node: str, target_nodes: List[str]) -> bool:
        """Optimize routing using AI consensus."""
        if source_node not in self.decision_engines:
            return False

        engine = self.decision_engines[source_node]

        decision_id = await engine.propose_decision(
            'routing',
            target_nodes,
            {'optimization_type': 'latency_minimization'},
            self.mesh_network
        )

        return decision_id is not None

    async def allocate_bandwidth(self, requester_node: str, requested_bandwidth: float) -> bool:
        """Allocate bandwidth using AI consensus."""
        if requester_node not in self.decision_engines:
            return False

        engine = self.decision_engines[requester_node]

        decision_id = await engine.propose_decision(
            'bandwidth',
            [requester_node],
            {'requested_bandwidth': requested_bandwidth},
            self.mesh_network
        )

        return decision_id is not None

    async def manage_congestion(self, congested_nodes: List[str]) -> bool:
        """Manage network congestion using AI consensus."""
        # Use the first available engine to propose
        for engine in self.decision_engines.values():
            decision_id = await engine.propose_decision(
                'congestion',
                congested_nodes,
                {'severity': 'high'},
                self.mesh_network
            )
            if decision_id:
                return True

        return False

    async def update_network_metrics(self, metrics_data: Dict[str, TrafficMetrics]):
        """Update traffic metrics across all nodes."""
        for node_id, metrics in metrics_data.items():
            if node_id in self.decision_engines:
                await self.decision_engines[node_id].update_traffic_metrics(metrics)

    def get_governance_stats(self) -> Dict[str, Any]:
        """Get governance statistics across all nodes."""
        total_pending = sum(len(engine.get_pending_decisions()) for engine in self.decision_engines.values())
        total_completed = sum(len(engine.completed_decisions) for engine in self.decision_engines.values())

        return {
            'total_nodes': len(self.decision_engines),
            'total_pending_decisions': total_pending,
            'total_completed_decisions': total_completed,
            'avg_decisions_per_node': (total_pending + total_completed) / max(1, len(self.decision_engines))
        }
