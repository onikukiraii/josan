import datetime as dt

from pydantic import BaseModel, Field


class ShiftRequestResponse(BaseModel):
    id: int
    member_id: int = Field(title="メンバーID")
    member_name: str = Field(title="メンバー名")
    year_month: str = Field(title="年月")
    date: dt.date = Field(title="日付")
    created_at: dt.datetime

    model_config = {"from_attributes": True}
