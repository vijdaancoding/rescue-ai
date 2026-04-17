"""
Tests for dispatch management service layer.

Tests dispatch creation, status updates, and dispatch tracking.
"""

import pytest
from uuid import uuid4

from app.db.models import Dispatch, CallSession
from app.services import dispatches as dispatches_service


class TestCreateDispatch:
    """Test dispatch creation logic."""

    @pytest.mark.unit
    @pytest.mark.service
    def test_create_dispatch_success(self, dispatch_repo, test_call):
        """Creating a dispatch should succeed."""
        result = dispatches_service.create_dispatch(
            call_id=test_call.id,
            dispatch_type="ambulance",
            notes="Medical emergency",
            ai_recommended=True,
            dispatches=dispatch_repo,
        )
        
        assert result is not None
        assert result.dispatch_type == "ambulance"
        assert result.status == "dispatched"
        assert result.ai_recommended is True

    @pytest.mark.unit
    @pytest.mark.service
    def test_create_dispatch_invalid_call(self, dispatch_repo):
        """Creating dispatch for nonexistent call should fail."""
        with pytest.raises(Exception):
            dispatches_service.create_dispatch(
                call_id=uuid4(),
                dispatch_type="ambulance",
                ai_recommended=False,
                dispatches=dispatch_repo,
            )

    @pytest.mark.unit
    @pytest.mark.service
    def test_create_dispatch_valid_types(self, dispatch_repo, test_call):
        """All valid dispatch types should be accepted."""
        for dispatch_type in ["police", "ambulance", "firefighters"]:
            result = dispatches_service.create_dispatch(
                call_id=test_call.id,
                dispatch_type=dispatch_type,
                ai_recommended=False,
                dispatches=dispatch_repo,
            )
            
            assert result is not None
            assert result.dispatch_type == dispatch_type

    @pytest.mark.unit
    @pytest.mark.service
    def test_create_dispatch_multiple_same_call(self, dispatch_repo, test_call):
        """Multiple dispatches for same call should succeed."""
        ids = []
        
        for dispatch_type in ["ambulance", "police"]:
            result = dispatches_service.create_dispatch(
                call_id=test_call.id,
                dispatch_type=dispatch_type,
                ai_recommended=False,
                dispatches=dispatch_repo,
            )
            ids.append(result.id)
        
        # All IDs should be unique
        assert len(set(ids)) == len(ids)

    @pytest.mark.unit
    @pytest.mark.service
    def test_create_dispatch_marks_ai_recommended(self, dispatch_repo, test_call):
        """AI recommendation flag should be preserved."""
        ai_recommended = dispatches_service.create_dispatch(
            call_id=test_call.id,
            dispatch_type="ambulance",
            ai_recommended=True,
            dispatches=dispatch_repo,
        )
        
        not_ai_recommended = dispatches_service.create_dispatch(
            call_id=test_call.id,
            dispatch_type="police",
            ai_recommended=False,
            dispatches=dispatch_repo,
        )
        
        assert ai_recommended.ai_recommended is True
        assert not_ai_recommended.ai_recommended is False


class TestUpdateDispatchStatus:
    """Test dispatch status updates."""

    @pytest.mark.unit
    @pytest.mark.service
    def test_update_dispatch_status_valid_transition(self, dispatch_repo, test_dispatch):
        """Valid status transition should work."""
        result = dispatches_service.update_dispatch_status(
            dispatch_id=test_dispatch.id,
            new_status="en_route",
            dispatches=dispatch_repo,
        )
        
        assert result is not None
        assert result.status == "en_route"

    @pytest.mark.unit
    @pytest.mark.service
    def test_update_dispatch_status_all_valid_statuses(self, dispatch_repo, test_dispatch):
        """All valid statuses should be accepted."""
        statuses = ["dispatched", "en_route", "on_scene", "resolved"]
        
        for status in statuses:
            result = dispatches_service.update_dispatch_status(
                dispatch_id=test_dispatch.id,
                new_status=status,
                dispatches=dispatch_repo,
            )
            
            assert result.status == status

    @pytest.mark.unit
    @pytest.mark.service
    def test_update_dispatch_nonexistent(self, dispatch_repo):
        """Updating nonexistent dispatch should fail."""
        with pytest.raises(Exception):
            dispatches_service.update_dispatch_status(
                dispatch_id=uuid4(),
                new_status="en_route",
                dispatches=dispatch_repo,
            )

    @pytest.mark.unit
    @pytest.mark.service
    def test_update_dispatch_with_notes(self, dispatch_repo, test_dispatch):
        """Updating dispatch with notes should work."""
        notes = "Patient arriving at hospital"
        result = dispatches_service.update_dispatch_status(
            dispatch_id=test_dispatch.id,
            new_status="on_scene",
            notes=notes,
            dispatches=dispatch_repo,
        )
        
        assert result.notes == notes


