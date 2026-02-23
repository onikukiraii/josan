import datetime

from pydantic import BaseModel

from entity.enums import RequestType


class ShiftRequestDateEntry(BaseModel):
    date: datetime.date
    request_type: RequestType = RequestType.day_off


class ShiftRequestBulkParams(BaseModel):
    member_id: int
    year_month: str
    entries: list[ShiftRequestDateEntry]
