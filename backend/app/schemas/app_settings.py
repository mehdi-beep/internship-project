from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# Mirrors app_settings_service.MIN/MAX_OFFSET_MINUTES exactly — duplicated
# here (rather than imported) so this schema module has no dependency on the
# service layer, matching how point_rule's schemas/service are already split
# in this codebase. Pydantic's Field bounds give FastAPI's normal 422 for
# free on the request path; app_settings_service re-checks the same range
# for any caller that isn't going through this schema.
MIN_OFFSET_MINUTES = -720
MAX_OFFSET_MINUTES = 840


class AppSettingsUpdate(BaseModel):
    company_utc_offset_minutes: int = Field(ge=MIN_OFFSET_MINUTES, le=MAX_OFFSET_MINUTES)


class AppSettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    company_utc_offset_minutes: int
    updated_at: datetime
