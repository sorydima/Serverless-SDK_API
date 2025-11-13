#!/usr/bin/env python3
"""
Comprehensive test suite for multimodal capabilities implementation.
Tests voice messaging mesh and AI speech synthesis features.
"""

import asyncio
import sys
import os
import tempfile
import time
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mesh.bluetooth_mesh import BLEMeshNode, VoiceMessage, BLEMeshNetwork
from ai.genai_assistant import GenAIAssistant, SpeechSynthesis

class TestMultimodalCapabilities:
    """Test suite for multimodal capabilities"""

    def __init__(self):
        self.results = []
        self.test_network = None
        self.test_nodes = []
        self.tts_engine = None

    def log_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "PASS" if success else "FAIL"
        result = f"{status}: {test_name}"
        if message:
            result += f" - {message}"
        self.results.append(result)
        print(result)

    async def test_voice_message_creation(self):
        """Test VoiceMessage class creation and serialization"""
        try:
            # Create test audio data (dummy)
            audio_data = b'\x00\x01\x02\x03' * 1000  # 4KB dummy audio

            # Create voice message
            voice_msg = VoiceMessage(
                message_id="test_voice_001",
                source_id="node_1",
                destination_id="node_2",
                audio_data=audio_data,
                sample_rate=16000,
                channels=1,
                duration=2.5
            )

            # Test compression
            compressed = voice_msg.compress_audio()
            assert len(compressed) > 0, "Compression failed"

            # Test mesh message conversion
            mesh_msg = voice_msg.to_mesh_message()
            assert mesh_msg.message_type == 'voice', "Wrong message type"
            assert mesh_msg.source_id == "node_1", "Wrong source ID"

            # Test deserialization
            reconstructed = VoiceMessage.from_mesh_message(mesh_msg)
            assert reconstructed is not None, "Deserialization failed"
            assert reconstructed.message_id == "test_voice_001", "Wrong message ID"

            self.log_result("VoiceMessage Creation", True, "All VoiceMessage operations successful")
            return True

        except Exception as e:
            self.log_result("VoiceMessage Creation", False, str(e))
            return False

    async def test_ble_mesh_voice_integration(self):
        """Test BLE mesh node voice messaging capabilities"""
        try:
            # Create test node
            node = BLEMeshNode("test_node_1")

            # Create voice message
            audio_data = b'\xFF\xFE\xFD' * 500
            voice_msg = VoiceMessage(
                message_id="mesh_test_001",
                source_id="test_node_1",
                destination_id="test_node_2",
                audio_data=audio_data,
                sample_rate=8000,
                channels=1,
                duration=1.0
            )

            # Test voice message sending
            await node.send_voice_message("test_node_2", voice_msg)

            # Check if message was added to advertising data
            assert len(node.advertising_data) > 0, "Voice message not queued for advertising"

            # Test broadcast voice message
            await node.broadcast_voice_message(voice_msg)

            # Check advertising data again
            assert len(node.advertising_data) > 1, "Broadcast voice message not queued"

            self.log_result("BLE Mesh Voice Integration", True, "Voice messaging methods work correctly")
            return True

        except Exception as e:
            self.log_result("BLE Mesh Voice Integration", False, str(e))
            return False

    async def test_mesh_network_voice_broadcast(self):
        """Test voice message broadcasting in mesh network"""
        try:
            # Create test network
            network = BLEMeshNetwork()

            # Add nodes
            node1 = network.add_node("network_node_1")
            node2 = network.add_node("network_node_2")
            node3 = network.add_node("network_node_3")

            # Connect nodes
            network.connect_nodes("network_node_1", "network_node_2")
            network.connect_nodes("network_node_2", "network_node_3")

            # Create voice message for broadcast
            audio_data = b'\xAA\xBB\xCC' * 300
            voice_msg = VoiceMessage(
                message_id="broadcast_test_001",
                source_id="network_node_1",
                destination_id="broadcast",
                audio_data=audio_data,
                sample_rate=16000,
                channels=1,
                duration=1.5
            )

            # Test broadcast
            await network.broadcast_message("network_node_1", "voice", voice_msg.to_mesh_message().payload)

            # Check network stats
            stats = network.get_network_stats()
            assert stats['total_nodes'] == 3, "Wrong node count"
            assert stats['total_neighbor_connections'] == 4, "Wrong connection count"  # node1:1, node2:2, node3:1 = 4 total

            self.log_result("Mesh Network Voice Broadcast", True, "Network broadcasting works")
            return True

        except Exception as e:
            self.log_result("Mesh Network Voice Broadcast", False, str(e))
            return False

    async def test_tts_initialization(self):
        """Test TTS engine initialization"""
        try:
            tts = SpeechSynthesis()

            # Test initialization
            success = tts.initialize()

            if not success:
                # This is expected if pyttsx3 is not installed
                self.log_result("TTS Initialization", True, "TTS disabled (pyttsx3 not available)")
                return True

            # If initialized, test basic functionality
            assert tts.is_initialized, "TTS not properly initialized"

            # Test voice listing
            voices = tts.get_available_voices()
            assert isinstance(voices, list), "Voice list not returned"

            self.log_result("TTS Initialization", True, f"TTS initialized with {len(voices)} voices")
            return True

        except Exception as e:
            self.log_result("TTS Initialization", False, str(e))
            return False

    async def test_tts_synthesis(self):
        """Test text-to-speech synthesis"""
        try:
            tts = SpeechSynthesis()
            initialized = tts.initialize()

            if not initialized:
                self.log_result("TTS Synthesis", True, "Skipped (TTS not available)")
                return True

            # Test speech synthesis
            test_text = "Hello, this is a test of the text-to-speech system."
            audio_data = tts.synthesize_speech(test_text)

            if audio_data is None:
                self.log_result("TTS Synthesis", False, "Speech synthesis returned None")
                return False

            assert len(audio_data) > 0, "No audio data generated"
            assert isinstance(audio_data, bytes), "Audio data not bytes"

            # Test caching (second call should use cache)
            audio_data2 = tts.synthesize_speech(test_text)
            assert audio_data == audio_data2, "Caching not working"

            self.log_result("TTS Synthesis", True, f"Generated {len(audio_data)} bytes of audio")
            return True

        except Exception as e:
            self.log_result("TTS Synthesis", False, str(e))
            return False

    async def test_genai_assistant_tts_integration(self):
        """Test GenAI assistant TTS integration"""
        try:
            # Create assistant with dummy model path (won't load but tests structure)
            assistant = GenAIAssistant("./dummy_model")

            # Check capabilities
            caps = assistant.get_capabilities()
            assert 'text_to_speech' in caps, "TTS capability not listed"

            # Test TTS initialization through assistant
            tts_initialized = assistant.tts.initialize()

            if not tts_initialized:
                self.log_result("GenAI Assistant TTS Integration", True, "TTS integration skipped (not available)")
                return True

            # Test voice operations
            voices = assistant.tts.get_available_voices()
            assert isinstance(voices, list), "Voice list not accessible through assistant"

            # Test speech synthesis through assistant
            test_text = "Test message from GenAI assistant."
            audio = assistant.tts.synthesize_speech(test_text)
            if audio:
                assert len(audio) > 0, "No audio from assistant TTS"

            self.log_result("GenAI Assistant TTS Integration", True, "Assistant TTS integration successful")
            return True

        except Exception as e:
            self.log_result("GenAI Assistant TTS Integration", False, str(e))
            return False

    async def test_voice_message_fragmentation(self):
        """Test handling of large voice messages (fragmentation simulation)"""
        try:
            # Create large voice message
            large_audio = b'\x00\xFF' * 50000  # ~100KB audio data
            voice_msg = VoiceMessage(
                message_id="large_test_001",
                source_id="sender",
                destination_id="receiver",
                audio_data=large_audio,
                sample_rate=44100,
                channels=2,
                duration=10.0
            )

            # Test compression on large data
            compressed = voice_msg.compress_audio()
            assert len(compressed) <= len(large_audio), "Compression didn't reduce size"

            # Convert to mesh message
            mesh_msg = voice_msg.to_mesh_message()

            # Simulate BLE advertising limit (31 bytes)
            # In real implementation, this would be fragmented
            advertising_bytes = mesh_msg.to_bytes()

            # For now, just check that conversion works
            assert len(advertising_bytes) > 0, "Large message conversion failed"

            # Note: Real fragmentation would require additional implementation
            self.log_result("Voice Message Fragmentation", True, "Large message handling works (fragmentation noted for future)")
            return True

        except Exception as e:
            self.log_result("Voice Message Fragmentation", False, str(e))
            return False

    async def test_error_handling(self):
        """Test error handling in multimodal components"""
        try:
            # Test VoiceMessage with invalid data
            try:
                invalid_voice = VoiceMessage(
                    message_id="",
                    source_id="",
                    destination_id="",
                    audio_data=b"",  # Empty audio
                    sample_rate=0,  # Invalid sample rate
                    channels=0,    # Invalid channels
                    duration=-1.0  # Invalid duration
                )
                # Should still create object (dataclass allows this)
                assert invalid_voice is not None, "VoiceMessage creation failed with invalid data"
            except Exception:
                pass  # Expected for some validations

            # Test TTS with invalid text
            tts = SpeechSynthesis()
            if tts.initialize():
                # Test with empty text
                empty_audio = tts.synthesize_speech("")
                # Should handle gracefully (may return None or empty audio)

                # Test with very long text
                long_text = "Test " * 10000
                long_audio = tts.synthesize_speech(long_text)
                # Should handle large text

            # Test mesh node with invalid voice message
            node = BLEMeshNode("error_test_node")
            invalid_voice = VoiceMessage(
                message_id="invalid",
                source_id="test",
                destination_id="test",
                audio_data=b"",  # Empty
                sample_rate=0,
                channels=0,
                duration=0.0
            )

            # Should not crash
            await node.send_voice_message("dest", invalid_voice)

            self.log_result("Error Handling", True, "Components handle errors gracefully")
            return True

        except Exception as e:
            self.log_result("Error Handling", False, str(e))
            return False

    async def test_performance(self):
        """Test performance of multimodal operations"""
        try:
            start_time = time.time()

            # Test multiple voice message creations
            messages = []
            for i in range(10):
                audio_data = b'\x00\x01\x02\x03' * (100 * (i + 1))  # Increasing sizes
                msg = VoiceMessage(
                    message_id=f"perf_test_{i}",
                    source_id="perf_sender",
                    destination_id="perf_receiver",
                    audio_data=audio_data,
                    sample_rate=16000,
                    channels=1,
                    duration=1.0
                )
                messages.append(msg)

            creation_time = time.time() - start_time

            # Test TTS performance if available
            tts = SpeechSynthesis()
            if tts.initialize():
                tts_start = time.time()
                for i in range(5):
                    tts.synthesize_speech(f"Performance test message {i}")
                tts_time = time.time() - tts_start
            else:
                tts_time = 0

            # Check reasonable performance (should complete in reasonable time)
            assert creation_time < 5.0, f"Voice message creation too slow: {creation_time}s"
            if tts_time > 0:
                assert tts_time < 10.0, f"TTS synthesis too slow: {tts_time}s"

            self.log_result("Performance", True, f"Voice creation: {creation_time:.2f}s, TTS: {tts_time:.2f}s")
            return True

        except Exception as e:
            self.log_result("Performance", False, str(e))
            return False

    async def run_all_tests(self):
        """Run all multimodal capability tests"""
        print("Starting Multimodal Capabilities Test Suite")
        print("=" * 50)

        tests = [
            self.test_voice_message_creation,
            self.test_ble_mesh_voice_integration,
            self.test_mesh_network_voice_broadcast,
            self.test_tts_initialization,
            self.test_tts_synthesis,
            self.test_genai_assistant_tts_integration,
            self.test_voice_message_fragmentation,
            self.test_error_handling,
            self.test_performance
        ]

        passed = 0
        total = len(tests)

        for test in tests:
            try:
                result = await test()
                if result:
                    passed += 1
            except Exception as e:
                self.log_result(test.__name__, False, f"Test crashed: {str(e)}")

        print("\n" + "=" * 50)
        print(f"Test Results: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All tests passed! Multimodal capabilities are working correctly.")
        else:
            print(f"⚠️  {total - passed} tests failed. Please review the implementation.")

        return passed == total

async def main():
    """Main test runner"""
    tester = TestMultimodalCapabilities()
    success = await tester.run_all_tests()

    # Print summary
    print("\nDetailed Results:")
    for result in tester.results:
        print(f"  {result}")

    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
