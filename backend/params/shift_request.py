import datetime

from pydantic import BaseModel


class ShiftRequestBulkParams(BaseModel):
    member_id: int
    year_month: str
    dates: list[datetime.date]
