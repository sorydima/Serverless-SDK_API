"""
Quantum Mesh Consensus Module.
Implements hybrid consensus algorithm with quantum superposition elements.
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import Dict, List, Set, Tuple, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import numpy as np
import random
from enum import Enum

logger = logging.getLogger(__name__)

class ConsensusState(Enum):
    PROPOSAL = "proposal"
    VOTING = "voting"
    QUANTUM_SUPERPOSITION = "quantum_superposition"
    CLASSICAL_COLLAPSE = "classical_collapse"
    COMMITTED = "committed"
    FAILED = "failed"

@dataclass
class QuantumVote:
    """Represents a vote with quantum superposition properties."""
    voter_id: str
    proposal_id: str
    vote_value: Any  # Can be classical (0/1) or quantum state
    superposition_weight: float  # Weight in quantum superposition (0.0 to 1.0)
    timestamp: float
    signature: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'voter_id': self.voter_id,
            'proposal_id': self.proposal_id,
            'vote_value': self.vote_value,
            'superposition_weight': self.superposition_weight,
            'timestamp': self.timestamp,
            'signature': self.signature
        }

@dataclass
class ConsensusProposal:
    """Represents a consensus proposal."""
    proposal_id: str
    proposer_id: str
    content: Any
    timestamp: float
    quantum_threshold: float = 0.67  # Threshold for quantum consensus
    classical_threshold: float = 0.51  # Threshold for classical fallback

    votes: Dict[str, QuantumVote] = field(default_factory=dict)
    state: ConsensusState = ConsensusState.PROPOSAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            'proposal_id': self.proposal_id,
            'proposer_id': self.proposer_id,
            'content': self.content,
            'timestamp': self.timestamp,
            'quantum_threshold': self.quantum_threshold,
            'classical_threshold': self.classical_threshold,
            'votes': {k: v.to_dict() for k, v in self.votes.items()},
            'state': self.state.value
        }

class QuantumConsensusEngine:
    """
    Hybrid consensus engine combining classical voting with quantum superposition.
    """

    def __init__(self, node_id: str, total_nodes: int = 10):
        self.node_id = node_id
        self.total_nodes = total_nodes

        # Consensus state
        self.proposals: Dict[str, ConsensusProposal] = {}
        self.active_proposals: Set[str] = set()

        # Quantum state tracking
        self.quantum_states: Dict[str, Dict[str, complex]] = {}  # proposal_id -> node_id -> amplitude

        # Network state
        self.known_nodes: Set[str] = {node_id}
        self.node_weights: Dict[str, float] = {node_id: 1.0}

        # Consensus parameters
        self.voting_timeout = 30.0  # seconds
        self.superposition_timeout = 10.0  # seconds
        self.max_retries = 3

        # Callbacks
        self.consensus_callbacks: List[Callable[[str, bool, Any], None]] = []

        logger.info(f"Quantum Consensus Engine initialized for node {node_id}")

    def add_node(self, node_id: str, weight: float = 1.0):
        """Add a known node to the consensus network."""
        self.known_nodes.add(node_id)
        self.node_weights[node_id] = weight
        self.total_nodes = len(self.known_nodes)

    def remove_node(self, node_id: str):
        """Remove a node from the consensus network."""
        if node_id in self.known_nodes:
            self.known_nodes.remove(node_id)
            if node_id in self.node_weights:
                del self.node_weights[node_id]
            self.total_nodes = len(self.known_nodes)

    def propose(self, content: Any, proposer_id: Optional[str] = None) -> str:
        """
        Create a new consensus proposal.

        Args:
            content: The proposal content
            proposer_id: ID of the proposer (defaults to self.node_id)

        Returns:
            Proposal ID
        """
        if proposer_id is None:
            proposer_id = self.node_id

        proposal_id = f"proposal_{int(time.time() * 1000)}_{hash(str(content)) % 10000}"

        proposal = ConsensusProposal(
            proposal_id=proposal_id,
            proposer_id=proposer_id,
            content=content,
            timestamp=time.time()
        )

        self.proposals[proposal_id] = proposal
        self.active_proposals.add(proposal_id)

        # Initialize quantum state for superposition
        self.quantum_states[proposal_id] = {}

        # Start consensus process
        asyncio.create_task(self._run_consensus_process(proposal))

        logger.info(f"Created proposal {proposal_id} by {proposer_id}")
        return proposal_id

    async def _run_consensus_process(self, proposal: ConsensusProposal):
        """Run the complete consensus process for a proposal."""
        try:
            # Phase 1: Classical voting
            proposal.state = ConsensusState.VOTING
            await self._collect_votes(proposal)

            # Phase 2: Quantum superposition analysis
            proposal.state = ConsensusState.QUANTUM_SUPERPOSITION
            quantum_result = await self._quantum_superposition_analysis(proposal)

            # Phase 3: Classical collapse decision
            proposal.state = ConsensusState.CLASSICAL_COLLAPSE
            final_decision = await self._classical_collapse(proposal, quantum_result)

            # Phase 4: Commit or fail
            if final_decision:
                proposal.state = ConsensusState.COMMITTED
                self._notify_consensus_callbacks(proposal.proposal_id, True, proposal.content)
            else:
                proposal.state = ConsensusState.FAILED
                self._notify_consensus_callbacks(proposal.proposal_id, False, None)

        except Exception as e:
            logger.error(f"Consensus process failed for {proposal.proposal_id}: {e}")
            proposal.state = ConsensusState.FAILED
            self._notify_consensus_callbacks(proposal.proposal_id, False, None)

        finally:
            # Clean up
            self.active_proposals.discard(proposal.proposal_id)

    async def _collect_votes(self, proposal: ConsensusProposal):
        """Collect votes from network nodes."""
        # In a real implementation, this would broadcast to network
        # For simulation, we'll simulate votes from known nodes

        vote_collection_time = min(self.voting_timeout, 5.0)  # Shorter for simulation

        # Simulate receiving votes
        for node_id in self.known_nodes:
            if node_id == proposal.proposer_id:
                continue  # Proposer doesn't vote

            # Simulate vote arrival
            await asyncio.sleep(random.uniform(0.1, vote_collection_time))

            vote_value = self._simulate_vote(proposal.content, node_id)
            superposition_weight = random.uniform(0.5, 1.0)

            vote = QuantumVote(
                voter_id=node_id,
                proposal_id=proposal.proposal_id,
                vote_value=vote_value,
                superposition_weight=superposition_weight,
                timestamp=time.time()
            )

            proposal.votes[node_id] = vote

            # Update quantum state
            self.quantum_states[proposal.proposal_id][node_id] = complex(
                superposition_weight if vote_value else 0.0,
                random.uniform(-0.5, 0.5)  # Phase
            )

        logger.info(f"Collected {len(proposal.votes)} votes for proposal {proposal.proposal_id}")

    def _simulate_vote(self, content: Any, voter_id: str) -> bool:
        """Simulate a vote based on content and voter."""
        # Simple simulation: approve with 70% probability
        # In practice, this would be based on actual consensus rules
        content_hash = hashlib.sha256(str(content).encode()).hexdigest()
        voter_hash = hashlib.sha256(voter_id.encode()).hexdigest()

        combined = content_hash + voter_hash
        vote_score = int(combined[:8], 16) % 100

        return vote_score < 70  # 70% approval rate

    async def _quantum_superposition_analysis(self, proposal: ConsensusProposal) -> Dict[str, Any]:
        """Perform quantum superposition analysis on votes."""
        await asyncio.sleep(self.superposition_timeout / 2)  # Simulate quantum processing

        quantum_state = self.quantum_states[proposal.proposal_id]

        # Calculate quantum consensus metrics
        amplitudes = list(quantum_state.values())

        if not amplitudes:
            return {'consensus_probability': 0.0, 'entanglement_measure': 0.0}

        # Calculate superposition consensus
        total_amplitude = sum(abs(amp) for amp in amplitudes)
        avg_amplitude = total_amplitude / len(amplitudes)

        # Calculate entanglement measure (simplified)
        phases = [np.angle(amp) for amp in amplitudes]
        phase_variance = np.var(phases) if phases else 0.0
        entanglement_measure = 1.0 - min(phase_variance / np.pi, 1.0)

        # Consensus probability based on amplitude alignment
        consensus_probability = min(avg_amplitude * 2.0, 1.0)

        result = {
            'consensus_probability': consensus_probability,
            'entanglement_measure': entanglement_measure,
            'total_amplitude': total_amplitude,
            'average_amplitude': avg_amplitude,
            'phase_variance': phase_variance
        }

        logger.info(f"Quantum analysis for {proposal.proposal_id}: consensus_prob={consensus_probability:.3f}")
        return result

    async def _classical_collapse(self, proposal: ConsensusProposal,
                                quantum_result: Dict[str, Any]) -> bool:
        """Perform classical collapse decision."""
        # Count classical votes
        yes_votes = sum(1 for vote in proposal.votes.values() if vote.vote_value)
        total_votes = len(proposal.votes)

        if total_votes == 0:
            return False

        classical_consensus = yes_votes / total_votes
        quantum_consensus = quantum_result['consensus_probability']

        # Hybrid decision: require both classical and quantum consensus
        hybrid_score = (classical_consensus + quantum_consensus) / 2.0

        # Use quantum threshold if entanglement is high
        entanglement = quantum_result['entanglement_measure']
        threshold = proposal.quantum_threshold if entanglement > 0.5 else proposal.classical_threshold

        decision = hybrid_score >= threshold

        logger.info(f"Classical collapse for {proposal.proposal_id}: "
                   f"classical={classical_consensus:.3f}, quantum={quantum_consensus:.3f}, "
                   f"hybrid={hybrid_score:.3f}, threshold={threshold:.3f}, decision={decision}")

        return decision

    def _notify_consensus_callbacks(self, proposal_id: str, success: bool, content: Any):
        """Notify registered callbacks of consensus result."""
        for callback in self.consensus_callbacks:
            try:
                callback(proposal_id, success, content)
            except Exception as e:
                logger.error(f"Error in consensus callback: {e}")

    def add_consensus_callback(self, callback: Callable[[str, bool, Any], None]):
        """Add a callback for consensus results."""
        self.consensus_callbacks.append(callback)

    def get_proposal_status(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a proposal."""
        if proposal_id not in self.proposals:
            return None

        proposal = self.proposals[proposal_id]
        return proposal.to_dict()

    def get_active_proposals(self) -> List[Dict[str, Any]]:
        """Get all active proposals."""
        return [self.proposals[pid].to_dict() for pid in self.active_proposals]

    def get_consensus_metrics(self) -> Dict[str, Any]:
        """Get consensus network metrics."""
        total_proposals = len(self.proposals)
        committed_proposals = sum(1 for p in self.proposals.values() if p.state == ConsensusState.COMMITTED)
        failed_proposals = sum(1 for p in self.proposals.values() if p.state == ConsensusState.FAILED)

        success_rate = committed_proposals / total_proposals if total_proposals > 0 else 0.0

        return {
            'total_nodes': self.total_nodes,
            'total_proposals': total_proposals,
            'committed_proposals': committed_proposals,
            'failed_proposals': failed_proposals,
            'success_rate': success_rate,
            'active_proposals': len(self.active_proposals)
        }

