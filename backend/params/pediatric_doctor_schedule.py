import datetime

from pydantic import BaseModel


class PediatricDoctorScheduleBulkParams(BaseModel):
    year_month: str
    dates: list[datetime.date]
