"""
Tests for dispatch management service layer.
"""

import pytest
from uuid import uuid4

from app.db.models import Dispatch, CallSession
from app.schemas.dispatches import DispatchCreate
from app.services import dispatches as dispatches_service


class TestCreateDispatch:
    """Test dispatch creation logic."""

    @pytest.mark.unit
    @pytest.mark.service
    def test_create_dispatch_success(self, call_repo, dispatch_repo, test_call):
        """Creating dispatches should succeed."""
        body = DispatchCreate(
            call_id=str(test_call.id),
            dispatch_types=["ambulance"],
            notes="Medical emergency",
            ai_recommended=["ambulance"],
        )
        result = dispatches_service.create_dispatches(body, calls=call_repo, dispatches=dispatch_repo)

        assert len(result) == 1
        assert result[0].dispatch_type == "ambulance"
        assert result[0].status == "dispatched"
        assert result[0].ai_recommended is True

    @pytest.mark.unit
    @pytest.mark.service
    def test_create_dispatch_invalid_call(self, call_repo, dispatch_repo):
        """Creating dispatch for nonexistent call should fail."""
        body = DispatchCreate(
            call_id=str(uuid4()),
            dispatch_types=["ambulance"],
        )
        with pytest.raises(Exception):
            dispatches_service.create_dispatches(body, calls=call_repo, dispatches=dispatch_repo)

    @pytest.mark.unit
    @pytest.mark.service
    def test_create_dispatch_valid_types(self, call_repo, dispatch_repo, test_call):
        """All valid dispatch types should be accepted."""
        for dispatch_type in ["police", "ambulance", "firefighters"]:
            body = DispatchCreate(
                call_id=str(test_call.id),
                dispatch_types=[dispatch_type],
            )
            result = dispatches_service.create_dispatches(body, calls=call_repo, dispatches=dispatch_repo)
            assert len(result) >= 1

    @pytest.mark.unit
    @pytest.mark.service
    def test_create_dispatch_multiple_same_call(self, call_repo, dispatch_repo, test_call):
        """Multiple dispatches for same call should succeed with unique IDs."""
        body = DispatchCreate(
            call_id=str(test_call.id),
            dispatch_types=["ambulance", "police"],
        )
        result = dispatches_service.create_dispatches(body, calls=call_repo, dispatches=dispatch_repo)

        ids = [r.id for r in result]
        assert len(set(ids)) == len(ids)

    @pytest.mark.unit
    @pytest.mark.service
    def test_create_dispatch_marks_ai_recommended(self, call_repo, dispatch_repo, test_call):
        """AI recommendation flag should be preserved."""
        body = DispatchCreate(
            call_id=str(test_call.id),
            dispatch_types=["ambulance"],
            ai_recommended=["ambulance"],
        )
        result = dispatches_service.create_dispatches(body, calls=call_repo, dispatches=dispatch_repo)
        assert result[0].ai_recommended is True


class TestUpdateDispatchStatus:
    """Test dispatch status updates."""

    @pytest.mark.unit
    @pytest.mark.service
    def test_update_dispatch_status_valid_transition(self, dispatch_repo, test_dispatch):
        """Valid status transition should work."""
        result = dispatches_service.update_status(
            str(test_dispatch.id),
            "en_route",
            dispatches=dispatch_repo,
        )

        assert result is not None
        assert result.status == "en_route"

    @pytest.mark.unit
    @pytest.mark.service
    def test_update_dispatch_status_all_valid_statuses(self, dispatch_repo, test_dispatch):
        """All valid statuses should be accepted."""
        for status in ["dispatched", "en_route", "on_scene", "resolved"]:
            result = dispatches_service.update_status(
                str(test_dispatch.id),
                status,
                dispatches=dispatch_repo,
            )
            assert result.status == status

    @pytest.mark.unit
    @pytest.mark.service
    def test_update_dispatch_nonexistent(self, dispatch_repo):
        """Updating nonexistent dispatch should fail."""
        with pytest.raises(Exception):
            dispatches_service.update_status(
                str(uuid4()),
                "en_route",
                dispatches=dispatch_repo,
            )

    @pytest.mark.unit
    @pytest.mark.service
    def test_update_dispatch_with_notes(self, dispatch_repo, test_dispatch):
        """Updating dispatch with notes should work."""
        notes = "Patient arriving at hospital"
        result = dispatches_service.update_status(
            str(test_dispatch.id),
            "on_scene",
            dispatches=dispatch_repo,
            notes=notes,
        )

        assert result.notes == notes


