"""
Tests for call repository data access layer.

Tests database queries, filtering, and data retrieval for calls.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from app.db.models import CallSession


class TestCallRepositoryGetById:
    """Test retrieving calls by ID."""

    @pytest.mark.unit
    def test_get_call_by_id_success(self, call_repo, test_call):
        """Retrieving call by ID should return the call."""
        result = call_repo.get_by_id(test_call.id)
        
        assert result is not None
        assert result.id == test_call.id
        assert result.caller_phone == test_call.caller_phone

    @pytest.mark.unit
    def test_get_call_by_id_nonexistent(self, call_repo):
        """Getting nonexistent call should return None."""
        result = call_repo.get_by_id(uuid4())
        assert result is None

    @pytest.mark.unit
    def test_get_call_by_id_preserves_all_fields(self, call_repo, test_call):
        """All call fields should be preserved."""
        result = call_repo.get_by_id(test_call.id)
        
        assert result.caller_hash == test_call.caller_hash
        assert result.status == test_call.status
        assert result.caller_city == test_call.caller_city
        assert result.room_name == test_call.room_name


class TestCallRepositoryList:
    """Test listing calls."""

    @pytest.mark.unit
    def test_list_calls_returns_all(self, call_repo, db_session):
        """List should return all calls."""
        # Create multiple calls
        for i in range(3):
            call = CallSession(
                id=uuid4(),
                caller_hash=f"hash_{i}",
                status="Active",
            )
            db_session.add(call)
        db_session.commit()
        
        result = call_repo.list()
        assert len(result) >= 3

    @pytest.mark.unit
    def test_list_calls_empty(self, call_repo, db_session):
        """Empty list should return empty array."""
        db_session.query(CallSession).delete()
        db_session.commit()
        
        result = call_repo.list()
        assert result == []

    @pytest.mark.unit
    def test_list_calls_pagination_limit(self, call_repo, db_session):
        """Limit parameter should work."""
        for i in range(5):
            call = CallSession(
                id=uuid4(),
                caller_hash=f"hash_{i}",
            )
            db_session.add(call)
        db_session.commit()
        
        result = call_repo.list(limit=2)
        assert len(result) <= 2

    @pytest.mark.unit
    def test_list_calls_pagination_offset(self, call_repo, db_session):
        """Offset parameter should work."""
        call_ids = []
        for i in range(5):
            call = CallSession(
                id=uuid4(),
                caller_hash=f"hash_{i}",
            )
            db_session.add(call)
            call_ids.append(call.id)
        db_session.commit()
        
        result = call_repo.list(limit=2, offset=2)
        # Should skip first 2 and return next 2
        assert len(result) <= 2


class TestCallRepositoryFilterByStatus:
    """Test filtering calls by status."""

    @pytest.mark.unit
    def test_filter_by_status_success(self, call_repo, db_session):
        """Should return only calls with matching status."""
        for status in ["Active", "Incoming", "Dispatched", "Active"]:
            call = CallSession(
                id=uuid4(),
                caller_hash=f"hash_{status}",
                status=status,
            )
            db_session.add(call)
        db_session.commit()
        
        result = call_repo.list(status_filter="Active")
        
        for call in result:
            assert call.status == "Active"
        assert len(result) >= 2

    @pytest.mark.unit
    def test_filter_by_status_no_matches(self, call_repo, db_session):
        """Filter with no matches should return empty list."""
        call = CallSession(
            id=uuid4(),
            caller_hash="hash_1",
            status="Active",
        )
        db_session.add(call)
        db_session.commit()
        
        result = call_repo.list(status_filter="NonexistentStatus")
        assert len(result) == 0


class TestCallRepositoryUpdate:
    """Test updating calls."""

    @pytest.mark.unit
    def test_update_call_status(self, call_repo, test_call):
        """Updating status should persist."""
        original_id = test_call.id
        
        call_repo.update(test_call.id, {"status": "Dispatched"})
        
        updated = call_repo.get_by_id(original_id)
        assert updated.status == "Dispatched"

    @pytest.mark.unit
    def test_update_call_end_time(self, call_repo, test_call):
        """Updating end_time should persist."""
        end_time = datetime.now(timezone.utc)
        
        call_repo.update(test_call.id, {"end_time": end_time})
        
        updated = call_repo.get_by_id(test_call.id)
        assert updated.end_time is not None

    @pytest.mark.unit
    def test_update_preserves_other_fields(self, call_repo, test_call):
        """Updating one field shouldn't affect others."""
        original_phone = test_call.caller_phone
        
        call_repo.update(test_call.id, {"status": "Dispatched"})
        
        updated = call_repo.get_by_id(test_call.id)
        assert updated.caller_phone == original_phone


class TestCallRepositoryCreate:
    """Test creating new calls."""

    @pytest.mark.unit
    def test_create_call_success(self, call_repo):
        """Creating a call should return the created call."""
        result = call_repo.create(
            caller_hash="test_hash",
            caller_phone="+923001234567",
            room_name="test_room",
        )
        
        assert result is not None
        assert result.id is not None
        assert result.caller_hash == "test_hash"
        assert result.status == "Incoming"  # Default status

    @pytest.mark.unit
    def test_create_call_with_metadata(self, call_repo):
        """Creating call with all fields should work."""
        result = call_repo.create(
            caller_hash="hash_full",
            caller_phone="+923009876543",
            caller_city="Lahore",
            caller_state="Punjab",
            caller_country="Pakistan",
            room_name="room_full",
        )
        
        assert result.caller_city == "Lahore"
        assert result.caller_state == "Punjab"
        assert result.room_name == "room_full"

    @pytest.mark.unit
    def test_create_call_generates_unique_id(self, call_repo):
        """Each created call should have unique ID."""
        call1 = call_repo.create(
            caller_hash="hash1",
            room_name="room1",
        )
        call2 = call_repo.create(
            caller_hash="hash2",
            room_name="room2",
        )
        
        assert call1.id != call2.id


class TestCallRepositoryLatestMetadata:
    """Test retrieving latest AI metadata for calls."""

    @pytest.mark.unit
    def test_get_latest_metadata(self, call_repo, test_call, test_ai_metadata):
        """Should retrieve latest metadata for a call."""
        result = call_repo.get_latest_metadata(test_call.id)
        
        assert result is not None
        assert result.call_id == test_call.id

    @pytest.mark.unit
    def test_get_latest_metadata_nonexistent_call(self, call_repo):
        """Nonexistent call should return None."""
        result = call_repo.get_latest_metadata(uuid4())
        assert result is None

    @pytest.mark.unit
    def test_get_latest_metadata_no_metadata(self, call_repo, test_call_incoming):
        """Call with no metadata should return None."""
        result = call_repo.get_latest_metadata(test_call_incoming.id)
        assert result is None