# Mesh integration
class QuantumMeshConsensus:
    """
    Integration of quantum consensus with mesh networking.
    """

    def __init__(self, node_id: str, mesh_network):
        self.node_id = node_id
        self.mesh = mesh_network
        self.consensus_engine = QuantumConsensusEngine(node_id)

        # Connect to mesh network
        self._setup_mesh_integration()

    def _setup_mesh_integration(self):
        """Setup integration with mesh networking layer."""
        # Register consensus message handlers
        self.mesh.register_message_handler('consensus_proposal', self._handle_proposal)
        self.mesh.register_message_handler('consensus_vote', self._handle_vote)
        self.mesh.register_message_handler('consensus_result', self._handle_result)

    def propose_mesh_change(self, change_type: str, change_data: Dict[str, Any]) -> str:
        """
        Propose a change to the mesh network topology or configuration.

        Args:
            change_type: Type of change ('add_node', 'remove_node', 'update_route', etc.)
            change_data: Change-specific data

        Returns:
            Proposal ID
        """
        proposal_content = {
            'type': 'mesh_change',
            'change_type': change_type,
            'change_data': change_data,
            'proposer': self.node_id,
            'timestamp': time.time()
        }

        proposal_id = self.consensus_engine.propose(proposal_content)

        # Broadcast proposal to mesh
        self._broadcast_consensus_message('consensus_proposal', {
            'proposal_id': proposal_id,
            'content': proposal_content
        })

        return proposal_id

    def _handle_proposal(self, message: Dict[str, Any], sender: str):
        """Handle incoming consensus proposal."""
        proposal_id = message['proposal_id']
        content = message['content']

        # Add to local consensus engine
        local_proposal = ConsensusProposal(
            proposal_id=proposal_id,
            proposer_id=content['proposer'],
            content=content,
            timestamp=content['timestamp']
        )

        self.consensus_engine.proposals[proposal_id] = local_proposal
        self.consensus_engine.active_proposals.add(proposal_id)

        # Initialize quantum state
        self.consensus_engine.quantum_states[proposal_id] = {}

        # Start local consensus process
        asyncio.create_task(self.consensus_engine._run_consensus_process(local_proposal))

        # Send vote
        vote = self._generate_vote(proposal_id, content)
        self._send_vote(proposal_id, vote)

    def _handle_vote(self, message: Dict[str, Any], sender: str):
        """Handle incoming vote."""
        vote_data = message['vote']
        proposal_id = vote_data['proposal_id']

        if proposal_id in self.consensus_engine.proposals:
            vote = QuantumVote(**vote_data)
            self.consensus_engine.proposals[proposal_id].votes[sender] = vote

            # Update quantum state
            self.consensus_engine.quantum_states[proposal_id][sender] = complex(
                vote.superposition_weight if vote.vote_value else 0.0,
                random.uniform(-0.5, 0.5)
            )

    def _handle_result(self, message: Dict[str, Any], sender: str):
        """Handle consensus result."""
        result_data = message['result']
        proposal_id = result_data['proposal_id']
        success = result_data['success']

        if success and proposal_id in self.consensus_engine.proposals:
            proposal = self.consensus_engine.proposals[proposal_id]
            if proposal.content['type'] == 'mesh_change':
                self._apply_mesh_change(proposal.content)

    def _generate_vote(self, proposal_id: str, content: Dict[str, Any]) -> QuantumVote:
        """Generate a vote for a proposal."""
        # Simple voting logic
        vote_value = self._evaluate_proposal(content)
        superposition_weight = random.uniform(0.6, 1.0)

        return QuantumVote(
            voter_id=self.node_id,
            proposal_id=proposal_id,
            vote_value=vote_value,
            superposition_weight=superposition_weight,
            timestamp=time.time()
        )

    def _evaluate_proposal(self, content: Dict[str, Any]) -> bool:
        """Evaluate a proposal and decide whether to vote yes/no."""
        if content['type'] == 'mesh_change':
            change_type = content['change_type']

            # Simple evaluation logic
            if change_type == 'add_node':
                # Approve adding nodes
                return True
            elif change_type == 'remove_node':
                # Be more cautious about removing nodes
                return random.choice([True, False])
            elif change_type == 'update_route':
                # Approve route updates
                return True

        return True  # Default to approve

    def _send_vote(self, proposal_id: str, vote: QuantumVote):
        """Send vote to network."""
        self._broadcast_consensus_message('consensus_vote', {
            'vote': vote.to_dict()
        })

    def _broadcast_consensus_message(self, message_type: str, payload: Dict[str, Any]):
        """Broadcast consensus message to mesh network."""
        message = {
            'type': message_type,
            'payload': payload,
            'sender': self.node_id,
            'timestamp': time.time()
        }

        self.mesh.broadcast_message(message)

    def _apply_mesh_change(self, change_content: Dict[str, Any]):
        """Apply a successful mesh change."""
        change_type = change_content['change_type']
        change_data = change_content['change_data']

        if change_type == 'add_node':
            node_id = change_data['node_id']
            self.mesh.add_node(node_id)
            logger.info(f"Added node {node_id} to mesh via consensus")

        elif change_type == 'remove_node':
            node_id = change_data['node_id']
            self.mesh.remove_node(node_id)
            logger.info(f"Removed node {node_id} from mesh via consensus")

        elif change_type == 'update_route':
            # Apply route update
            logger.info("Updated mesh routing via consensus")

# Utility functions
def create_quantum_consensus_network(node_ids: List[str]) -> Dict[str, QuantumConsensusEngine]:
    """Create a network of quantum consensus engines."""
    engines = {}

    for node_id in node_ids:
        engine = QuantumConsensusEngine(node_id, len(node_ids))
        engines[node_id] = engine

        # Add all other nodes
        for other_id in node_ids:
            if other_id != node_id:
                engine.add_node(other_id)

    return engines

def simulate_quantum_consensus_test():
    """Run a simulation test of quantum consensus."""
    node_ids = [f'node_{i}' for i in range(5)]
    engines = create_quantum_consensus_network(node_ids)

    # Simulate proposal and consensus
    proposer = engines['node_0']
    proposal_id = proposer.propose("Test proposal: Add quantum routing")

    # Run simulation for a short time
    async def run_simulation():
        await asyncio.sleep(2.0)  # Let consensus run

        # Check results
        status = proposer.get_proposal_status(proposal_id)
        print(f"Proposal {proposal_id} status: {status['state'] if status else 'Not found'}")

        metrics = proposer.get_consensus_metrics()
        print(f"Network metrics: {metrics}")

    asyncio.run(run_simulation())