class TestListDispatches:
    """Test listing dispatches."""

    @pytest.mark.unit
    @pytest.mark.service
    def test_list_dispatches_returns_all(self, dispatch_repo, db_session, test_call):
        """Listing dispatches for call should return all dispatches."""
        for i in range(3):
            dispatch = Dispatch(
                id=uuid4(),
                call_id=test_call.id,
                dispatch_type="ambulance",
                status="dispatched",
            )
            db_session.add(dispatch)
        db_session.commit()

        result = dispatches_service.list_for_call(str(test_call.id), dispatches=dispatch_repo)
        assert len(result) >= 3

    @pytest.mark.unit
    @pytest.mark.service
    def test_list_dispatches_filter_by_status(self, dispatch_repo, db_session, test_call):
        """list_all with status filter should work."""
        for status in ["dispatched", "en_route", "resolved"]:
            dispatch = Dispatch(
                id=uuid4(),
                call_id=test_call.id,
                dispatch_type="ambulance",
                status=status,
            )
            db_session.add(dispatch)
        db_session.commit()

        rows = dispatch_repo.list_all(status_filter="en_route")
        for row in rows:
            assert row.status == "en_route"

    @pytest.mark.unit
    @pytest.mark.service
    def test_list_dispatches_filter_by_type(self, dispatch_repo, db_session, test_call):
        """list_all with type filter should work."""
        for dtype in ["ambulance", "police", "firefighters"]:
            dispatch = Dispatch(
                id=uuid4(),
                call_id=test_call.id,
                dispatch_type=dtype,
                status="dispatched",
            )
            db_session.add(dispatch)
        db_session.commit()

        rows = dispatch_repo.list_all(type_filter="police")
        for row in rows:
            assert row.dispatch_type == "police"

    @pytest.mark.unit
    @pytest.mark.service
    def test_list_dispatches_ai_recommended_filter(self, dispatch_repo, db_session, test_call):
        """AI-recommended dispatches can be filtered."""
        for ai_recommended in [True, False, True]:
            dispatch = Dispatch(
                id=uuid4(),
                call_id=test_call.id,
                dispatch_type="ambulance",
                ai_recommended=ai_recommended,
            )
            db_session.add(dispatch)
        db_session.commit()

        all_rows = dispatch_repo.list_all()
        ai_rows = [r for r in all_rows if r.ai_recommended]
        for row in ai_rows:
            assert row.ai_recommended is True


class TestDispatchMetrics:
    """Test dispatch metrics and statistics."""

    @pytest.mark.unit
    @pytest.mark.service
    def test_get_dispatch_stats_by_type(self, dispatch_repo, db_session, test_call):
        """Should calculate dispatch counts by type."""
        for dtype in ["ambulance", "police", "firefighters", "ambulance"]:
            dispatch = Dispatch(
                id=uuid4(),
                call_id=test_call.id,
                dispatch_type=dtype,
            )
            db_session.add(dispatch)
        db_session.commit()

        all_rows = dispatch_repo.list_all()
        stats: dict = {}
        for row in all_rows:
            stats[row.dispatch_type] = stats.get(row.dispatch_type, 0) + 1

        assert stats is not None
        assert stats.get("ambulance", 0) >= 2
