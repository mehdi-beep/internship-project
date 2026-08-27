from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    message: str
    related_intervention_id: int | None
    related_planning_id: int | None
    read: bool
    created_at: datetime
