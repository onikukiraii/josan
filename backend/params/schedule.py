from pydantic import BaseModel

from entity.enums import ShiftType


class ShiftAssignmentUpdateParams(BaseModel):
    shift_type: ShiftType
    member_id: int


class ScheduleGenerateParams(BaseModel):
    year_month: str
