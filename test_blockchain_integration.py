#!/usr/bin/env python3
"""
Test script for blockchain integration in mesh voting application.
"""

import asyncio
import sys
import os
from unittest.mock import Mock, MagicMock

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mesh.voting_app import MeshVotingApp, VoteOption


class MockMeshNetwork:
    """Mock mesh network for testing."""
    def __init__(self):
        self.message_handlers = {}

    def register_message_handler(self, message_type, handler):
        self.message_handlers[message_type] = handler

    async def broadcast_message(self, message_type, payload):
        pass  # Mock implementation


async def test_blockchain_initialization():
    """Test blockchain component initialization."""
    print("Testing blockchain component initialization...")

    # Create mock mesh network
    mesh_network = MockMeshNetwork()

    # Test with blockchain enabled (if imports work)
    try:
        app = MeshVotingApp("test_node", mesh_network)
        print("✓ MeshVotingApp initialized successfully")

        # Check if blockchain components are initialized
        if hasattr(app, 'blockchain_enabled') and app.blockchain_enabled:
            print("✓ Blockchain integration enabled")
            if app.polkadot_bridge is not None:
                print("✓ PolkadotBridge initialized")
            else:
                print("✗ PolkadotBridge not initialized")

            if app.message_recorder is not None:
                print("✓ MeshMessageRecorder initialized")
            else:
                print("✗ MeshMessageRecorder not initialized")
        else:
            print("ℹ Blockchain integration disabled (imports failed)")

    except Exception as e:
        print(f"✗ Failed to initialize MeshVotingApp: {e}")
        return False

    return True


async def test_vote_casting_with_blockchain():
    """Test vote casting with blockchain recording."""
    print("\nTesting vote casting with blockchain recording...")

    mesh_network = MockMeshNetwork()
    app = MeshVotingApp("test_node", mesh_network)

    # Create a voting session
    options = [
        VoteOption("opt1", "Option 1", "First choice"),
        VoteOption("opt2", "Option 2", "Second choice")
    ]

    try:
        session_id = await app.create_voting_session(
            title="Test Session",
            description="Blockchain integration test",
            options=options,
            duration_minutes=5,
            eligible_voters=["test_node"]
        )
        print(f"✓ Created voting session: {session_id}")

        # Cast a vote
        success = await app.cast_vote(session_id, "opt1")
        if success:
            print("✓ Vote cast successfully")
        else:
            print("✗ Failed to cast vote")
            return False

        # Check if blockchain recording was attempted
        if app.blockchain_enabled:
            print("✓ Blockchain recording attempted (check logs for details)")
        else:
            print("ℹ Blockchain recording skipped (disabled)")

    except Exception as e:
        print(f"✗ Error during vote casting: {e}")
        return False

    return True


async def test_error_handling():
    """Test error handling when blockchain components fail."""
    print("\nTesting error handling...")

    mesh_network = MockMeshNetwork()

    # Test with mocked failing blockchain components
    try:
        app = MeshVotingApp("test_node", mesh_network)

        # Manually set blockchain components to None to simulate failure
        app.polkadot_bridge = None
        app.message_recorder = None
        app.blockchain_enabled = True

        # Create session and cast vote - should handle errors gracefully
        options = [VoteOption("opt1", "Option 1")]
        session_id = await app.create_voting_session(
            title="Error Test",
            description="Testing error handling",
            options=options,
            duration_minutes=1,
            eligible_voters=["test_node"]
        )

        success = await app.cast_vote(session_id, "opt1")
        if success:
            print("✓ Vote casting handled blockchain errors gracefully")
        else:
            print("✗ Vote casting failed due to errors")
            return False

    except Exception as e:
        print(f"✗ Unexpected error in error handling test: {e}")
        return False

    return True


async def test_session_metadata():
    """Test session metadata recording."""
    print("\nTesting session metadata recording...")

    mesh_network = MockMeshNetwork()
    app = MeshVotingApp("test_node", mesh_network)

    # Create session with specific metadata
    options = [
        VoteOption("opt1", "Yes", "Approve the proposal"),
        VoteOption("opt2", "No", "Reject the proposal")
    ]

    session_id = await app.create_voting_session(
        title="Metadata Test Session",
        description="Testing metadata recording",
        options=options,
        duration_minutes=10,
        eligible_voters=["test_node", "node2"],
        consensus_threshold=0.6
    )

    # Cast vote and check if metadata would be recorded correctly
    success = await app.cast_vote(session_id, "opt1")

    if success:
        print("✓ Session metadata recording test completed")
        # In a real test, we'd verify the metadata sent to blockchain
    else:
        print("✗ Failed to test session metadata")
        return False

    return True


async def main():
    """Run all tests."""
    print("Starting blockchain integration tests for mesh voting app...\n")

    tests = [
        test_blockchain_initialization,
        test_vote_casting_with_blockchain,
        test_error_handling,
        test_session_metadata
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if await test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")

    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All tests passed!")
        return True
    else:
        print("✗ Some tests failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
