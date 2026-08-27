from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, model_validator


class PointRuleCreate(BaseModel):
    start_time: time
    end_time: time
    points: int

    @model_validator(mode="after")
    def _validate_interval(self) -> "PointRuleCreate":
        # A rule spanning zero duration (start == end) is ambiguous — it could
        # mean "no window" or "the full 24h", and neither is a sane default.
        # Midnight-crossing rules (e.g. 22:00-00:00) are legal: end_time == 00:00
        # while start_time != 00:00 is not caught here, since that is the
        # documented way to express "until midnight" and end < start is the
        # documented way to express "crossing into the next day".
        if self.start_time == self.end_time:
            raise ValueError("Start time and end time cannot be identical.")
        return self


class PointRuleUpdate(PointRuleCreate):
    pass


class PointRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    start_time: time
    end_time: time
    points: int
    active: bool
    created_at: datetime
    updated_at: datetime
