from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
