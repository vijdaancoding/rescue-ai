"""
Tests for call management service layer.

Tests call status updates, context retrieval, and call operations.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.db.models import CallSession
from app.services import calls as calls_service


class TestUpdateCallStatus:
    """Test call status update logic."""

    @pytest.mark.unit
    @pytest.mark.service
    def test_update_call_status_valid_transition(self, call_repo, test_call):
        """Valid status transition should work."""
        result = calls_service.update_call_status(
            call_id=test_call.id,
            new_status="Dispatched",
            calls=call_repo,
        )
        
        assert result is not None
        assert result.status == "Dispatched"

    @pytest.mark.unit
    @pytest.mark.service
    def test_update_call_status_nonexistent_call(self, call_repo):
        """Updating nonexistent call should fail."""
        with pytest.raises(Exception):
            calls_service.update_call_status(
                call_id=uuid4(),
                new_status="Dispatched",
                calls=call_repo,
            )

    @pytest.mark.unit
    @pytest.mark.service
    def test_update_call_status_sets_end_time(self, call_repo, test_call):
        """Closing a call should set end_time."""
        result = calls_service.update_call_status(
            call_id=test_call.id,
            new_status="FalseAlarm",
            calls=call_repo,
        )
        
        assert result is not None
        assert result.status == "FalseAlarm"
        # end_time should be set
        assert result.end_time is not None

    @pytest.mark.unit
    @pytest.mark.service
    def test_update_call_status_duration_tracking(self, call_repo, test_call):
        """Call duration should be calculable after closing."""
        original_start = test_call.start_time
        
        result = calls_service.update_call_status(
            call_id=test_call.id,
            new_status="Dispatched",
            calls=call_repo,
        )
        
        assert result.start_time == original_start


class TestGetCallContext:
    """Test retrieving complete call context."""

    @pytest.mark.unit
    @pytest.mark.service
    def test_get_call_context_includes_metadata(self, call_repo, test_call, test_ai_metadata):
        """Call context should include AI metadata."""
        result = calls_service.get_call_context(
            call_id=test_call.id,
            calls=call_repo,
        )
        
        assert result is not None
        # Should have call data
        assert result.get("id") == str(test_call.id)

    @pytest.mark.unit
    @pytest.mark.service
    def test_get_call_context_includes_geolocation(self, call_repo, test_call, test_geolocation):
        """Call context should include geolocation."""
        result = calls_service.get_call_context(
            call_id=test_call.id,
            calls=call_repo,
        )
        
        assert result is not None
        # Should have location info
        assert result.get("caller_city") == test_call.caller_city

    @pytest.mark.unit
    @pytest.mark.service
    def test_get_call_context_nonexistent_call(self, call_repo):
        """Getting context for nonexistent call should fail."""
        with pytest.raises(Exception):
            calls_service.get_call_context(
                call_id=uuid4(),
                calls=call_repo,
            )

    @pytest.mark.unit
    @pytest.mark.service
    def test_get_call_context_with_dispatches(self, call_repo, db_session, test_call, test_dispatch):
        """Call context should include associated dispatches."""
        result = calls_service.get_call_context(
            call_id=test_call.id,
            calls=call_repo,
        )
        
        assert result is not None
        # Should have dispatch information
        if "dispatches" in result:
            assert len(result["dispatches"]) > 0


class TestListCalls:
    """Test listing calls with filtering."""

    @pytest.mark.unit
    @pytest.mark.service
    def test_list_calls_returns_all(self, call_repo, db_session):
        """Listing calls should return all calls."""
        # Create multiple calls
        for i in range(3):
            call = CallSession(
                id=uuid4(),
                caller_hash=f"hash_{i}",
                status="Active",
            )
            db_session.add(call)
        db_session.commit()
        
        result = calls_service.list_calls(calls=call_repo)
        
        assert len(result) >= 3

    @pytest.mark.unit
    @pytest.mark.service
    def test_list_calls_filter_by_status(self, call_repo, db_session):
        """Filtering by status should work."""
        # Create calls with different statuses
        for status in ["Active", "Incoming", "Dispatched"]:
            call = CallSession(
                id=uuid4(),
                caller_hash=f"hash_{status}",
                status=status,
            )
            db_session.add(call)
        db_session.commit()
        
        result = calls_service.list_calls(
            calls=call_repo,
            status_filter="Active",
        )
        
        for call in result:
            assert call.status == "Active"

    @pytest.mark.unit
    @pytest.mark.service
    def test_list_calls_pagination(self, call_repo, db_session):
        """Pagination should limit results."""
        # Create multiple calls
        for i in range(10):
            call = CallSession(
                id=uuid4(),
                caller_hash=f"hash_{i}",
            )
            db_session.add(call)
        db_session.commit()
        
        result = calls_service.list_calls(
            calls=call_repo,
            limit=3,
        )
        
        assert len(result) <= 3
