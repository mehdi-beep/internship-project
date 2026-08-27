"""Ch.27 (duration), Ch.28 (points), Ch.9/Ch.17 (status transitions)."""

from datetime import datetime, time
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException

from app.models.enums import InterventionStatus

CASABLANCA = ZoneInfo("Africa/Casablanca")
UTC = ZoneInfo("UTC")


def at_casablanca_hour(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 8, 2, hour, minute, tzinfo=CASABLANCA).astimezone(UTC)


class TestDurationCalculation:
    def test_matches_the_spec_worked_example(self):
        from app.services.business_logic_service import calculate_net_duration_minutes

        # Ch.27: 08:00-17:30, 1h lunch -> 9h30 gross - 1h = 8h30 = 510 minutes.
        assert calculate_net_duration_minutes(time(8, 0), time(17, 30), 60) == 510

    def test_zero_lunch_break(self):
        from app.services.business_logic_service import calculate_net_duration_minutes

        assert calculate_net_duration_minutes(time(9, 0), time(12, 0), 0) == 180

    def test_lunch_break_exceeding_gross_duration_rejected(self):
        from app.services.business_logic_service import calculate_net_duration_minutes

        with pytest.raises(HTTPException) as exc_info:
            calculate_net_duration_minutes(time(8, 0), time(8, 30), 60)
        assert exc_info.value.status_code == 400


class TestPointSystem:
    """Ch.28 / Task 2 — every boundary hour, evaluated in Africa/Casablanca
    local time (not UTC), against the seeded DEFAULT_POINT_RULES (which
    reproduce the original hardcoded spec exactly). `calculate_points` now
    reads `point_rules` from the database, so these need a real session —
    `client` guarantees one seeded and importable via a fresh SessionLocal."""

    def _session(self):
        from app.database.session import SessionLocal

        return SessionLocal()

    def test_five_points_window(self, client):
        from app.services.business_logic_service import calculate_points

        db = self._session()
        try:
            assert calculate_points(db, at_casablanca_hour(17, 0)) == 5
            assert calculate_points(db, at_casablanca_hour(18, 59)) == 5
        finally:
            db.close()

    def test_two_points_window(self, client):
        from app.services.business_logic_service import calculate_points

        db = self._session()
        try:
            assert calculate_points(db, at_casablanca_hour(19, 0)) == 2
            assert calculate_points(db, at_casablanca_hour(21, 59)) == 2
        finally:
            db.close()

    def test_one_point_window(self, client):
        from app.services.business_logic_service import calculate_points

        db = self._session()
        try:
            assert calculate_points(db, at_casablanca_hour(22, 0)) == 1
            assert calculate_points(db, at_casablanca_hour(23, 59)) == 1
        finally:
            db.close()

    def test_flat_penalty_outside_the_three_positive_windows(self, client):
        from app.services.business_logic_service import calculate_points

        db = self._session()
        try:
            assert calculate_points(db, at_casablanca_hour(0, 0)) == -1
            assert calculate_points(db, at_casablanca_hour(5, 59)) == -1
            assert calculate_points(db, at_casablanca_hour(6, 0)) == -1
            assert calculate_points(db, at_casablanca_hour(12, 0)) == -1
            assert calculate_points(db, at_casablanca_hour(16, 59)) == -1
        finally:
            db.close()


class TestStatusTransitionStateMachine:
    """Ch.9 lifecycle + Ch.17 locking rules."""

    def test_fully_approved_is_terminal(self):
        from app.services.status_transition_service import ensure_transition_allowed

        with pytest.raises(HTTPException) as exc_info:
            ensure_transition_allowed(InterventionStatus.FULLY_APPROVED, InterventionStatus.REJECTED)
        assert exc_info.value.status_code == 409

    def test_cannot_skip_the_approval_pipeline(self):
        from app.services.status_transition_service import ensure_transition_allowed

        with pytest.raises(HTTPException) as exc_info:
            ensure_transition_allowed(InterventionStatus.DRAFT, InterventionStatus.FULLY_APPROVED)
        assert exc_info.value.status_code == 409

    def test_legal_transitions_pass(self):
        from app.services.status_transition_service import ensure_transition_allowed

        # Submit skips the standalone "Submitted" state (Ch.9 State 4->5 is automatic).
        ensure_transition_allowed(InterventionStatus.DRAFT, InterventionStatus.PENDING_TECHNICAL_APPROVAL)
        # Technical approval skips the standalone "Technical Approved" state (State 6->7 is automatic).
        ensure_transition_allowed(
            InterventionStatus.PENDING_TECHNICAL_APPROVAL, InterventionStatus.PENDING_ADMINISTRATIVE_APPROVAL
        )
        ensure_transition_allowed(InterventionStatus.PENDING_TECHNICAL_APPROVAL, InterventionStatus.REJECTED)
        ensure_transition_allowed(InterventionStatus.PENDING_ADMINISTRATIVE_APPROVAL, InterventionStatus.FULLY_APPROVED)
        ensure_transition_allowed(InterventionStatus.PENDING_ADMINISTRATIVE_APPROVAL, InterventionStatus.REJECTED)
        ensure_transition_allowed(InterventionStatus.REJECTED, InterventionStatus.PENDING_TECHNICAL_APPROVAL)

    def test_editable_statuses_match_ch17(self):
        from app.services.status_transition_service import ensure_editable

        ensure_editable(InterventionStatus.DRAFT)
        ensure_editable(InterventionStatus.REJECTED)
        for locked_status in [
            InterventionStatus.SUBMITTED,
            InterventionStatus.PENDING_TECHNICAL_APPROVAL,
            InterventionStatus.PENDING_ADMINISTRATIVE_APPROVAL,
            InterventionStatus.FULLY_APPROVED,
        ]:
            with pytest.raises(HTTPException) as exc_info:
                ensure_editable(locked_status)
            assert exc_info.value.status_code == 409
