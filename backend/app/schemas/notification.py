from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import InterventionStatus

# Maps an actionable notification's title to the single InterventionStatus
# that means "the action this notification asked for is still pending."
# Once the intervention has moved to any OTHER status, the action already
# happened (by whoever got there first) or the intervention was rejected —
# either way, this specific notification's call-to-action is resolved for
# every recipient who got a copy of it, not just whoever acted on it. Titles
# not in this map (e.g. "Intervention Rejected"/"Intervention Approved" — a
# pure FYI to the technician with nothing further to do) are never stale by
# definition; is_still_actionable is None for those, not False, since
# "resolved" implies there was an action to resolve.
_ACTIONABLE_STATUS_BY_TITLE: dict[str, InterventionStatus] = {
    "Intervention Submitted": InterventionStatus.PENDING_TECHNICAL_APPROVAL,
    "Administrative Approval Needed": InterventionStatus.PENDING_ADMINISTRATIVE_APPROVAL,
}


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    # Task 5: nullable — permanently deleting the recipient detaches (never
    # deletes) the notification; deleted_user_label carries their name
    # forward once user_id is cleared. In practice a deleted recipient can
    # never authenticate to fetch this again, so this is precautionary.
    user_id: int | None
    deleted_user_label: str | None = None
    title: str
    message: str
    related_intervention_id: int | None
    related_planning_id: int | None
    read: bool
    created_at: datetime
    # Whether the action this notification implies is still pending, based on
    # the CURRENT state of the entity it refers to — distinct from `read`,
    # which only tracks whether the recipient has seen it. Computed fresh on
    # every fetch (see from_model below), never stored, so it can never
    # itself go stale. None for notifications with no action to become stale.
    is_still_actionable: bool | None = None

    @classmethod
    def from_model(cls, notification) -> "NotificationOut":
        expected_status = _ACTIONABLE_STATUS_BY_TITLE.get(notification.title)
        is_still_actionable = (
            notification.related_intervention.status == expected_status
            if expected_status is not None and notification.related_intervention is not None
            else None
        )
        return cls(
            id=notification.id,
            user_id=notification.user_id,
            deleted_user_label=notification.deleted_user_label,
            title=notification.title,
            message=notification.message,
            related_intervention_id=notification.related_intervention_id,
            related_planning_id=notification.related_planning_id,
            read=notification.read,
            created_at=notification.created_at,
            is_still_actionable=is_still_actionable,
        )
