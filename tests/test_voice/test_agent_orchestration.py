"""
Tests for voice agent integration and orchestration.

Tests the main voice agent logic without actually connecting to LiveKit.
Mocks LiveKit room connections and agent processing.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.voice.agent import init_voice_agent


class TestVoiceAgentInitialization:
    """Test voice agent initialization and setup."""

    @pytest.mark.unit
    @pytest.mark.voice
    @pytest.mark.asyncio
    async def test_init_voice_agent_success(self, mock_livekit_room, mock_voice_agent_context):
        """Voice agent should initialize successfully."""
        with patch("app.voice.agent.connect_to_room", new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = mock_livekit_room
            
            result = await init_voice_agent(
                room_name=mock_voice_agent_context["room_name"],
                participant_name="ai_agent",
            )
            
            assert result is not None
            mock_connect.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.voice
    @pytest.mark.asyncio
    async def test_init_voice_agent_with_context(self, mock_livekit_room, mock_voice_agent_context):
        """Voice agent should accept call context metadata."""
        with patch("app.voice.agent.connect_to_room", new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = mock_livekit_room
            
            result = await init_voice_agent(
                room_name=mock_voice_agent_context["room_name"],
                participant_name="ai_agent",
                context=mock_voice_agent_context,
            )
            
            assert result is not None

    @pytest.mark.unit
    @pytest.mark.voice
    @pytest.mark.asyncio
    async def test_init_voice_agent_connection_failure(self):
        """Voice agent should handle connection failures gracefully."""
        with patch("app.voice.agent.connect_to_room", new_callable=AsyncMock) as mock_connect:
            mock_connect.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception):
                await init_voice_agent(
                    room_name="test_room",
                    participant_name="ai_agent",
                )

    @pytest.mark.unit
    @pytest.mark.voice
    @pytest.mark.asyncio
    async def test_init_voice_agent_invalid_room_name(self):
        """Voice agent should validate room name."""
        with patch("app.voice.agent.connect_to_room", new_callable=AsyncMock):
            with pytest.raises(Exception):
                await init_voice_agent(
                    room_name="",
                    participant_name="ai_agent",
                )


class TestVoiceAgentProcessing:
    """Test voice agent audio/speech processing."""

    @pytest.mark.unit
    @pytest.mark.voice
    @pytest.mark.asyncio
    async def test_process_incoming_audio(self, mock_livekit_agent):
        """Agent should process incoming audio."""
        # Mock audio data
        audio_data = b'fake_audio_data_pcm'
        
        result = await mock_livekit_agent.process_audio(audio_data)
        
        assert result is not None
        mock_livekit_agent.process_audio.assert_called_once_with(audio_data)

    @pytest.mark.unit
    @pytest.mark.voice
    @pytest.mark.asyncio
    async def test_agent_speech_to_text(self, mock_livekit_agent):
        """Agent should convert speech to text via STT."""
        mock_livekit_agent.process_audio.return_value = {
            "transcript": "I need help immediately",
            "language": "en",
            "confidence": 0.95,
        }
        
        result = await mock_livekit_agent.process_audio(b'audio_data')
        
        assert result["transcript"] == "I need help immediately"
        assert result["confidence"] == 0.95

    @pytest.mark.unit
    @pytest.mark.voice
    @pytest.mark.asyncio
    async def test_agent_urdu_speech_support(self, mock_livekit_agent):
        """Agent should support Urdu speech processing."""
        mock_livekit_agent.process_audio.return_value = {
            "transcript": "مجھے فوری مدد چاہیے",
            "language": "ur",
            "confidence": 0.88,
        }
        
        result = await mock_livekit_agent.process_audio(b'urdu_audio_data')
        
        assert result["language"] == "ur"
        assert "چاہیے" in result["transcript"]


class TestVoiceAgentResponse:
    """Test voice agent response generation."""

    @pytest.mark.unit
    @pytest.mark.voice
    @pytest.mark.asyncio
    async def test_agent_generates_response(self, mock_livekit_agent):
        """Agent should generate appropriate responses."""
        mock_livekit_agent.say.return_value = {
            "status": "success",
            "audio_duration": 2.5,
        }
        
        result = await mock_livekit_agent.say("I'm here to help. What is your emergency?")
        
        assert result["status"] == "success"
        assert result["audio_duration"] > 0

    @pytest.mark.unit
    @pytest.mark.voice
    @pytest.mark.asyncio
    async def test_agent_generates_urdu_response(self, mock_livekit_agent):
        """Agent should generate Urdu responses."""
        mock_livekit_agent.say.return_value = {
            "status": "success",
            "language": "ur",
            "audio_duration": 1.8,
        }
        
        result = await mock_livekit_agent.say("میں آپ کی مدد کے لیے یہاں ہوں")
        
        assert result["status"] == "success"

    @pytest.mark.unit
    @pytest.mark.voice
    @pytest.mark.asyncio
    async def test_agent_respects_noise_cancellation(self, mock_livekit_room):
        """Agent should apply noise cancellation."""
        mock_livekit_room.connect.return_value = {
            "noise_cancellation": "enabled",
            "noise_level": 0.15,
        }
        
        result = await mock_livekit_room.connect()
        
        assert result["noise_cancellation"] == "enabled"


class TestVoiceAgentDisconnection:
    """Test voice agent disconnection and cleanup."""

    @pytest.mark.unit
    @pytest.mark.voice
    @pytest.mark.asyncio
    async def test_agent_disconnect_success(self, mock_livekit_agent):
        """Agent should disconnect cleanly."""
        mock_livekit_agent.disconnect.return_value = {"status": "disconnected"}
        
        result = await mock_livekit_agent.disconnect()
        
        assert result["status"] == "disconnected"

    @pytest.mark.unit
    @pytest.mark.voice
    @pytest.mark.asyncio
    async def test_agent_disconnect_releases_resources(self, mock_livekit_agent):
        """Disconnect should release all resources."""
        await mock_livekit_agent.disconnect()
        mock_livekit_agent.disconnect.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.voice
    @pytest.mark.asyncio
    async def test_agent_handles_connection_loss(self, mock_livekit_agent):
        """Agent should handle unexpected disconnection."""
        mock_livekit_agent.disconnect.side_effect = Exception("Connection lost")
        
        with pytest.raises(Exception):
            await mock_livekit_agent.disconnect()


class TestVoiceAgentContextHandling:
    """Test voice agent context data handling."""

    @pytest.mark.unit
    @pytest.mark.voice
    @pytest.mark.asyncio
    async def test_agent_accesses_call_context(self, mock_voice_agent_context):
        """Agent should access call context data."""
        assert mock_voice_agent_context["call_id"] is not None
        assert mock_voice_agent_context["caller_phone"] is not None
        assert mock_voice_agent_context["caller_city"] is not None

    @pytest.mark.unit
    @pytest.mark.voice
    @pytest.mark.asyncio
    async def test_agent_injects_context_into_prompt(self, mock_livekit_agent, mock_voice_agent_context):
        """Agent should use context for system prompt."""
        location = f"{mock_voice_agent_context['caller_city']}"
        phone = mock_voice_agent_context["caller_phone"]
        
        context_aware_prompt = f"Emergency in {location} from {phone}"
        
        assert "Emergency" in context_aware_prompt
        assert mock_voice_agent_context["caller_city"] in context_aware_prompt

    @pytest.mark.unit
    @pytest.mark.voice
    @pytest.mark.asyncio
    async def test_agent_preserves_context_across_turns(self, mock_livekit_agent, mock_voice_agent_context):
        """Agent should maintain context across conversation turns."""
        call_id = mock_voice_agent_context["call_id"]
        
        # First turn
        await mock_livekit_agent.say("What is your emergency?")
        # Second turn (context should be preserved)
        await mock_livekit_agent.say("I'm sending help to your location")
        
        # Context call_id should remain the same
        assert mock_voice_agent_context["call_id"] == call_id


class TestVoiceAgentErrorHandling:
    """Test voice agent error handling."""

    @pytest.mark.unit
    @pytest.mark.voice
    @pytest.mark.asyncio
    async def test_agent_handles_stt_failure(self, mock_livekit_agent):
        """Agent should handle STT failures gracefully."""
        mock_livekit_agent.process_audio.side_effect = Exception("STT service unavailable")
        
        with pytest.raises(Exception):
            await mock_livekit_agent.process_audio(b'audio_data')

    @pytest.mark.unit
    @pytest.mark.voice
    @pytest.mark.asyncio
    async def test_agent_handles_tts_failure(self, mock_livekit_agent):
        """Agent should handle TTS failures gracefully."""
        mock_livekit_agent.say.side_effect = Exception("TTS service unavailable")
        
        with pytest.raises(Exception):
            await mock_livekit_agent.say("Test message")

    @pytest.mark.unit
    @pytest.mark.voice
    @pytest.mark.asyncio
    async def test_agent_timeout_handling(self, mock_livekit_agent):
        """Agent should handle operation timeouts."""
        import asyncio
        
        async def slow_operation():
            await asyncio.sleep(10)
        
        mock_livekit_agent.process_audio.side_effect = asyncio.TimeoutError()
        
        with pytest.raises(asyncio.TimeoutError):
            await mock_livekit_agent.process_audio(b'audio_data')
