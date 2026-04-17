"""
Tests for dispatch management API endpoints.

Tests dispatch creation, listing, and status updates.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from app.db.models import Dispatch, CallSession


class TestCreateDispatch:
    """Test POST /dispatches endpoint."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_create_dispatch_success(self, client, test_call, auth_headers):
        """Creating a dispatch should succeed."""
        response = client.post(
            "/dispatches",
            json={
                "call_id": str(test_call.id),
                "dispatch_type": "ambulance",
                "notes": "Medical emergency",
                "ai_recommended": True,
            },
            headers=auth_headers,
        )
        
        assert response.status_code == 201 or response.status_code == 200
        data = response.json()
        assert data["dispatch_type"] == "ambulance"
        assert data["status"] == "dispatched"
        assert data["call_id"] == str(test_call.id)

    @pytest.mark.unit
    @pytest.mark.api
    def test_create_dispatch_requires_auth(self, client, test_call):
        """Creating dispatch without auth should fail."""
        response = client.post(
            "/dispatches",
            json={
                "call_id": str(test_call.id),
                "dispatch_type": "ambulance",
            },
        )
        assert response.status_code == 401

    @pytest.mark.unit
    @pytest.mark.api
    def test_create_dispatch_invalid_call_id(self, client, auth_headers):
        """Creating dispatch with invalid call_id should fail."""
        response = client.post(
            "/dispatches",
            json={
                "call_id": str(uuid4()),  # Non-existent call
                "dispatch_type": "ambulance",
            },
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.unit
    @pytest.mark.api
    def test_create_dispatch_valid_types(self, client, test_call, auth_headers):
        """All valid dispatch types should be accepted."""
        valid_types = ["police", "ambulance", "firefighters"]
        
        for dispatch_type in valid_types:
            response = client.post(
                "/dispatches",
                json={
                    "call_id": str(test_call.id),
                    "dispatch_type": dispatch_type,
                },
                headers=auth_headers,
            )
            assert response.status_code in [200, 201]
            assert response.json()["dispatch_type"] == dispatch_type

    @pytest.mark.unit
    @pytest.mark.api
    def test_create_dispatch_invalid_type(self, client, test_call, auth_headers):
        """Invalid dispatch type should be rejected."""
        response = client.post(
            "/dispatches",
            json={
                "call_id": str(test_call.id),
                "dispatch_type": "invalid_type",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422 or response.status_code == 400

    @pytest.mark.unit
    @pytest.mark.api
    def test_create_multiple_dispatches_same_call(self, client, test_call, auth_headers):
        """Multiple different dispatch types can be sent for same call."""
        types = ["ambulance", "police"]
        dispatch_ids = []
        
        for dispatch_type in types:
            response = client.post(
                "/dispatches",
                json={
                    "call_id": str(test_call.id),
                    "dispatch_type": dispatch_type,
                },
                headers=auth_headers,
            )
            assert response.status_code in [200, 201]
            dispatch_ids.append(response.json()["id"])
        
        # All dispatch IDs should be unique
        assert len(set(dispatch_ids)) == len(dispatch_ids)


class TestListDispatches:
    """Test GET /dispatches endpoint."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_list_dispatches_requires_auth(self, client):
        """Listing dispatches without auth should fail."""
        response = client.get("/dispatches")
        assert response.status_code == 401

    @pytest.mark.unit
    @pytest.mark.api
    def test_list_dispatches_success(self, client, test_dispatch, auth_headers):
        """Listing dispatches should return array."""
        response = client.get("/dispatches", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.unit
    @pytest.mark.api
    def test_list_dispatches_empty(self, client, db_session, auth_headers):
        """Empty dispatch list should return empty array."""
        db_session.query(Dispatch).delete()
        db_session.commit()
        
        response = client.get("/dispatches", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.unit
    @pytest.mark.api
    def test_list_dispatches_includes_required_fields(self, client, test_dispatch, auth_headers):
        """Returned dispatches should include all required fields."""
        response = client.get("/dispatches", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            dispatch = data[0]
            assert "id" in dispatch
            assert "call_id" in dispatch
            assert "dispatch_type" in dispatch
            assert "status" in dispatch


class TestUpdateDispatchStatus:
    """Test PATCH /dispatches/{dispatch_id} endpoint."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_update_dispatch_status_success(self, client, test_dispatch, auth_headers):
        """Updating dispatch status should succeed."""
        response = client.patch(
            f"/dispatches/{test_dispatch.id}",
            json={"status": "en_route"},
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "en_route"

    @pytest.mark.unit
    @pytest.mark.api
    def test_update_dispatch_status_requires_auth(self, client, test_dispatch):
        """Update without auth should fail."""
        response = client.patch(
            f"/dispatches/{test_dispatch.id}",
            json={"status": "en_route"},
        )
        assert response.status_code == 401

    @pytest.mark.unit
    @pytest.mark.api
    def test_update_dispatch_status_valid_transitions(self, client, test_dispatch, auth_headers):
        """Valid status transitions should work."""
        valid_statuses = ["dispatched", "en_route", "on_scene", "resolved"]
        
        for status in valid_statuses:
            response = client.patch(
                f"/dispatches/{test_dispatch.id}",
                json={"status": status},
                headers=auth_headers,
            )
            assert response.status_code == 200

    @pytest.mark.unit
    @pytest.mark.api
    def test_update_dispatch_nonexistent(self, client, auth_headers):
        """Updating nonexistent dispatch should fail."""
        fake_id = str(uuid4())
        response = client.patch(
            f"/dispatches/{fake_id}",
            json={"status": "en_route"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.unit
    @pytest.mark.api
    def test_update_dispatch_with_notes(self, client, test_dispatch, auth_headers):
        """Updating dispatch with notes should preserve them."""
        notes = "Updated notes: patient stable"
        response = client.patch(
            f"/dispatches/{test_dispatch.id}",
            json={
                "status": "on_scene",
                "notes": notes,
            },
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == notes


class TestDispatchFilter:
    """Test filtering dispatches by status and type."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_filter_dispatches_by_status(self, client, db_session, auth_headers):
        """Filtering by status should work."""
        # Create test data
        call = CallSession(id=uuid4(), caller_hash="test")
        db_session.add(call)
        db_session.flush()
        
        for status in ["dispatched", "en_route", "resolved"]:
            dispatch = Dispatch(
                id=uuid4(),
                call_id=call.id,
                dispatch_type="ambulance",
                status=status,
            )
            db_session.add(dispatch)
        db_session.commit()
        
        response = client.get(
            "/dispatches?status=en_route",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for dispatch in data:
            assert dispatch["status"] == "en_route"

    @pytest.mark.unit
    @pytest.mark.api
    def test_filter_dispatches_by_type(self, client, db_session, auth_headers):
        """Filtering by dispatch type should work."""
        call = CallSession(id=uuid4(), caller_hash="test")
        db_session.add(call)
        db_session.flush()
        
        for dtype in ["ambulance", "police", "firefighters"]:
            dispatch = Dispatch(
                id=uuid4(),
                call_id=call.id,
                dispatch_type=dtype,
            )
            db_session.add(dispatch)
        db_session.commit()
        
        response = client.get(
            "/dispatches?dispatch_type=police",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for dispatch in data:
            assert dispatch["dispatch_type"] == "police"