class TestListDispatches:
    """Test listing dispatches with filtering."""

    @pytest.mark.unit
    @pytest.mark.service
    def test_list_dispatches_returns_all(self, dispatch_repo, db_session, test_call):
        """Listing should return all dispatches."""
        # Create multiple dispatches
        for i in range(3):
            dispatch = Dispatch(
                id=uuid4(),
                call_id=test_call.id,
                dispatch_type="ambulance",
                status="dispatched",
            )
            db_session.add(dispatch)
        db_session.commit()
        
        result = dispatches_service.list_dispatches(dispatches=dispatch_repo)
        
        assert len(result) >= 3

    @pytest.mark.unit
    @pytest.mark.service
    def test_list_dispatches_filter_by_status(self, dispatch_repo, db_session, test_call):
        """Filtering by status should work."""
        # Create dispatches with different statuses
        for status in ["dispatched", "en_route", "resolved"]:
            dispatch = Dispatch(
                id=uuid4(),
                call_id=test_call.id,
                dispatch_type="ambulance",
                status=status,
            )
            db_session.add(dispatch)
        db_session.commit()
        
        result = dispatches_service.list_dispatches(
            dispatches=dispatch_repo,
            status_filter="en_route",
        )
        
        for dispatch in result:
            assert dispatch.status == "en_route"

    @pytest.mark.unit
    @pytest.mark.service
    def test_list_dispatches_filter_by_type(self, dispatch_repo, db_session, test_call):
        """Filtering by dispatch type should work."""
        # Create dispatches of different types
        for dtype in ["ambulance", "police", "firefighters"]:
            dispatch = Dispatch(
                id=uuid4(),
                call_id=test_call.id,
                dispatch_type=dtype,
                status="dispatched",
            )
            db_session.add(dispatch)
        db_session.commit()
        
        result = dispatches_service.list_dispatches(
            dispatches=dispatch_repo,
            type_filter="police",
        )
        
        for dispatch in result:
            assert dispatch.dispatch_type == "police"

    @pytest.mark.unit
    @pytest.mark.service
    def test_list_dispatches_ai_recommended_filter(self, dispatch_repo, db_session, test_call):
        """Filtering by AI recommendation should work."""
        # Create some AI-recommended and some manual
        for ai_recommended in [True, False, True]:
            dispatch = Dispatch(
                id=uuid4(),
                call_id=test_call.id,
                dispatch_type="ambulance",
                ai_recommended=ai_recommended,
            )
            db_session.add(dispatch)
        db_session.commit()
        
        result = dispatches_service.list_dispatches(
            dispatches=dispatch_repo,
            ai_recommended_only=True,
        )
        
        for dispatch in result:
            assert dispatch.ai_recommended is True


class TestDispatchMetrics:
    """Test dispatch metrics and statistics."""

    @pytest.mark.unit
    @pytest.mark.service
    def test_get_dispatch_stats_by_type(self, dispatch_repo, db_session, test_call):
        """Should calculate dispatch counts by type."""
        # Create dispatches
        types = ["ambulance", "police", "firefighters", "ambulance"]
        for dtype in types:
            dispatch = Dispatch(
                id=uuid4(),
                call_id=test_call.id,
                dispatch_type=dtype,
            )
            db_session.add(dispatch)
        db_session.commit()
        
        result = dispatches_service.get_dispatch_stats(
            dispatches=dispatch_repo,
            group_by="type",
        )
        
        assert result is not None
        # Should count 2 ambulances, 1 police, 1 firefighters
        assert result.get("ambulance", 0) == 2
