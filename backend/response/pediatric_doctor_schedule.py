import datetime as dt

from pydantic import BaseModel, Field


class PediatricDoctorScheduleResponse(BaseModel):
    id: int
    date: dt.date = Field(title="日付")
    created_at: dt.datetime

    model_config = {"from_attributes": True}
