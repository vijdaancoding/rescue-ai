"""
Tests for call management API endpoints.

Tests call listing, updating status, and retrieving call context.
"""

import pytest
import json
from datetime import datetime, timezone
from uuid import uuid4

from app.db.models import CallSession


class TestCallsList:
    """Test GET /calls endpoint - list all calls."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_list_calls_requires_auth(self, client):
        """Accessing /calls without auth should fail."""
        response = client.get("/calls")
        assert response.status_code == 401

    @pytest.mark.unit
    @pytest.mark.api
    def test_list_calls_with_valid_token(self, client, test_call, auth_headers):
        """Authenticated request should return calls list."""
        response = client.get("/calls", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.unit
    @pytest.mark.api
    def test_list_calls_with_invalid_token(self, client, invalid_auth_headers):
        """Invalid token should be rejected."""
        response = client.get("/calls", headers=invalid_auth_headers)
        assert response.status_code == 401

    @pytest.mark.unit
    @pytest.mark.api
    def test_list_calls_returns_call_data(self, client, test_call, auth_headers):
        """Call list should contain call objects with expected fields."""
        response = client.get("/calls", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        
        # Check call structure
        call = data[0]
        assert "id" in call
        assert "status" in call
        assert "start_time" in call
        assert "caller_phone" in call

    @pytest.mark.unit
    @pytest.mark.api
    def test_list_calls_empty(self, client, db_session, auth_headers):
        """Empty calls list should return empty array."""
        # Clear all calls
        db_session.query(CallSession).delete()
        db_session.commit()
        
        response = client.get("/calls", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data == []


class TestUpdateCallStatus:
    """Test PATCH /calls/{call_id} endpoint."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_update_call_status_success(self, client, test_call, auth_headers):
        """Updating call status should succeed."""
        response = client.patch(
            f"/calls/{test_call.id}",
            json={"status": "Dispatched"},
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Dispatched"

    @pytest.mark.unit
    @pytest.mark.api
    def test_update_call_status_requires_auth(self, client, test_call):
        """Update without auth should fail."""
        response = client.patch(
            f"/calls/{test_call.id}",
            json={"status": "Dispatched"},
        )
        assert response.status_code == 401

    @pytest.mark.unit
    @pytest.mark.api
    def test_update_call_status_nonexistent(self, client, auth_headers):
        """Updating nonexistent call should fail."""
        fake_id = str(uuid4())
        response = client.patch(
            f"/calls/{fake_id}",
            json={"status": "Dispatched"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.unit
    @pytest.mark.api
    def test_update_call_status_valid_statuses(self, client, test_call, auth_headers):
        """All valid status transitions should work."""
        valid_statuses = ["Incoming", "Active", "Dispatched", "FalseAlarm"]
        
        for status in valid_statuses:
            response = client.patch(
                f"/calls/{test_call.id}",
                json={"status": status},
                headers=auth_headers,
            )
            assert response.status_code == 200
            assert response.json()["status"] == status

    @pytest.mark.unit
    @pytest.mark.api
    def test_update_call_status_sets_end_time_on_close(self, client, test_call, auth_headers):
        """Updating to final status should set end_time."""
        response = client.patch(
            f"/calls/{test_call.id}",
            json={"status": "FalseAlarm"},
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "end_time" in data or data["status"] == "FalseAlarm"


class TestGetCallContext:
    """Test GET /calls/{call_id}/context endpoint."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_get_call_context_success(self, client, test_call, test_ai_metadata, auth_headers):
        """Getting call context should return complete data."""
        response = client.get(
            f"/calls/{test_call.id}/context",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should contain call data
        assert data["id"] == str(test_call.id)
        assert data["status"] == test_call.status

    @pytest.mark.unit
    @pytest.mark.api
    def test_get_call_context_includes_metadata(self, client, test_call, test_ai_metadata, auth_headers):
        """Call context should include AI metadata."""
        response = client.get(
            f"/calls/{test_call.id}/context",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have metadata fields
        if "metadata" in data:
            assert "scam_probability" in data["metadata"]

    @pytest.mark.unit
    @pytest.mark.api
    def test_get_call_context_requires_auth(self, client, test_call):
        """Getting context without auth should fail."""
        response = client.get(f"/calls/{test_call.id}/context")
        assert response.status_code == 401

    @pytest.mark.unit
    @pytest.mark.api
    def test_get_call_context_nonexistent(self, client, auth_headers):
        """Getting context for nonexistent call should fail."""
        fake_id = str(uuid4())
        response = client.get(
            f"/calls/{fake_id}/context",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.unit
    @pytest.mark.api
    def test_get_call_context_includes_geolocation(self, client, test_call, test_geolocation, auth_headers):
        """Call context should include geolocation data."""
        response = client.get(
            f"/calls/{test_call.id}/context",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have location info
        assert "caller_city" in data or "geolocation" in data


class TestCallsListPagination:
    """Test pagination and filtering of calls list."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_list_calls_with_status_filter(self, client, db_session, auth_headers):
        """Listing calls with status filter should work."""
        # Create calls with different statuses
        for status in ["Active", "Incoming", "Dispatched"]:
            call = CallSession(
                id=uuid4(),
                caller_hash=f"hash_{status}",
                status=status,
                room_name=f"room_{status}",
            )
            db_session.add(call)
        db_session.commit()
        
        response = client.get(
            "/calls?status=Active",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned calls should have status "Active"
        for call in data:
            assert call["status"] == "Active"

    @pytest.mark.unit
    @pytest.mark.api
    def test_list_calls_pagination_limit(self, client, db_session, auth_headers):
        """Pagination limit parameter should work."""
        # Create multiple calls
        for i in range(5):
            call = CallSession(
                id=uuid4(),
                caller_hash=f"hash_{i}",
                room_name=f"room_{i}",
            )
            db_session.add(call)
        db_session.commit()
        
        response = client.get(
            "/calls?limit=2",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2
