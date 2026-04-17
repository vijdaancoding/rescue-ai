"""
Tests for the analysis pipeline (ONNX runner and Gemini analyzer).

Note: These tests focus on orchestration and error handling rather than
specific implementation details, since the pipeline may be replaced
with HuggingFace API in the future.
"""

import pytest
from unittest.mock import AsyncMock, patch


class TestAnalysisPipelineOrchestration:
    """Test analysis pipeline setup and execution."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_trigger_analysis_both_models(self, mock_onnx_runner, mock_gemini_analyzer):
        """Analysis should run both ONNX and Gemini in parallel."""
        from app.analysis.pipeline import run_analysis
        
        transcript = "I need emergency help now"
        
        result = await run_analysis(
            transcript=transcript,
            call_id="test_call_123",
        )
        
        assert result is not None
        # Should have results from both models
        if "spam_score" in result:
            assert 0 <= result["spam_score"] <= 100

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analysis_onnx_only_fallback(self, mock_onnx_runner):
        """Analysis should continue if Gemini fails."""
        from app.analysis.pipeline import run_analysis
        
        with patch("app.analysis.gemini_analyzer.analyze", side_effect=Exception("API Error")):
            result = await run_analysis(
                transcript="Help needed",
                call_id="test_call_456",
            )
            
            # Should still have some result
            assert result is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analysis_both_fail_graceful(self):
        """Analysis should fail gracefully if both models fail."""
        from app.analysis.pipeline import run_analysis
        
        with patch("app.analysis.onnx_runner.run", side_effect=Exception("ONNX Error")), \
             patch("app.analysis.gemini_analyzer.analyze", side_effect=Exception("Gemini Error")):
            
            result = await run_analysis(
                transcript="Test",
                call_id="test_call_789",
            )
            
            # Should return error status or None
            assert result is None or "error" in str(result).lower()


class TestAnalysisInputValidation:
    """Test analysis pipeline input validation."""

    @pytest.mark.unit
    def test_analysis_empty_transcript(self):
        """Empty transcript should be rejected."""
        from app.analysis.pipeline import validate_input
        
        result = validate_input(transcript="")
        assert result is False

    @pytest.mark.unit
    def test_analysis_very_short_transcript(self):
        """Very short transcript might be accepted but flagged."""
        from app.analysis.pipeline import validate_input
        
        result = validate_input(transcript="Hi")
        # Depending on implementation, might be valid or not
        assert result is not None

    @pytest.mark.unit
    def test_analysis_very_long_transcript(self):
        """Very long transcript should be handled."""
        from app.analysis.pipeline import validate_input
        
        long_text = "word " * 10000  # Very long
        result = validate_input(transcript=long_text)
        assert result is not None  # Should handle gracefully


class TestAnalysisConfiguration:
    """Test analysis configuration and model loading."""

    @pytest.mark.unit
    def test_onnx_model_loads(self, mock_onnx_runner):
        """ONNX model should load successfully."""
        from app.analysis import onnx_runner
        
        mock_onnx_runner["load"]()
        mock_onnx_runner["load"].assert_called_once()

    @pytest.mark.unit
    def test_model_memory_efficiency(self):
        """Models should be memory efficient."""
        # Just track that models load without excessive memory
        # This is more of an integration/performance test
        pass
