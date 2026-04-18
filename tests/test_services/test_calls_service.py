"""
Tests for call management service layer.

Tests call status updates, context retrieval, and call operations.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.db.models import CallSession
from app.schemas.calls import CallFilters
from app.services import calls as calls_service


class TestUpdateCallStatus:
    """Test call status update logic."""

    @pytest.mark.unit
    @pytest.mark.service
    def test_update_call_status_valid_transition(self, call_repo, test_call):
        """Valid status transition should work."""
        result = calls_service.update_status(
            str(test_call.id),
            "Dispatched",
            calls=call_repo,
        )

        assert result is not None
        assert result["status"] == "Dispatched"

    @pytest.mark.unit
    @pytest.mark.service
    def test_update_call_status_nonexistent_call(self, call_repo):
        """Updating nonexistent call should fail."""
        with pytest.raises(Exception):
            calls_service.update_status(
                str(uuid4()),
                "Dispatched",
                calls=call_repo,
            )

    @pytest.mark.unit
    @pytest.mark.service
    def test_update_call_status_sets_end_time(self, call_repo, test_call):
        """Closing a call should set end_time."""
        calls_service.update_status(
            str(test_call.id),
            "FalseAlarm",
            calls=call_repo,
        )

        updated = call_repo.get(test_call.id)
        assert updated is not None
        assert updated.status == "FalseAlarm"
        assert updated.end_time is not None

    @pytest.mark.unit
    @pytest.mark.service
    def test_update_call_status_duration_tracking(self, call_repo, test_call):
        """Call duration should be calculable after closing."""
        original_start = test_call.start_time

        calls_service.update_status(
            str(test_call.id),
            "Dispatched",
            calls=call_repo,
        )

        updated = call_repo.get(test_call.id)
        assert updated.start_time == original_start


class TestGetCallContext:
    """Test retrieving complete call context."""

    @pytest.mark.unit
    @pytest.mark.service
    def test_get_call_context_includes_metadata(self, call_repo, geolocation_repo, test_call, test_ai_metadata):
        """Call context should return call data for a known room."""
        result = calls_service.get_context(
            test_call.room_name,
            calls=call_repo,
            geolocation=geolocation_repo,
        )

        assert result is not None
        assert result.call_id == str(test_call.id)

    @pytest.mark.unit
    @pytest.mark.service
    def test_get_call_context_includes_geolocation(self, call_repo, geolocation_repo, test_call, test_geolocation):
        """Call context should reflect geolocation when present."""
        result = calls_service.get_context(
            test_call.room_name,
            calls=call_repo,
            geolocation=geolocation_repo,
        )

        assert result is not None
        assert result.has_location is True

    @pytest.mark.unit
    @pytest.mark.service
    def test_get_call_context_nonexistent_call(self, call_repo, geolocation_repo):
        """Getting context for unknown room should return no-location result."""
        result = calls_service.get_context(
            "nonexistent_room",
            calls=call_repo,
            geolocation=geolocation_repo,
        )

        assert result is not None
        assert result.has_location is False

    @pytest.mark.unit
    @pytest.mark.service
    def test_get_call_context_with_dispatches(self, call_repo, geolocation_repo, test_call, test_dispatch):
        """Call context should be returned even when dispatches exist."""
        result = calls_service.get_context(
            test_call.room_name,
            calls=call_repo,
            geolocation=geolocation_repo,
        )

        assert result is not None
        assert result.call_id == str(test_call.id)


class TestListCalls:
    """Test listing calls with filtering."""

    @pytest.mark.unit
    @pytest.mark.service
    def test_list_calls_returns_all(self, call_repo, ai_metadata_repo, dispatch_repo, db_session):
        """Listing calls should return all calls."""
        for i in range(3):
            call = CallSession(
                id=uuid4(),
                caller_hash=f"hash_{i}",
                status="Active",
            )
            db_session.add(call)
        db_session.commit()

        filters = CallFilters(status=None, spam_label=None, page=1, limit=100)
        result = calls_service.list_calls(
            filters,
            calls=call_repo,
            ai_metadata=ai_metadata_repo,
            dispatches=dispatch_repo,
        )

        assert len(result) >= 3

    @pytest.mark.unit
    @pytest.mark.service
    def test_list_calls_filter_by_status(self, call_repo, ai_metadata_repo, dispatch_repo, db_session):
        """Filtering by status should work."""
        for status in ["Active", "Incoming", "Dispatched"]:
            call = CallSession(
                id=uuid4(),
                caller_hash=f"hash_{status}",
                status=status,
            )
            db_session.add(call)
        db_session.commit()

        filters = CallFilters(status="Active", spam_label=None, page=1, limit=100)
        result = calls_service.list_calls(
            filters,
            calls=call_repo,
            ai_metadata=ai_metadata_repo,
            dispatches=dispatch_repo,
        )

        for call in result:
            assert call.status == "Active"

    @pytest.mark.unit
    @pytest.mark.service
    def test_list_calls_pagination(self, call_repo, ai_metadata_repo, dispatch_repo, db_session):
        """Pagination should limit results."""
        for i in range(10):
            call = CallSession(
                id=uuid4(),
                caller_hash=f"hash_{i}",
            )
            db_session.add(call)
        db_session.commit()

        filters = CallFilters(status=None, spam_label=None, page=1, limit=3)
        result = calls_service.list_calls(
            filters,
            calls=call_repo,
            ai_metadata=ai_metadata_repo,
            dispatches=dispatch_repo,
        )

        assert len(result) <= 3
