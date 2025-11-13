"""
Offline Voting Application for Mesh Networks

This module implements an offline voting application that works between
mesh network nodes using majority-agreement consensus.
"""

import asyncio
import logging
import time
import hashlib
import json
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass
from enum import Enum
import threading

# Blockchain integration imports
try:
    from ..ai.blockchain.smart_contracts.deploy_vote_validator import VoteValidatorDeployer
    from ..ai.blockchain.polkadot.bridge import PolkadotBridge, MeshMessageRecorder
    _HAS_BLOCKCHAIN = True
except ImportError:
    _HAS_BLOCKCHAIN = False
    VoteValidatorDeployer = None
    PolkadotBridge = None
    MeshMessageRecorder = None

logger = logging.getLogger(__name__)


class VoteStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ConsensusResult(Enum):
    UNDECIDED = "undecided"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIED = "tied"


@dataclass
class VoteOption:
    """Represents a voting option."""
    option_id: str
    title: str
    description: str = ""
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'option_id': self.option_id,
            'title': self.title,
            'description': self.description,
            'metadata': self.metadata or {}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VoteOption':
        return cls(
            option_id=data['option_id'],
            title=data['title'],
            description=data.get('description', ''),
            metadata=data.get('metadata', {})
        )


@dataclass
class Vote:
    """Represents a vote cast by a node."""
    voter_id: str
    option_id: str
    timestamp: float
    signature: str = ""  # Digital signature for verification

    def to_dict(self) -> Dict[str, Any]:
        return {
            'voter_id': self.voter_id,
            'option_id': self.option_id,
            'timestamp': self.timestamp,
            'signature': self.signature
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Vote':
        return cls(
            voter_id=data['voter_id'],
            option_id=data['option_id'],
            timestamp=data['timestamp'],
            signature=data.get('signature', '')
        )

    def calculate_hash(self) -> str:
        """Calculate hash of the vote for integrity."""
        vote_data = f"{self.voter_id}:{self.option_id}:{self.timestamp}"
        return hashlib.sha256(vote_data.encode()).hexdigest()


@dataclass
class VotingSession:
    """Represents a voting session."""
    session_id: str
    title: str
    description: str
    creator_id: str
    options: List[VoteOption]
    start_time: float
    end_time: float
    eligible_voters: Set[str]
    votes: Dict[str, Vote]  # voter_id -> vote
    status: VoteStatus = VoteStatus.PENDING
    consensus_threshold: float = 0.5  # Percentage needed for consensus
    min_participants: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'title': self.title,
            'description': self.description,
            'creator_id': self.creator_id,
            'options': [opt.to_dict() for opt in self.options],
            'start_time': self.start_time,
            'end_time': self.end_time,
            'eligible_voters': list(self.eligible_voters),
            'votes': {vid: vote.to_dict() for vid, vote in self.votes.items()},
            'status': self.status.value,
            'consensus_threshold': self.consensus_threshold,
            'min_participants': self.min_participants
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VotingSession':
        return cls(
            session_id=data['session_id'],
            title=data['title'],
            description=data['description'],
            creator_id=data['creator_id'],
            options=[VoteOption.from_dict(opt) for opt in data['options']],
            start_time=data['start_time'],
            end_time=data['end_time'],
            eligible_voters=set(data['eligible_voters']),
            votes={vid: Vote.from_dict(vote) for vid, vote in data.get('votes', {}).items()},
            status=VoteStatus(data['status']),
            consensus_threshold=data.get('consensus_threshold', 0.5),
            min_participants=data.get('min_participants', 1)
        )

    def is_active(self) -> bool:
        """Check if voting session is currently active."""
        current_time = time.time()
        return (self.status == VoteStatus.ACTIVE and
                self.start_time <= current_time <= self.end_time)

    def can_vote(self, voter_id: str) -> bool:
        """Check if a voter can participate."""
        return (voter_id in self.eligible_voters and
                voter_id not in self.votes and
                self.is_active())

    def add_vote(self, vote: Vote) -> bool:
        """Add a vote to the session."""
        if not self.can_vote(vote.voter_id):
            return False

        self.votes[vote.voter_id] = vote
        logger.info(f"Vote added to session {self.session_id} by {vote.voter_id}")
        return True

    def get_vote_counts(self) -> Dict[str, int]:
        """Get vote counts for each option."""
        counts = {}
        for vote in self.votes.values():
            counts[vote.option_id] = counts.get(vote.option_id, 0) + 1
        return counts

    def get_consensus_result(self) -> ConsensusResult:
        """Calculate consensus result based on votes."""
        if not self.is_completed():
            return ConsensusResult.UNDECIDED

        vote_counts = self.get_vote_counts()
        total_votes = len(self.votes)
        total_eligible = len(self.eligible_voters)

        if total_votes < self.min_participants:
            return ConsensusResult.UNDECIDED

        # Find winning option
        max_votes = 0
        winning_option = None
        total_counted = 0

        for option_id, count in vote_counts.items():
            total_counted += count
            if count > max_votes:
                max_votes = count
                winning_option = option_id
            elif count == max_votes:
                # Tie
                return ConsensusResult.TIED

        if winning_option is None:
            return ConsensusResult.UNDECIDED

        # Check consensus threshold
        consensus_ratio = max_votes / total_counted
        if consensus_ratio >= self.consensus_threshold:
            return ConsensusResult.APPROVED
        else:
            return ConsensusResult.REJECTED

    def is_completed(self) -> bool:
        """Check if voting session is completed."""
        current_time = time.time()
        return (self.status == VoteStatus.COMPLETED or
                (self.status == VoteStatus.ACTIVE and current_time > self.end_time))

    def get_participation_rate(self) -> float:
        """Get current participation rate."""
        if not self.eligible_voters:
            return 0.0
        return len(self.votes) / len(self.eligible_voters)


class MeshVotingApp:
    """
    Offline Voting Application for Mesh Networks.

    Implements decentralized voting with majority-agreement consensus.
    Supports blockchain integration for vote validation and recording.
    """

    def __init__(self, node_id: str, mesh_network):
        self.node_id = node_id
        self.mesh_network = mesh_network  # Reference to mesh network for communication
        self.voting_sessions: Dict[str, VotingSession] = {}
        self.vote_handlers: Dict[str, Callable] = {}
        self.session_handlers: Dict[str, Callable] = {}

        # Blockchain integration
        self.blockchain_enabled = _HAS_BLOCKCHAIN
        self.polkadot_bridge = None
        self.message_recorder = None
        self.smart_contract_deployer = None

        # Initialize blockchain components if available
        if self.blockchain_enabled:
            self._initialize_blockchain()

        # Message types for mesh communication
        self.MESSAGE_VOTE_REQUEST = "vote_request"
        self.MESSAGE_VOTE_CAST = "vote_cast"
        self.MESSAGE_VOTE_SYNC = "vote_sync"
        self.MESSAGE_SESSION_UPDATE = "session_update"

        # Register message handlers
        self._register_message_handlers()

    def _initialize_blockchain(self):
        """Initialize blockchain components for vote validation."""
        try:
            # Initialize Polkadot bridge for cross-chain communication
            self.polkadot_bridge = PolkadotBridge(
                node_id=self.node_id,
                mesh_network=self.mesh_network
            )

            # Initialize message recorder for audit trails
            self.message_recorder = MeshMessageRecorder(
                bridge=self.polkadot_bridge,
                node_id=self.node_id
            )

            # Initialize smart contract deployer for vote validation
            # This would be configured with actual network credentials
            self.smart_contract_deployer = None  # Initialize when needed

            logger.info("Blockchain integration initialized for voting app")

        except Exception as e:
            logger.error(f"Failed to initialize blockchain components: {e}")
            self.blockchain_enabled = False

    def _register_message_handlers(self):
        """Register handlers for mesh network messages."""
        self.mesh_network.register_message_handler(self.MESSAGE_VOTE_REQUEST, self._handle_vote_request)
        self.mesh_network.register_message_handler(self.MESSAGE_VOTE_CAST, self._handle_vote_cast)
        self.mesh_network.register_message_handler(self.MESSAGE_VOTE_SYNC, self._handle_vote_sync)
        self.mesh_network.register_message_handler(self.MESSAGE_SESSION_UPDATE, self._handle_session_update)

    def register_vote_handler(self, event_type: str, handler: Callable):
        """Register handler for voting events."""
        self.vote_handlers[event_type] = handler

    def register_session_handler(self, event_type: str, handler: Callable):
        """Register handler for session events."""
        self.session_handlers[event_type] = handler

    async def create_voting_session(self, title: str, description: str, options: List[VoteOption],
                                   duration_minutes: int, eligible_voters: List[str],
                                   consensus_threshold: float = 0.5, min_participants: int = 1) -> str:
        """Create a new voting session."""
        session_id = f"vote_{self.node_id}_{int(time.time())}"

        session = VotingSession(
            session_id=session_id,
            title=title,
            description=description,
            creator_id=self.node_id,
            options=options,
            start_time=time.time(),
            end_time=time.time() + (duration_minutes * 60),
            eligible_voters=set(eligible_voters),
            votes={},
            status=VoteStatus.ACTIVE,
            consensus_threshold=consensus_threshold,
            min_participants=min_participants
        )

        self.voting_sessions[session_id] = session

        # Broadcast session creation to network
        await self._broadcast_session_update(session, "created")

        logger.info(f"Created voting session: {session_id}")
        return session_id

    async def cast_vote(self, session_id: str, option_id: str) -> bool:
        """Cast a vote in a voting session."""
        if session_id not in self.voting_sessions:
            logger.error(f"Session {session_id} not found")
            return False

        session = self.voting_sessions[session_id]

        if not session.can_vote(self.node_id):
            logger.error(f"Cannot vote in session {session_id}")
            return False

        # Create vote
        timestamp = time.time()
        vote = Vote(
            voter_id=self.node_id,
            option_id=option_id,
            timestamp=timestamp,
            signature=""  # Will set after creation
        )
        # Calculate signature after vote creation
        vote.signature = vote.calculate_hash()

        # Add vote locally
        if not session.add_vote(vote):
            return False

        # Broadcast vote to network
        await self._broadcast_vote_cast(session_id, vote)

        # Record vote on blockchain if enabled
        if self.blockchain_enabled and self.message_recorder:
            try:
                await self.message_recorder.record_vote(
                    session_id=session_id,
                    vote=vote,
                    session_metadata={
                        'title': session.title,
                        'creator_id': session.creator_id,
                        'total_options': len(session.options)
                    }
                )
                logger.info(f"Vote recorded on blockchain for session {session_id}")
            except Exception as e:
                logger.error(f"Failed to record vote on blockchain: {e}")

        # Check if consensus reached
        if session.get_consensus_result() != ConsensusResult.UNDECIDED:
            await self._finalize_session(session_id)

        # Call vote handler
        if "vote_cast" in self.vote_handlers:
            await self.vote_handlers["vote_cast"](session_id, vote)

        return True

    async def get_session_results(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get results for a voting session."""
        if session_id not in self.voting_sessions:
            return None

        session = self.voting_sessions[session_id]
        vote_counts = session.get_vote_counts()

        return {
            'session_id': session_id,
            'title': session.title,
            'status': session.status.value,
            'total_votes': len(session.votes),
            'participation_rate': session.get_participation_rate(),
            'vote_counts': vote_counts,
            'consensus_result': session.get_consensus_result().value,
            'eligible_voters': len(session.eligible_voters),
            'time_remaining': max(0, session.end_time - time.time())
        }

    async def sync_session(self, session_id: str):
        """Request synchronization of a session from network."""
        sync_request = {
            'session_id': session_id,
            'requester': self.node_id,
            'timestamp': time.time()
        }

        await self.mesh_network.broadcast_message(
            self.MESSAGE_VOTE_SYNC,
            json.dumps(sync_request).encode()
        )

    async def _broadcast_session_update(self, session: VotingSession, update_type: str):
        """Broadcast session update to network."""
        update_data = {
            'session': session.to_dict(),
            'update_type': update_type,
            'sender': self.node_id,
            'timestamp': time.time()
        }

        await self.mesh_network.broadcast_message(
            self.MESSAGE_SESSION_UPDATE,
            json.dumps(update_data).encode()
        )

    async def _broadcast_vote_cast(self, session_id: str, vote: Vote):
        """Broadcast vote cast to network."""
        vote_data = {
            'session_id': session_id,
            'vote': vote.to_dict(),
            'sender': self.node_id,
            'timestamp': time.time()
        }

        await self.mesh_network.broadcast_message(
            self.MESSAGE_VOTE_CAST,
            json.dumps(vote_data).encode()
        )

    async def _finalize_session(self, session_id: str):
        """Finalize a completed voting session."""
        if session_id in self.voting_sessions:
            session = self.voting_sessions[session_id]
            session.status = VoteStatus.COMPLETED

            # Broadcast finalization
            await self._broadcast_session_update(session, "completed")

            # Call session handler
            if "session_completed" in self.session_handlers:
                await self.session_handlers["session_completed"](session_id, session)

            logger.info(f"Finalized voting session: {session_id}")

    async def _handle_vote_request(self, sender_id: str, payload: bytes):
        """Handle vote request from network."""
        try:
            data = json.loads(payload.decode())
            session_id = data.get('session_id')

            if session_id in self.voting_sessions:
                session = self.voting_sessions[session_id]
                # Send session info back
                await self._broadcast_session_update(session, "info")

        except Exception as e:
            logger.error(f"Error handling vote request: {e}")

    async def _handle_vote_cast(self, sender_id: str, payload: bytes):
        """Handle vote cast from network."""
        try:
            data = json.loads(payload.decode())
            session_id = data.get('session_id')
            vote_data = data.get('vote')

            if session_id in self.voting_sessions:
                session = self.voting_sessions[session_id]
                vote = Vote.from_dict(vote_data)

                # Add vote if not already present
                if vote.voter_id not in session.votes:
                    session.add_vote(vote)

                    # Check consensus
                    if session.get_consensus_result() != ConsensusResult.UNDECIDED:
                        await self._finalize_session(session_id)

        except Exception as e:
            logger.error(f"Error handling vote cast: {e}")

    async def _handle_vote_sync(self, sender_id: str, payload: bytes):
        """Handle vote synchronization request."""
        try:
            data = json.loads(payload.decode())
            session_id = data.get('session_id')
            requester = data.get('requester')

            if session_id in self.voting_sessions and requester != self.node_id:
                session = self.voting_sessions[session_id]
                # Send current session state
                await self._broadcast_session_update(session, "sync")

        except Exception as e:
            logger.error(f"Error handling vote sync: {e}")

    async def _handle_session_update(self, sender_id: str, payload: bytes):
        """Handle session update from network."""
        try:
            data = json.loads(payload.decode())
            session_data = data.get('session')
            update_type = data.get('update_type')

            session = VotingSession.from_dict(session_data)
            session_id = session.session_id

            # Update local session if newer or not present
            if (session_id not in self.voting_sessions or
                session_data.get('timestamp', 0) > self.voting_sessions[session_id].start_time):
                self.voting_sessions[session_id] = session

                # Call session handler
                if update_type in self.session_handlers:
                    await self.session_handlers[update_type](session_id, session)

        except Exception as e:
            logger.error(f"Error handling session update: {e}")

    def get_active_sessions(self) -> List[str]:
        """Get list of active voting session IDs."""
        return [sid for sid, session in self.voting_sessions.items() if session.is_active()]

    def get_completed_sessions(self) -> List[str]:
        """Get list of completed voting session IDs."""
        return [sid for sid, session in self.voting_sessions.items() if session.is_completed()]

    def get_session_stats(self) -> Dict[str, Any]:
        """Get overall voting statistics."""
        active_sessions = len(self.get_active_sessions())
        completed_sessions = len(self.get_completed_sessions())
        total_votes = sum(len(session.votes) for session in self.voting_sessions.values())

        return {
            'total_sessions': len(self.voting_sessions),
            'active_sessions': active_sessions,
            'completed_sessions': completed_sessions,
            'total_votes': total_votes,
            'node_id': self.node_id
        }


class MeshVotingNetwork:
    """
    Mesh Voting Network coordinator.

    Manages multiple voting applications across the mesh network.
    """

    def __init__(self, mesh_network):
        self.mesh_network = mesh_network
        self.voting_apps: Dict[str, MeshVotingApp] = {}

    def add_voting_app(self, node_id: str) -> MeshVotingApp:
        """Add voting application for a node."""
        if node_id not in self.voting_apps:
            self.voting_apps[node_id] = MeshVotingApp(node_id, self.mesh_network)
        return self.voting_apps[node_id]

    async def create_network_vote(self, title: str, description: str, options: List[VoteOption],
                                 duration_minutes: int, consensus_threshold: float = 0.5) -> str:
        """Create a network-wide voting session."""
        # Get all known nodes from mesh network
        known_nodes = []  # This would come from mesh network discovery
        if hasattr(self.mesh_network, 'get_discovered_nodes'):
            known_nodes = [node.node_id for node in self.mesh_network.get_discovered_nodes()]

        if not known_nodes:
            known_nodes = [node_id for node_id in self.voting_apps.keys()]

        # Create session on all nodes
        session_ids = []
        for app in self.voting_apps.values():
            session_id = await app.create_voting_session(
                title, description, options, duration_minutes,
                known_nodes, consensus_threshold
            )
            session_ids.append(session_id)

        # Return primary session ID
        return session_ids[0] if session_ids else ""

    async def get_network_vote_results(self, session_id: str) -> Dict[str, Any]:
        """Get consolidated results from network vote."""
        all_results = {}
        consensus_results = []

        for app in self.voting_apps.values():
            results = await app.get_session_results(session_id)
            if results:
                all_results[app.node_id] = results
                consensus_results.append(results.get('consensus_result'))

        # Determine network consensus
        if consensus_results:
            approved_count = consensus_results.count('approved')
            rejected_count = consensus_results.count('rejected')
            tied_count = consensus_results.count('tied')

            if approved_count > rejected_count and approved_count > tied_count:
                network_consensus = 'approved'
            elif rejected_count > approved_count and rejected_count > tied_count:
                network_consensus = 'rejected'
            elif tied_count > approved_count and tied_count > rejected_count:
                network_consensus = 'tied'
            else:
                network_consensus = 'undecided'
        else:
            network_consensus = 'undecided'

        return {
            'session_id': session_id,
            'network_consensus': network_consensus,
            'node_results': all_results,
            'participating_nodes': len(all_results)
        }

    def get_network_stats(self) -> Dict[str, Any]:
        """Get network-wide voting statistics."""
        app_stats = [app.get_session_stats() for app in self.voting_apps.values()]

        total_sessions = sum(stats['total_sessions'] for stats in app_stats)
        total_votes = sum(stats['total_votes'] for stats in app_stats)

        return {
            'total_voting_apps': len(self.voting_apps),
            'total_sessions': total_sessions,
            'total_votes': total_votes,
            'app_stats': app_stats
        }
